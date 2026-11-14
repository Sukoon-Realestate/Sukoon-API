from core_apps.features.http import ActionPolicy, FeatureAPIView
from rest_framework.permissions import IsAuthenticated
from core_apps.features.renderers import FeatureJsonRenderer

from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .company_contract_models import CompanyMandate
from .company_contract_serializers import (
    MandateBody,
    MandateDecisionBody,
    PreparationBody,
    PreparationResponseBody,
)
from .company_serializers import CommandBody
from .company_views import mutate, page
from .rental_lifecycle_views.common import validated
from .services.company.access import company_for, member_for
from .services.company import (
    mandates as m,
    contract_preparation as c,
    contract_access as a,
    contract_projection as p,
)


class MandatesView(FeatureAPIView):
    name = "Mandates"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_contract_views",
            "mandates",
            boundary="company",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "company_contract_views",
            "mandates",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, company_id):
        company = company_for(request.user, company_id)
        member = member_for(request.user, company)
        query = (
            CompanyMandate.objects.filter(company=company)
            .select_related("membership__user")
            .order_by("-created_at", "id")
        )
        if not member.is_admin and not member.is_coordinator:
            query = query.filter(membership=member)
        return page(request, query, lambda item: m.payload(item, request.user))

    def post(self, request, company_id):
        body = validated(MandateBody, request.data)
        return mutate(
            request,
            "company.mandate.propose",
            lambda: company_for(request.user, company_id, "admin", lock=True),
            lambda _: m.propose(request.user, company_id, body),
            lambda item: m.payload(item, request.user),
            creating=True,
        )


# Stable callable import for integrations; URLs use the explicit class.
mandates = MandatesView.as_view()


class MandateActionView(FeatureAPIView):
    name = "Mandate Action"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "company_contract_views",
            "mandate_action",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, mandate_id, action):
        if action not in {"approve", "reject", "revoke"}:
            raise ValidationError("Unsupported mandate action.")
        body = validated(MandateDecisionBody, request.data)
        return mutate(
            request,
            "company.mandate." + action,
            lambda: m.authorize(
                request.user, mandate_id, lock=True, admin=action != "revoke"
            ),
            lambda _: m.decide(request.user, mandate_id, action, body),
            lambda item: m.decision_payload(item, request.user, action),
        )


# Stable callable import for integrations; URLs use the explicit class.
mandate_action = MandateActionView.as_view()


class PreparationView(FeatureAPIView):
    name = "Preparation"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_contract_views",
            "preparation",
            boundary="company",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "company_contract_views",
            "preparation",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, item_id):
        return Response(p.context(c.booking_for(request.user, item_id), request.user))

    def post(self, request, item_id):
        body = validated(PreparationBody, request.data)
        return mutate(
            request,
            "company.contract.prepare",
            lambda: c.booking_for(request.user, item_id, lock=True),
            lambda _: c.prepare(request.user, item_id, body),
            lambda item: p.payload(item, request.user),
            creating=True,
            account_parties=lambda: c.account_parties(item_id, body),
        )


# Stable callable import for integrations; URLs use the explicit class.
preparation = PreparationView.as_view()


class PreparationsView(FeatureAPIView):
    name = "Preparations"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_contract_views",
            "preparations",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        from .services.rental_lifecycle.common import require_actor

        require_actor(request.user)
        identity = None
        if request.query_params.get("company_id"):
            identity = serializers.UUIDField().run_validation(
                request.query_params["company_id"]
            )
        query = a.visible(request.user, company_id=identity)
        # Employee-only rows are projected without coworkers or commercial amounts.
        return page(
            request,
            query,
            lambda item: p.payload(a.get(request.user, item.id), request.user),
        )


# Stable callable import for integrations; URLs use the explicit class.
preparations = PreparationsView.as_view()


class DetailView(FeatureAPIView):
    name = "Detail"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_contract_views",
            "detail",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, preparation_id):
        return Response(p.payload(a.get(request.user, preparation_id), request.user))


# Stable callable import for integrations; URLs use the explicit class.
detail = DetailView.as_view()


class PreparationActionView(FeatureAPIView):
    name = "Preparation Action"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "company_contract_views",
            "preparation_action",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, preparation_id, action):
        if action not in {"respond", "withdraw", "reserve"}:
            raise ValidationError("Unsupported preparation action.")
        body = validated(
            PreparationResponseBody if action == "respond" else CommandBody,
            request.data,
        )
        handler = {"respond": c.respond, "withdraw": c.withdraw, "reserve": c.reserve}[
            action
        ]
        return mutate(
            request,
            "company.contract." + action,
            lambda: a.get(request.user, preparation_id, lock=True),
            lambda _: handler(request.user, preparation_id, body),
            lambda item: p.payload(item, request.user),
            account_parties=lambda: c.existing_account_parties(preparation_id),
        )


# Stable callable import for integrations; URLs use the explicit class.
preparation_action = PreparationActionView.as_view()
