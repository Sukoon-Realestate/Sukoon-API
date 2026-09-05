from datetime import date, datetime, timedelta

from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import PermissionDenied, ValidationError

from ..models import (
    OwnerAvailabilitySlot,
    PropertyRating,
    PropertyVisit,
    PropertyVisitReview,
)


class PropertyVisitService:
    BOOKED_STATUSES = (PropertyVisit.Status.PENDING, PropertyVisit.Status.CONFIRMED)

    @staticmethod
    def get_available_dates(property_obj, requested_date=None):
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
                status__in=PropertyVisitService.BOOKED_STATUSES,
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

    @staticmethod
    @transaction.atomic
    def create_visit(tenant, property_obj, validated_data):
        """
        Creates a property visit request.
        """
        # Validate that tenant is not the property owner
        if property_obj.owner == tenant:
            raise ValidationError(_("You cannot book a visit for your own property."))

        visit_date = validated_data.get("visit_date")
        visit_time = validated_data.get("visit_time")
        slot = (
            OwnerAvailabilitySlot.objects.select_for_update()
            .filter(
                owner=property_obj.owner,
                property=property_obj,
                date=visit_date,
                time=visit_time,
                is_enabled=True,
            )
            .first()
        )
        if slot is None:
            raise ValidationError(_("The selected visit slot is not available."))

        now = timezone.localtime()
        slot_datetime = datetime.combine(slot.date, slot.time, now.tzinfo)
        if slot_datetime <= now:
            raise ValidationError(_("The selected visit slot is in the past."))

        if PropertyVisit.objects.filter(
            property=property_obj,
            visit_date=visit_date,
            visit_time=visit_time,
            status__in=PropertyVisitService.BOOKED_STATUSES,
        ).exists():
            raise ValidationError(_("The selected visit slot is already booked."))

        return PropertyVisit.objects.create(
            tenant=tenant, property=property_obj, **validated_data
        )

    @staticmethod
    @transaction.atomic
    def update_visit_status(user, visit_obj, status):
        """
        Updates the status of a property visit request.
        """
        if status == PropertyVisit.Status.CANCELED:
            # Only tenant can cancel the visit
            if visit_obj.tenant != user:
                raise PermissionDenied(
                    _("You do not have permission to cancel this visit.")
                )
            if visit_obj.status in [
                PropertyVisit.Status.CANCELED,
                PropertyVisit.Status.REJECTED,
            ]:
                raise ValidationError(
                    _("This visit has already been canceled or rejected.")
                )
            visit_obj.status = status
            visit_obj.save()
            return visit_obj

        elif status in [PropertyVisit.Status.CONFIRMED, PropertyVisit.Status.REJECTED]:
            # Only owner can confirm/reject the visit
            if visit_obj.property.owner != user:
                raise PermissionDenied(
                    _(
                        "You do not have permission to confirm or reject this visit request."
                    )
                )
            if visit_obj.status != PropertyVisit.Status.PENDING:
                raise ValidationError(
                    _(
                        f"Cannot change status from {visit_obj.status} to {status}. Only pending requests can be confirmed or rejected."
                    )
                )
            visit_obj.status = status
            visit_obj.save()
            return visit_obj

        else:
            raise ValidationError(_("Invalid status transition requested."))

    @staticmethod
    @transaction.atomic
    def create_review(tenant, visit_obj, validated_data):
        """Create the tenant's one-time review after a confirmed visit took place."""
        visit_obj = (
            PropertyVisit.objects.select_for_update()
            .select_related("property")
            .get(pk=visit_obj.pk)
        )
        if visit_obj.tenant != tenant:
            raise PermissionDenied(_("You cannot review another tenant's visit."))

        if visit_obj.status != PropertyVisit.Status.CONFIRMED:
            raise ValidationError(_("Only confirmed visits can be reviewed."))

        now = timezone.localtime()
        scheduled_at = datetime.combine(
            visit_obj.visit_date, visit_obj.visit_time, now.tzinfo
        )
        if scheduled_at > now:
            raise ValidationError(
                _("The visit cannot be reviewed before it takes place.")
            )

        if PropertyVisitReview.objects.filter(visit=visit_obj).exists():
            raise ValidationError(_("This visit has already been reviewed."))

        review = PropertyVisitReview.objects.create(visit=visit_obj, **validated_data)
        # ? Keep the existing property aggregate API in sync with visit reviews.
        PropertyRating.objects.update_or_create(
            user=tenant,
            property=visit_obj.property,
            defaults={"rating": review.overall_rating},
        )
        return review

    @staticmethod
    def get_owner_availability(property_obj, start_date):
        """Return one property's seven-day availability grid and booked slots."""
        end_date = start_date + timedelta(days=6)
        slots = OwnerAvailabilitySlot.objects.filter(
            property=property_obj,
            date__range=(start_date, end_date),
        ).order_by("date", "time")
        visits = PropertyVisit.objects.filter(
            property=property_obj,
            visit_date__range=(start_date, end_date),
            status__in=PropertyVisitService.BOOKED_STATUSES,
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
                PropertyVisitService._owner_slot_payload(slot, booked_visits.get(key))
            )

        # ? A legacy booking can exist without a slot record; keep it visible and protected.
        for key, visit in booked_visits.items():
            if key not in known_slot_keys:
                slots_by_date.setdefault(visit.visit_date, []).append(
                    PropertyVisitService._booked_slot_payload(visit)
                )

        available_slots_by_date = {
            day: sorted(
                (slot for slot in day_slots if slot["state"] == "available"),
                key=lambda item: item["time"],
            )
            for day, day_slots in slots_by_date.items()
        }
        days_with_available_slots = [
            day
            for day in (start_date + timedelta(days=offset) for offset in range(7))
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

    @staticmethod
    @transaction.atomic
    def replace_property_day_availability(property_obj, availability_date, slots_data):
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
                status__in=PropertyVisitService.BOOKED_STATUSES,
            )
            .values_list("visit_time", flat=True)
        )

        for key in booked_keys:
            if key in requested_slots and not requested_slots[key]:
                raise ValidationError(_("Booked visit slots cannot be disabled."))

        existing_by_time = {slot.time: slot for slot in existing_slots}
        for slot_time, slot in existing_by_time.items():
            requested_enabled = requested_slots.pop(slot_time, None)
            if requested_enabled is None:
                if slot_time in booked_keys:
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
        return PropertyVisitService.get_owner_availability(
            property_obj, availability_date
        )

    @staticmethod
    @transaction.atomic
    def accept_visit(user, visit_obj):
        """Owner accepts a pending visit request."""
        return PropertyVisitService.update_visit_status(
            user=user,
            visit_obj=visit_obj,
            status=PropertyVisit.Status.CONFIRMED,
        )

    @staticmethod
    @transaction.atomic
    def reject_visit(user, visit_obj, reason=None, custom_reason=None):
        """Owner rejects a pending visit request with an optional reason."""
        return PropertyVisitService.update_visit_status(
            user=user,
            visit_obj=visit_obj,
            status=PropertyVisit.Status.REJECTED,
        )

    @staticmethod
    def get_owner_visit_calendar(owner, year, month, selected_date=None):
        """Build monthly visit indicators and the selected-day appointment cards."""
        arabic_months = {
            1: "يناير",
            2: "فبراير",
            3: "مارس",
            4: "أبريل",
            5: "مايو",
            6: "يونيو",
            7: "يوليو",
            8: "أغسطس",
            9: "سبتمبر",
            10: "أكتوبر",
            11: "نوفمبر",
            12: "ديسمبر",
        }
        month_start = date(year, month, 1)
        next_month = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
        visits = list(
            PropertyVisit.objects.filter(
                property__owner=owner,
                visit_date__gte=month_start,
                visit_date__lt=next_month,
                status__in=PropertyVisitService.BOOKED_STATUSES,
            )
            .select_related("tenant", "tenant__profile", "property")
            .order_by("visit_date", "visit_time")
        )
        counts = {}
        for visit in visits:
            counts[visit.visit_date] = counts.get(visit.visit_date, 0) + 1

        selected_visits = (
            [visit for visit in visits if visit.visit_date == selected_date]
            if selected_date
            else []
        )

        def _fmt_time(t):
            h = t.hour
            m = t.minute
            period = "ص" if h < 12 else "م"
            h12 = h % 12 or 12
            return f"{h12}:{m:02d} {period}"

        visits_payload = []
        for visit in selected_visits:
            tenant_name = visit.tenant.get_full_name
            first_letter = tenant_name.strip()[0] if tenant_name and tenant_name.strip() else ""
            profile = getattr(visit.tenant, "profile", None)
            avatar_url = (
                profile.avatar.url
                if profile and getattr(profile, "avatar", None)
                else None
            )
            status_label = (
                "مؤكدة"
                if visit.status == PropertyVisit.Status.CONFIRMED
                else "معلقة"
            )
            visits_payload.append(
                {
                    "id": str(visit.id),
                    "tenant": {
                        "id": str(visit.tenant.id),
                        "name": tenant_name,
                        "initial": first_letter,
                        "avatar": avatar_url,
                    },
                    "property": {
                        "id": str(visit.property.id),
                        "title": visit.property.title,
                    },
                    "visit_time": visit.visit_time.strftime("%H:%M:%S"),
                    "time_formatted": _fmt_time(visit.visit_time),
                    "status": visit.status,
                    "status_label": status_label,
                }
            )

        month_label = f"{arabic_months.get(month, '')} {year}".strip()
        selected_date_label = (
            f"زيارات يوم {selected_date.day}" if selected_date else None
        )

        return {
            "year": year,
            "month": month,
            "month_label": month_label,
            "days": [
                {
                    "date": visit_date.isoformat(),
                    "day": visit_date.day,
                    "visit_count": count,
                }
                for visit_date, count in counts.items()
            ],
            "selected_date": selected_date.isoformat() if selected_date else None,
            "selected_date_label": selected_date_label,
            "visits": visits_payload,
        }

    @staticmethod
    def _owner_slot_payload(slot, visit):
        if visit:
            return PropertyVisitService._booked_slot_payload(visit, slot_id=slot.id)
        return {
            "id": str(slot.id),
            "time": slot.time.strftime("%H:%M:%S"),
            "is_enabled": slot.is_enabled,
            "state": "available" if slot.is_enabled else "disabled",
            "visit": None,
        }

    @staticmethod
    def _booked_slot_payload(visit, slot_id=None):
        return {
            "id": str(slot_id) if slot_id else None,
            "time": visit.visit_time.strftime("%H:%M:%S"),
            "is_enabled": True,
            "state": "booked",
            "visit": {
                "id": str(visit.id),
                "tenant_name": visit.tenant.get_full_name,
                "property_id": str(visit.property.id),
                "property_title": visit.property.title,
                "status": visit.status,
            },
        }
