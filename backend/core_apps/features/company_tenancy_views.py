from .services.company import tenancy_commands as commands

from core_apps.features.http import ActionPolicy, FeatureAPIView
from rest_framework.permissions import IsAuthenticated
from core_apps.features.renderers import FeatureJsonRenderer

from rest_framework.response import Response
from .company_views import page
from .company_serializers import CommandBody
from .company_tenancy_serializers import ExecutionAuthorityBody, command_body
from .rental_lifecycle_views.common import validated
from .services.company import tenancy_access as access, tenancy_projection as projection


class CreateView(FeatureAPIView):
    name = "Create"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "company_tenancy_views",
            "create",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, preparation_id):
        body = validated(CommandBody, request.data)
        payload, status = commands.create_agreement(
            request.user, preparation_id, body, request.data
        )
        return Response(payload, status=status)


# Stable callable import for integrations; URLs use the explicit class.
create = CreateView.as_view()


class CollectionView(FeatureAPIView):
    name = "Collection"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_tenancy_views",
            "collection",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        from rest_framework import serializers

        from .services.rental_lifecycle.common import require_actor

        require_actor(request.user)
        scope = {}
        if request.query_params.get("company_id"):
            identity = serializers.UUIDField().run_validation(
                request.query_params["company_id"]
            )
            scope["company_id"] = identity
        if "lease_id" in request.query_params:
            lease_id = serializers.UUIDField().run_validation(
                request.query_params["lease_id"]
            )
            scope["lease_id"] = lease_id
        query = access.visible(request.user, **scope)
        return page(request, query, lambda item: projection.payload(item, request.user))


# Stable callable import for integrations; URLs use the explicit class.
collection = CollectionView.as_view()


class DetailView(FeatureAPIView):
    name = "Detail"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_tenancy_views",
            "detail",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, tenancy_id):
        return Response(
            projection.payload(access.get(request.user, tenancy_id), request.user)
        )


# Stable callable import for integrations; URLs use the explicit class.
detail = DetailView.as_view()


class ResolveOperationView(FeatureAPIView):
    name = "Resolve Operation"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "company_tenancy_views",
            "resolve_operation",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, tenancy_id):
        from .services.company.tenancy_operation_recovery import RecoveryBody, resolve
        from .services.rental_foundation import private_no_store

        body = validated(RecoveryBody, request.data)
        return private_no_store(Response(resolve(request.user, tenancy_id, body)))


# Stable callable import for integrations; URLs use the explicit class.
resolve_operation = ResolveOperationView.as_view()


class ActionView(FeatureAPIView):
    name = "Action"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "company_tenancy_views",
            "action",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, tenancy_id, action):
        body = command_body(action, request.data)
        payload, status = commands.apply_action(
            request.user, tenancy_id, action, body, request.data
        )
        return Response(payload, status=status)


# Stable callable import for integrations; URLs use the explicit class.
action = ActionView.as_view()


class VerifyMandateView(FeatureAPIView):
    name = "Verify Mandate"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "company_tenancy_views",
            "verify_mandate",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, mandate_id):
        body = validated(ExecutionAuthorityBody, request.data)
        payload, status = commands.verify_execution_mandate(
            request.user, mandate_id, body, request.data
        )
        return Response(payload, status=status)


# Stable callable import for integrations; URLs use the explicit class.
verify_mandate = VerifyMandateView.as_view()

# Supported service helpers retain their import identities.
from .services.company.tenancy_commands import (
    HANDLERS as HANDLERS,
    open_case as open_case,
    receipt_resource as receipt_resource,
    authorize_action as authorize_action,
)

__all__ = ["HANDLERS", "authorize_action", "open_case", "receipt_resource"]
