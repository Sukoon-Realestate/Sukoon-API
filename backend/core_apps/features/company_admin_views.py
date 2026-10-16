"""Company administration and scoped authority review endpoints."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from .company_views import company_api, mutate, page
from .company_serializers import AuthorityReviewBody, CompanyBudgetBody, CoordinatorBody
from .company_models import Company, CompanyHousingRequest
from .rental_lifecycle_views.common import validated
from .services.company import administration, portfolio, bookings
from .services.company.access import company_for
from .services.company.projections import company_payload
from .services.rental_lifecycle.common import require_staff
from core_apps.properties.models import ResidentialBuilding, ResidentialComplex


@company_api(["POST"])
def authority_review(request, kind, identity):
    if kind not in {"company", "building", "complex"}:
        raise ValidationError("Unsupported authority scope.")
    data = validated(AuthorityReviewBody, request.data)

    def authorize():
        require_staff(
            request.user,
            {"kyc_reviewer"} if kind == "company" else {"property_reviewer"},
        )
        return get_object_or_404(
            {
                "company": Company,
                "building": ResidentialBuilding,
                "complex": ResidentialComplex,
            }[kind],
            id=identity,
        )

    return mutate(
        request,
        "company.authority.review." + kind,
        authorize,
        lambda _: administration.review(request.user, kind, identity, data),
        lambda item: {
            "id": str(item.id),
            "revision": item.revision,
            "status": data["status"],
        },
    )


@company_api(["POST"])
def company_budget(request, company_id):
    data = validated(CompanyBudgetBody, request.data)
    return mutate(
        request,
        "company.budget.update",
        lambda: company_for(request.user, company_id, "admin", lock=True),
        lambda _: administration.set_budget(request.user, company_id, data),
        lambda c: company_payload(c, request.user),
    )


@company_api(["POST"])
def reassign_coordinator(request, request_id):
    data = validated(CoordinatorBody, request.data)

    def authorize():
        item = get_object_or_404(CompanyHousingRequest, id=request_id)
        company_for(request.user, item.company.id, "admin", lock=True)
        return item

    return mutate(
        request,
        "company.coordinator.reassign",
        authorize,
        lambda _: administration.reassign_coordinator(request.user, request_id, data),
        bookings.request_payload,
    )


@company_api(["GET"])
def occupants(request, company_id):
    company = company_for(request.user, company_id, "coordinate")
    return page(
        request,
        company.memberships.filter(is_active=True, is_employee=True)
        .select_related("user")
        .order_by("id"),
        lambda m: {
            "id": str(m.id),
            "user_id": str(m.user.id),
            "name": m.user.get_full_name,
            "revision": m.revision,
            "is_active": True,
        },
    )
