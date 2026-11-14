from functools import partial
from ..services.rental_lifecycle import claims_commands as commands

from core_apps.features.http import ActionPolicy, FeatureAPIView
from rest_framework.permissions import IsAuthenticated
from core_apps.features.renderers import FeatureJsonRenderer

from ..rental_lifecycle_serializers import ClaimBody, ReasonBody
from .common import validated, mutate


class VerificationClaimsView(FeatureAPIView):
    name = "Verification Claims"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "claims",
            "verification_claims",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request):
        data = validated(ClaimBody, request.data)

        authorize = partial(
            commands.verification_claims_post_authorize, actor=request.user, data=data
        )

        execute = partial(commands.verification_claims_post_execute, data=data)

        return mutate(request, "verification_claim.create", authorize, execute)


# Stable callable import for integrations; URLs use the explicit class.
verification_claims = VerificationClaimsView.as_view()


class RevokeClaimView(FeatureAPIView):
    name = "Revoke Claim"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "claims", "revoke_claim", boundary="standard", capability=None, typed=False
        ),
    }

    def post(self, request, claim_id):
        data = validated(ReasonBody, request.data)

        authorize = partial(
            commands.revoke_claim_post_authorize, actor=request.user, claim_id=claim_id
        )

        execute = partial(
            commands.revoke_claim_post_execute, actor=request.user, data=data
        )

        return mutate(
            request, f"verification_claim.revoke.{claim_id}", authorize, execute
        )


# Stable callable import for integrations; URLs use the explicit class.
revoke_claim = RevokeClaimView.as_view()
