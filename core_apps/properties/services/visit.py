from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import PermissionDenied, ValidationError

from ..models import PropertyVisit


class PropertyVisitService:
    @staticmethod
    @transaction.atomic
    def create_visit(tenant, property_obj, validated_data):
        """
        Creates a property visit request.
        """
        # Validate that tenant is not the property owner
        if property_obj.owner == tenant:
            raise ValidationError(
                _("You cannot book a visit for your own property.")
            )

        # Check for double booking by the same tenant for the same slot
        visit_date = validated_data.get("visit_date")
        visit_time = validated_data.get("visit_time")
        if PropertyVisit.objects.filter(
            tenant=tenant,
            property=property_obj,
            visit_date=visit_date,
            visit_time=visit_time,
        ).exists():
            raise ValidationError(
                _(
                    "You have already requested a visit for this property at this date and time."
                )
            )

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
