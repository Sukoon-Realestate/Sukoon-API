from functools import partial
from .services.company import administration_commands as entry_commands

"""Company administration and scoped authority review endpoints."""

from core_apps.features.http import ActionPolicy, FeatureAPIView
from rest_framework.permissions import IsAuthenticated
from core_apps.features.renderers import FeatureJsonRenderer


from rest_framework.exceptions import ValidationError
from .company_views import mutate, page
from .company_serializers import AuthorityReviewBody, CompanyBudgetBody, CoordinatorBody
from .rental_lifecycle_views.common import validated
from .services.company import administration
from .services.company.access import company_for
from .services.company.projections import company_payload


class AuthorityReviewView(FeatureAPIView):
    name = "Authority Review"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "company_admin_views",
            "authority_review",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, kind, identity):
        if kind not in {"company", "building", "complex"}:
            raise ValidationError("Unsupported authority scope.")
        data = validated(AuthorityReviewBody, request.data)

        authorize = partial(
            entry_commands.authority_review_post_authorize,
            actor=request.user,
            identity=identity,
            kind=kind,
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


# Stable callable import for integrations; URLs use the explicit class.
authority_review = AuthorityReviewView.as_view()


class CompanyBudgetView(FeatureAPIView):
    name = "Company Budget"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "company_admin_views",
            "company_budget",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, company_id):
        data = validated(CompanyBudgetBody, request.data)
        return mutate(
            request,
            "company.budget.update",
            lambda: company_for(request.user, company_id, "admin", lock=True),
            lambda _: administration.set_budget(request.user, company_id, data),
            lambda c: company_payload(c, request.user),
        )


# Stable callable import for integrations; URLs use the explicit class.
company_budget = CompanyBudgetView.as_view()


class ReassignCoordinatorView(FeatureAPIView):
    name = "Reassign Coordinator"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "company_admin_views",
            "reassign_coordinator",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, request_id):
        data = validated(CoordinatorBody, request.data)

        authorize = partial(
            entry_commands.reassign_coordinator_post_authorize,
            actor=request.user,
            request_id=request_id,
        )

        return mutate(
            request,
            "company.coordinator.reassign",
            authorize,
            lambda _: administration.reassign_coordinator(
                request.user, request_id, data
            ),
            lambda item: {"id": str(item.id), "revision": item.revision},
        )


# Stable callable import for integrations; URLs use the explicit class.
reassign_coordinator = ReassignCoordinatorView.as_view()


class OccupantsView(FeatureAPIView):
    name = "Occupants"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_admin_views",
            "occupants",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, company_id):
        from core_apps.users.services.new_business import restricted_accounts

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
                "account_closure_blocked": bool(restricted_accounts(m.user_id)),
            },
        )


# Stable callable import for integrations; URLs use the explicit class.
occupants = OccupantsView.as_view()
