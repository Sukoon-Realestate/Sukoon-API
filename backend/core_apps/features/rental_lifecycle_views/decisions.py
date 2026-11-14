from functools import partial
from ..services.rental_lifecycle import decisions_commands as commands

from core_apps.features.http import ActionPolicy, FeatureAPIView
from rest_framework.permissions import IsAuthenticated
from core_apps.features.renderers import FeatureJsonRenderer

from rest_framework.response import Response
from ..rental_lifecycle_serializers import SelectionBody, ConfirmationBody, FactBody
from ..services.rental_lifecycle.access import property_for
from ..services.rental_lifecycle.decisions import decision_summary
from .common import validated, mutate


class PropertyDecisionView(FeatureAPIView):
    name = "Property Decision"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "decisions",
            "property_decision",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, property_id):
        data = validated(SelectionBody, request.query_params.dict())
        response = Response(
            decision_summary(
                property_for(request.user, property_id), data, request.user
            )
        )
        response["Cache-Control"] = "private, no-store"
        return response


# Stable callable import for integrations; URLs use the explicit class.
property_decision = PropertyDecisionView.as_view()


class AvailabilityConfirmationView(FeatureAPIView):
    name = "Availability Confirmation"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "decisions",
            "availability_confirmation",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, property_id):
        data = validated(ConfirmationBody, request.data)

        execute = partial(
            commands.availability_confirmation_post_execute,
            actor=request.user,
            data=data,
        )

        return mutate(
            request,
            f"availability.confirm.{property_id}",
            lambda: property_for(request.user, property_id, owner=True, lock=True),
            execute,
        )


# Stable callable import for integrations; URLs use the explicit class.
availability_confirmation = AvailabilityConfirmationView.as_view()


class PropertyFactView(FeatureAPIView):
    name = "Property Fact"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "decisions",
            "property_fact",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, property_id):
        data = validated(FactBody, request.data)

        execute = partial(
            commands.property_fact_post_execute, actor=request.user, data=data
        )

        return mutate(
            request,
            f"property_fact.save.{property_id}",
            lambda: property_for(request.user, property_id, owner=True, lock=True),
            execute,
        )


# Stable callable import for integrations; URLs use the explicit class.
property_fact = PropertyFactView.as_view()
