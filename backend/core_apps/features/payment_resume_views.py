from core_apps.features.http import ActionPolicy, FeatureAPIView

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .renderers import FeatureJsonRenderer
from .rental_phase3_views_parts.rent_invoice_quote import (
    _attempt,
    PaymentReconcileThrottle,
)
from .services.rental_phase3 import payment_attempt_payload
from .services.payment_resume import resume


class PaymentAttemptResumeView(FeatureAPIView):
    name = "Payment Attempt Resume"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    throttle_classes = [PaymentReconcileThrottle]
    action_policies = {
        "post": ActionPolicy(
            "payment_resume_views",
            "payment_attempt_resume",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, attempt_id):
        attempt = resume(
            request.user, _attempt(request, attempt_id), request.data.get("request_key")
        )
        payload = payment_attempt_payload(attempt, request.user)
        if attempt.invoice.purpose == "rent":
            from .rental_phase3_views_parts.rent_invoice_quote import _active_session

            payload["checkout_session"] = _active_session(attempt)
        return Response(payload)


# Stable callable import for integrations; URLs use the explicit class.
payment_attempt_resume = PaymentAttemptResumeView.as_view()

__all__ = ["PaymentAttemptResumeView"]
