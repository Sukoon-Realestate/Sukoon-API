from core_apps.features.http import ActionPolicy, FeatureAPIView
from rest_framework.permissions import IsAuthenticated
from core_apps.features.renderers import FeatureJsonRenderer

from rest_framework import serializers
from rest_framework.exceptions import ValidationError, APIException
from django.utils import timezone
from .company_views import page, mutate
from .rental_lifecycle_views.common import validated
from .company_negotiation_serializers import StartTerms, DecideTerms, ReviseTerms
from .services.company import (
    negotiation,
    negotiation_access as access,
    negotiation_projection as projection,
    negotiation_binding as binding,
)
from .services.company.access import booking_account_parties


class NegotiationsView(FeatureAPIView):
    name = "Negotiations"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_negotiation_views",
            "negotiations",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        scope = request.query_params.get("workspace")
        company_id = request.query_params.get("company_id")
        qs = projection.visible(request.user)
        if scope == "owner":
            qs = qs.filter(owner=request.user)
        elif scope == "company":
            qs = qs.exclude(owner=request.user)
            if company_id:
                company_id = serializers.UUIDField().run_validation(company_id)
                qs = qs.filter(booking__request__company__id=company_id)
        else:
            raise ValidationError("Choose owner or company workspace.")
        property_id = request.query_params.get("property_id")
        active = serializers.BooleanField().run_validation(
            request.query_params.get("active_agreements", False)
        )
        if property_id or active:
            if scope != "company" or not company_id or not property_id:
                raise ValidationError("Choose the company and exact property.")
            property_id = serializers.UUIDField().run_validation(property_id)
            # A portfolio offer has its own identity. Never match a public room/bed
            # offer ID or attribute the whole package price to one of its units.
            qs = qs.filter(
                source_snapshot__inventory__units__contains=[{"id": str(property_id)}]
            )
        if active:
            qs = qs.filter(
                status="accepted",
                expires_at__gt=timezone.now(),
                followed_at__isnull=True,
                booking__hold__isnull=True,
                booking__invitation__isnull=True,
                booking__lease__isnull=True,
            )
        # Historical lists remain available to current parties. The listing card
        # only presents agreements whose physical inventory and parties still match.
        ids = []
        for item in qs:
            if not access.role(item, request.user):
                continue
            if active:
                try:
                    binding.current(item)
                except APIException:
                    continue
            ids.append(item.pk)
        response = page(
            request,
            qs.filter(pk__in=ids).order_by("-updated_at"),
            lambda item: projection.payload(item, request.user),
        )
        response["Cache-Control"] = "private, no-store"
        return response


# Stable callable import for integrations; URLs use the explicit class.
negotiations = NegotiationsView.as_view()


class StartView(FeatureAPIView):
    name = "Start"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "company_negotiation_views",
            "start",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, item_id):
        data = validated(StartTerms, request.data)
        return mutate(
            request,
            f"company.terms.start.{item_id}",
            lambda: access.start_booking(request.user, item_id),
            lambda item: negotiation.start(item, request.user, data),
            lambda item: projection.payload(item, request.user),
            creating=True,
            account_parties=lambda: booking_account_parties(item_id),
        )


# Stable callable import for integrations; URLs use the explicit class.
start = StartView.as_view()


class DetailView(FeatureAPIView):
    name = "Detail"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_negotiation_views",
            "detail",
            boundary="company",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "company_negotiation_views",
            "detail",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, negotiation_id, action=None):
        from rest_framework.response import Response

        return Response(
            projection.payload(access.get(request.user, negotiation_id), request.user),
            headers={"Cache-Control": "private, no-store"},
        )

    def post(self, request, negotiation_id, action=None):
        if action not in {
            "edit",
            "counter",
            "accept",
            "reject",
            "request-changes",
            "withdraw",
        }:
            raise ValidationError("Choose a supported negotiation action.")
        data = validated(
            ReviseTerms if action in {"edit", "counter"} else DecideTerms, request.data
        )
        return mutate(
            request,
            f"company.terms.{action}.{negotiation_id}",
            lambda: access.get(request.user, negotiation_id, lock=True),
            lambda item: negotiation.act(item, request.user, action, data),
            lambda item: projection.payload(item, request.user),
            account_parties=lambda: access.parties(negotiation_id),
        )


# Stable callable import for integrations; URLs use the explicit class.
detail = DetailView.as_view()
