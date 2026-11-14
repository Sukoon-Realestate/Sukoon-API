from functools import partial
from .services.company import work_commands as entry_commands

from core_apps.features.http import ActionPolicy, FeatureAPIView
from rest_framework.permissions import IsAuthenticated
from core_apps.features.renderers import FeatureJsonRenderer

from .company_views import mutate, page
from .company_staff_serializers import ApprovalRouteBody, ApprovalReassignmentBody
from .rental_lifecycle_views.common import validated
from .services.company.access import company_for
from .services.company.projections import company_payload
from .services.company import approval_routing as routing


class ApprovalRouteView(FeatureAPIView):
    name = "Approval Route"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "company_work_views",
            "approval_route",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, company_id):
        data = validated(ApprovalRouteBody, request.data)
        return mutate(
            request,
            "company.approval_route.configure",
            lambda: company_for(request.user, company_id, "admin", lock=True),
            lambda _: routing.configure(request.user, company_id, data),
            lambda c: company_payload(c, request.user),
        )


# Stable callable import for integrations; URLs use the explicit class.
approval_route = ApprovalRouteView.as_view()


class ReassignView(FeatureAPIView):
    name = "Reassign"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "company_work_views",
            "reassign",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, item_id):
        data = validated(ApprovalReassignmentBody, request.data)

        authorize = partial(
            entry_commands.reassign_post_authorize, actor=request.user, item_id=item_id
        )

        return mutate(
            request,
            "company.approval.reassign",
            authorize,
            lambda _: routing.reassign(request.user, item_id, data),
            lambda item: routing.work_payload(item, request.user),
        )


# Stable callable import for integrations; URLs use the explicit class.
reassign = ReassignView.as_view()


class WorkView(FeatureAPIView):
    name = "Work"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_work_views",
            "work",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, company_id):
        company = company_for(request.user, company_id)
        return page(
            request,
            routing.work_items(request.user, company),
            lambda item: routing.work_payload(item, request.user),
        )


# Stable callable import for integrations; URLs use the explicit class.
work = WorkView.as_view()
