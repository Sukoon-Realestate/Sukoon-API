"""Explicit method policy for housing transport adapters.

Resource/action identities are stable independently of Python callable names.
Command services still enforce current membership, mandates and locked authority;
this layer preserves the additional historical HTTP wrapper contract only.
"""

from dataclasses import dataclass

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView


@dataclass(frozen=True)
class ActionPolicy:
    resource: str
    action: str
    boundary: str = "standard"
    capability: str | None = None
    typed: bool = False


class FeatureAPIView(APIView):
    action_policies = {}

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.action_policy = self.action_policies.get(request.method.lower())
        self.policy_entered = False
        self.policy_error = False
        if self.action_policy is None:
            return
        policy = self.action_policy
        if policy.boundary == "company":
            from .services.company.role_routes import authorize_policy

            authorize_policy(request, policy.resource, policy.action)
        elif policy.boundary == "planning":
            from .services.planning import require_planning, validate_payload_types

            require_planning(request.user, policy.capability)
            if request.method == "POST":
                if not isinstance(request.data, dict):
                    raise ValidationError("Supply a JSON object.")
                if not policy.typed:
                    validate_payload_types(request.data)
        self.policy_entered = True

    def handle_exception(self, exc):
        self.policy_error = True
        policy = getattr(self, "action_policy", None)
        if getattr(self, "policy_entered", False):
            if policy.boundary == "company" and isinstance(exc, IntegrityError):
                exc = ValidationError(
                    "An inventory code or operation identity already exists. Reload and review the current values."
                )
            elif policy.boundary == "planning" and isinstance(
                exc, DjangoValidationError
            ):
                exc = ValidationError(
                    "A supplied identifier or field value is invalid."
                )
        return super().handle_exception(exc)

    def finalize_response(self, request, response, *args, **kwargs):
        policy = getattr(self, "action_policy", None)
        if (
            policy is not None
            and policy.boundary == "planning"
            and getattr(self, "policy_entered", False)
            and not getattr(self, "policy_error", False)
        ):
            response["Cache-Control"] = "private, no-store"
        return super().finalize_response(request, response, *args, **kwargs)
