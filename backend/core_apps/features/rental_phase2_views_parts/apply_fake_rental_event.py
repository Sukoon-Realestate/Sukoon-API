"""Rental phase2 views: apply fake rental event."""

from core_apps.features.http import ActionPolicy, FeatureAPIView


from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from ..providers import fake_provider_available, verify_fake_webhook
from ..renderers import FeatureJsonRenderer


from core_apps.features.services.rental_provider_events import (
    apply_fake_rental_event as apply_fake_rental_event,
)


class FakeRentalProviderWebhookView(FeatureAPIView):
    name = "Fake Rental Provider Webhook"
    http_method_names = ["post", "options"]
    permission_classes = [AllowAny]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "apply_fake_rental_event",
            "fake_rental_provider_webhook",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request):
        if not fake_provider_available():
            raise NotFound()
        if not verify_fake_webhook(
            request.data, request.headers.get("X-Rental-Signature")
        ):
            raise PermissionDenied("Invalid provider signature.")

        return Response(apply_fake_rental_event(request.data))


# Stable callable import for integrations; URLs use the explicit class.
fake_rental_provider_webhook = FakeRentalProviderWebhookView.as_view()

__all__ = [
    "FakeRentalProviderWebhookView",
    "apply_fake_rental_event",
    "fake_rental_provider_webhook",
]
