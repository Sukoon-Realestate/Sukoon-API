from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from .company_models import CompanyBookingItem
from .company_views import company_api, mutate, page
from .company_staff_serializers import ApprovalRouteBody, ApprovalReassignmentBody
from .rental_lifecycle_views.common import validated
from .services.company.access import company_for
from .services.company.projections import company_payload
from .services.company import approval_routing as routing


@company_api(["POST"])
def approval_route(request, company_id):
    data = validated(ApprovalRouteBody, request.data)
    return mutate(
        request,
        "company.approval_route.configure",
        lambda: company_for(request.user, company_id, "admin", lock=True),
        lambda _: routing.configure(request.user, company_id, data),
        lambda c: company_payload(c, request.user),
    )


@company_api(["POST"])
def reassign(request, item_id):
    data = validated(ApprovalReassignmentBody, request.data)

    def authorize():
        item = get_object_or_404(CompanyBookingItem, id=item_id)
        company_for(request.user, item.request.company.id, "admin", lock=True)
        return item

    return mutate(
        request,
        "company.approval.reassign",
        authorize,
        lambda _: routing.reassign(request.user, item_id, data),
        lambda item: routing.work_payload(item, request.user),
    )


@company_api(["GET"])
def work(request, company_id):
    company = company_for(request.user, company_id)
    return page(
        request,
        routing.work_items(request.user, company),
        lambda item: routing.work_payload(item, request.user),
    )
