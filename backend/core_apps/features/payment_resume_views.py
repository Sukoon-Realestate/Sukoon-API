from rest_framework.decorators import (
    api_view,
    permission_classes,
    renderer_classes,
    throttle_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .renderers import FeatureJsonRenderer
from .rental_phase3_views_parts.rent_invoice_quote import (
    _attempt,
    PaymentReconcileThrottle,
)
from .services.rental_phase3 import payment_attempt_payload
from .services.payment_resume import resume


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
@throttle_classes([PaymentReconcileThrottle])
def payment_attempt_resume(request, attempt_id):
    attempt = resume(
        request.user, _attempt(request, attempt_id), request.data.get("request_key")
    )
    payload = payment_attempt_payload(attempt, request.user)
    if attempt.invoice.purpose == "rent":
        from .rental_phase3_views_parts.rent_invoice_quote import _active_session

        payload["checkout_session"] = _active_session(attempt)
    return Response(payload)
