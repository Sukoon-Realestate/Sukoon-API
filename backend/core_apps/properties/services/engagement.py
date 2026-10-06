from django.db import transaction

from ..models import SavedProperty


class SavedPropertyService:
    """Business operations for a tenant's saved properties."""

    @staticmethod
    @transaction.atomic
    def save_property(user, property_obj):
        """Save a property once and report whether a new record was created."""
        return SavedProperty.objects.get_or_create(
            user=user,
            property=property_obj,
        )

    @staticmethod
    @transaction.atomic
    def remove_saved_property(saved_property):
        """Remove a previously resolved saved-property record."""
        saved_property.delete()
