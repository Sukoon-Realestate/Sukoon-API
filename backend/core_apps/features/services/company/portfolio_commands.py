"""Portfolio command steps; typed adapters retain the HTTP boundary."""

from django.shortcuts import get_object_or_404
from core_apps.features.services.company import (
    portfolio_changes as changes,
    portfolio_topology as topology,
)
from core_apps.features.services.rental_lifecycle.common import require_staff
from core_apps.properties.models import ResidentialMedia


def change_post_apply(item, *, actor, body, change_id):
    handler = (
        changes.apply_bulk if item.operation == "bulk_edit" else topology.apply_topology
    )
    return handler(actor, change_id, body)


def media_review_post_authorize(*, actor, media_id):
    require_staff(actor, {"property_reviewer"})
    return get_object_or_404(ResidentialMedia, id=media_id)
