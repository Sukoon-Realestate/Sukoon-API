"""Company Work command steps; typed adapters retain the HTTP boundary."""

from django.shortcuts import get_object_or_404
from core_apps.features.company_models import CompanyBookingItem
from core_apps.features.services.company.access import company_for


def reassign_post_authorize(*, actor, item_id):
    item = get_object_or_404(CompanyBookingItem, id=item_id)
    company_for(actor, item.request.company.id, "admin", lock=True)
    return item
