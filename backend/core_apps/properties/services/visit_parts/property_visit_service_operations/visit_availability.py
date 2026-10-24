"""VisitAvailability operations owned by PropertyVisitService."""

from datetime import datetime, timedelta
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from ....models import OwnerAvailabilitySlot, PropertyVisit


class VisitAvailabilityMixin:
    @classmethod
    def get_available_dates(cls, property_obj, requested_date=None):
        """Build an owner's future schedule and availability for one date."""
        now = timezone.localtime()
        today = now.date()
        current_time = now.time().replace(tzinfo=None)

        future_enabled_slots = OwnerAvailabilitySlot.objects.filter(
            property=property_obj,
            is_enabled=True,
        ).filter(models.Q(date__gt=today) | models.Q(date=today, time__gt=current_time))
        available_days = list(
            future_enabled_slots.order_by("date")
            .values_list("date", flat=True)
            .distinct()
        )

        if not available_days:
            if requested_date is not None:
                raise ValidationError(_("The selected date is not available."))
            return {"days": []}

        if requested_date is not None and requested_date not in available_days:
            raise ValidationError(_("The selected date is not available."))

        if requested_date is None:
            return {
                "days": [
                    {
                        "day": day.strftime("%A").lower(),
                        "date": f"{day.day}/{day.month}",
                        "visit_date": day.isoformat(),
                    }
                    for day in available_days
                ]
            }

        slots = list(
            OwnerAvailabilitySlot.objects.filter(
                property=property_obj, date=requested_date
            ).order_by("time")
        )
        booked_times = set(
            PropertyVisit.objects.filter(
                property=property_obj,
                visit_date=requested_date,
                status__in=cls.BOOKED_STATUSES,
            ).values_list("visit_time", flat=True)
        )

        return {
            "times": [
                {
                    "time": slot.time.strftime("%I:%M %p").lstrip("0"),
                    "visit_time": slot.time.strftime("%H:%M:%S"),
                    "is_available": (
                        slot.is_enabled
                        and slot.time not in booked_times
                        and datetime.combine(slot.date, slot.time, now.tzinfo) > now
                    ),
                }
                for slot in slots
            ],
        }

    @classmethod
    def get_owner_availability(cls, property_obj, start_date, day_count=7):
        """Return one property's seven-day availability grid and booked slots."""
        end_date = start_date + timedelta(days=day_count - 1)
        slots = OwnerAvailabilitySlot.objects.filter(
            property=property_obj,
            date__range=(start_date, end_date),
        ).order_by("date", "time")
        visits = PropertyVisit.objects.filter(
            property=property_obj,
            visit_date__range=(start_date, end_date),
            status__in=cls.BOOKED_STATUSES,
        ).select_related("tenant", "property")

        booked_visits = {
            (visit.visit_date, visit.visit_time): visit for visit in visits
        }
        slots_by_date = {}
        known_slot_keys = set()
        for slot in slots:
            key = (slot.date, slot.time)
            known_slot_keys.add(key)
            slots_by_date.setdefault(slot.date, []).append(
                cls._owner_slot_payload(slot, booked_visits.get(key))
            )

        # ? A legacy booking can exist without a slot record; keep it visible and protected.
        for key, visit in booked_visits.items():
            if key not in known_slot_keys:
                slots_by_date.setdefault(visit.visit_date, []).append(
                    cls._booked_slot_payload(visit)
                )

        available_slots_by_date = {
            day: sorted(
                day_slots,
                key=lambda item: item["time"],
            )
            for day, day_slots in slots_by_date.items()
        }
        days_with_available_slots = [
            day
            for day in (start_date + timedelta(days=offset) for offset in range(day_count))
            if available_slots_by_date.get(day)
        ]

        return {
            "week_start": start_date.isoformat(),
            "week_end": end_date.isoformat(),
            "days": [
                {
                    "date": day.isoformat(),
                    "day": day.strftime("%A").lower(),
                    "slots": available_slots_by_date[day],
                }
                for day in days_with_available_slots
            ],
        }

    @classmethod
    @transaction.atomic
    def replace_property_day_availability(
        cls, property_obj, availability_date, slots_data
    ):
        """Replace one property's editable daily slots without changing bookings."""
        requested_slots = {entry["time"]: entry["is_enabled"] for entry in slots_data}
        existing_slots = list(
            OwnerAvailabilitySlot.objects.select_for_update().filter(
                property=property_obj,
                date=availability_date,
            )
        )
        booked_keys = set(
            PropertyVisit.objects.select_for_update()
            .filter(
                property=property_obj,
                visit_date=availability_date,
                status__in=cls.BOOKED_STATUSES,
            )
            .values_list("visit_time", flat=True)
        )

        for key in booked_keys:
            if key in requested_slots and not requested_slots[key]:
                raise ValidationError(_("Booked visit slots cannot be disabled."))

        existing_by_time = {slot.time: slot for slot in existing_slots}
        now = timezone.localtime()
        for slot_time, enabled in requested_slots.items():
            if datetime.combine(availability_date, slot_time, now.tzinfo) <= now:
                previous = existing_by_time.get(slot_time)
                unchanged = previous is not None and previous.is_enabled == enabled
                if not unchanged and not (slot_time in booked_keys and enabled):
                    raise ValidationError(_("Availability slots must be in the future."))
        for slot_time, slot in existing_by_time.items():
            requested_enabled = requested_slots.pop(slot_time, None)
            if requested_enabled is None:
                if slot_time in booked_keys or datetime.combine(availability_date, slot_time, now.tzinfo) <= now:
                    continue
                slot.delete()
            elif slot.is_enabled != requested_enabled:
                slot.is_enabled = requested_enabled
                slot.save(update_fields=["is_enabled", "updated_at"])

        new_slots = [
            OwnerAvailabilitySlot(
                owner=property_obj.owner,
                property=property_obj,
                date=availability_date,
                time=slot_time,
                is_enabled=is_enabled,
            )
            for slot_time, is_enabled in requested_slots.items()
        ]
        OwnerAvailabilitySlot.objects.bulk_create(new_slots)
        return cls.get_owner_availability(property_obj, availability_date)
