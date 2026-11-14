"""Company Admin command steps; typed adapters retain the HTTP boundary."""

from django.shortcuts import get_object_or_404
from core_apps.features.company_models import Company, CompanyHousingRequest
from core_apps.features.services.company.access import company_for
from core_apps.features.services.rental_lifecycle.common import require_staff
from core_apps.properties.models import ResidentialBuilding, ResidentialComplex


def authority_review_post_authorize(*, actor, identity, kind):
    require_staff(
        actor, {"kyc_reviewer"} if kind == "company" else {"property_reviewer"}
    )
    return get_object_or_404(
        {
            "company": Company,
            "building": ResidentialBuilding,
            "complex": ResidentialComplex,
        }[kind],
        id=identity,
    )


def reassign_coordinator_post_authorize(*, actor, request_id):
    item = get_object_or_404(CompanyHousingRequest, id=request_id)
    company_for(actor, item.company.id, "admin", lock=True)
    return item
