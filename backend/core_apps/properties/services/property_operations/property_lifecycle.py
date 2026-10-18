"""PropertyLifecycle operations owned by PropertyService."""

from django.db import transaction
from ...models import Property, PropertyVisit


class PropertyLifecycleMixin:
    @classmethod
    @transaction.atomic
    def delete_property(cls, property_obj, user):
        """
        Deletes a property if the user is the owner and no active visit requests or leases exist.
        """
        from rest_framework.exceptions import APIException, PermissionDenied
        from rest_framework import status

        if property_obj.owner != user:
            raise PermissionDenied("You are not the owner of this property listing.")

        property_obj = Property.objects.select_for_update().get(pk=property_obj.pk)
        if (
            property_obj.building_id
            or property_obj.retired_at
            or property_obj.complex_id
            or property_obj.portfolio_offers.exists()
        ):
            from core_apps.features.services.rental_phase2 import RentalConflict

            raise RentalConflict(
                "Portfolio inventory identities must be retained. Hide the listing instead.",
                code="inventory_history_protected",
            )

        # Check for active or confirmed visit requests
        active_visits = property_obj.visits.filter(
            status__in=[PropertyVisit.Status.PENDING, PropertyVisit.Status.CONFIRMED]
        )
        if active_visits.exists():
            conflict_exc = APIException(
                "Cannot delete property with active or upcoming visit requests."
            )
            conflict_exc.status_code = status.HTTP_409_CONFLICT
            raise conflict_exc

        property_id = str(property_obj.id)
        property_obj.delete()
        return property_id

    @classmethod
    @transaction.atomic
    def toggle_property_visibility(cls, property_obj, is_hidden=None):
        """
        Toggles or sets the property's visibility between HIDDEN and active/verified.
        """
        property_obj = Property.objects.select_for_update().get(pk=property_obj.pk)
        if property_obj.retired_at:
            from core_apps.features.services.rental_phase2 import RentalConflict

            raise RentalConflict(
                "This inventory identity has been retired.", code="inventory_retired"
            )
        if is_hidden is None:
            new_hidden = property_obj.status != Property.Status.HIDDEN
        else:
            new_hidden = bool(is_hidden)

        # Historical owner edits left a stale approval flag on pending content.
        # Hiding and showing that content must never act as reviewer approval.
        if property_obj.status in {
            Property.Status.UNDER_REVIEW,
            Property.Status.NEEDS_REVISION,
        }:
            property_obj.is_verified = False

        if new_hidden:
            property_obj.status = Property.Status.HIDDEN
        else:
            if property_obj.is_verified:
                property_obj.status = Property.Status.VERIFIED
            else:
                property_obj.status = Property.Status.UNDER_REVIEW

        property_obj.save(update_fields=["status", "is_verified", "updated_at"])
        return property_obj
