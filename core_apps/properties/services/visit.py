from datetime import datetime

from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import PermissionDenied, ValidationError

from ..models import OwnerAvailabilitySlot, PropertyVisit


class PropertyVisitService:
    BOOKED_STATUSES = (PropertyVisit.Status.PENDING, PropertyVisit.Status.CONFIRMED)

    @staticmethod
    def get_available_dates(property_obj, requested_date=None):
        """Build an owner's future schedule and availability for one date."""
        now = timezone.localtime()
        today = now.date()
        current_time = now.time().replace(tzinfo=None)

        future_enabled_slots = OwnerAvailabilitySlot.objects.filter(
            owner=property_obj.owner,
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
            return {"days": [], "times": []}

        if requested_date is not None and requested_date not in available_days:
            raise ValidationError(_("The selected date is not available."))

        selected_date = requested_date or available_days[0]
        slots = list(
            OwnerAvailabilitySlot.objects.filter(
                owner=property_obj.owner, date=selected_date
            ).order_by("time")
        )
        booked_times = set(
            PropertyVisit.objects.filter(
                property__owner=property_obj.owner,
                visit_date=selected_date,
                status__in=PropertyVisitService.BOOKED_STATUSES,
            ).values_list("visit_time", flat=True)
        )

        return {
            "days": [
                {
                    "day": day.strftime("%A").lower(),
                    "date": f"{day.day}/{day.month}",
                    "visit_date": day.isoformat(),
                }
                for day in available_days
            ],
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
            property__owner=property_obj.owner,
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
