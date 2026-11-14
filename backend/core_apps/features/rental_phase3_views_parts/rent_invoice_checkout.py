"""Rental phase3 views: rent invoice checkout."""

from core_apps.features.http import ActionPolicy, FeatureAPIView


from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from ..providers import fake_provider_available, verify_fake_webhook
from ..renderers import FeatureJsonRenderer
from .owner_payables import apply_fake_payment_event


class RentInvoiceCheckoutView(FeatureAPIView):
    name = "Rent Invoice Checkout"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "rent_invoice_checkout",
            "rent_invoice_checkout",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, invoice_id):
        from ..services.rental_payment_commands import checkout_rent

        result = checkout_rent(
            request.user,
            request.auth,
            request.data,
            request.headers.get("X-Sokoun-Authorization", ""),
            invoice_id,
        )
        return Response(result.data, status=result.status)


# Stable callable import for integrations; URLs use the explicit class.
rent_invoice_checkout = RentInvoiceCheckoutView.as_view()


class FakePaymentWebhookView(FeatureAPIView):
    name = "Fake Payment Webhook"
    http_method_names = ["post", "options"]
    permission_classes = [AllowAny]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "rent_invoice_checkout",
            "fake_payment_webhook",
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

        return Response(apply_fake_payment_event(request.data))


# Stable callable import for integrations; URLs use the explicit class.
fake_payment_webhook = FakePaymentWebhookView.as_view()

__all__ = [
    "FakePaymentWebhookView",
    "RentInvoiceCheckoutView",
    "fake_payment_webhook",
    "rent_invoice_checkout",
]
