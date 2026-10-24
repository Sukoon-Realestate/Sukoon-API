import json

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .paymob import BOOLEAN_FIELDS, callback_values, reported_status, valid_signature
from .paymob_models import PaymobCallbackEvent


def verified_values(request, data, *, redirect=False):
    if not settings.PAYMOB_HMAC_SECRET or not settings.PAYMOB_INTEGRATION_ID:
        return None, JsonResponse(
            {"error": "payment_provider_not_configured"}, status=503
        )
    if len(request.GET.getlist("hmac")) != 1:
        return None, JsonResponse({"error": "invalid_signature"}, status=403)
    try:
        values = callback_values(data, redirect=redirect)
    except (KeyError, TypeError, ValueError):
        return None, JsonResponse({"error": "invalid_callback"}, status=400)
    if not valid_signature(values, request.GET["hmac"], settings.PAYMOB_HMAC_SECRET):
        return None, JsonResponse({"error": "invalid_signature"}, status=403)
    if values["integration_id"] != str(settings.PAYMOB_INTEGRATION_ID):
        return None, JsonResponse({"error": "unexpected_integration"}, status=403)
    if values["currency"] != "EGP":
        return None, JsonResponse({"error": "unsupported_currency"}, status=400)
    return values, None


@csrf_exempt
@never_cache
@require_POST
def webhook(request):
    if request.content_type != "application/json":
        return JsonResponse({"error": "json_required"}, status=415)
    try:
        payload = json.loads(request.body)
    except (ValueError, UnicodeError):
        return JsonResponse({"error": "invalid_json"}, status=400)
    if not isinstance(payload, dict) or payload.get("type") != "TRANSACTION":
        return JsonResponse({"error": "unsupported_callback"}, status=400)
    values, error = verified_values(request, payload.get("obj"))
    if error is not None:
        return error
    # Acknowledge only after durable storage. DB failures propagate as 5xx so
    # Paymob can retry; a repeated signed event is safe to acknowledge again.
    event, created = PaymobCallbackEvent.objects.get_or_create(
        signature=request.GET["hmac"].lower(),
        defaults={
            "transaction_id": values["id"],
            "order_id": values["order"],
            "integration_id": values["integration_id"],
            "amount_cents": int(values["amount_cents"]),
            "currency": values["currency"],
            "reported_status": reported_status(values),
            "flags": {key: values[key] == "true" for key in BOOLEAN_FIELDS},
        },
    )
    from core_apps.features.services.paymob_payments import process_callback
    from rest_framework.exceptions import APIException

    try:
        process_callback(event)
    except APIException:
        return JsonResponse({"error": "payment_reconciliation_pending"}, status=503)
    return JsonResponse({"received": True, "duplicate": not created})


@never_cache
@require_GET
def payment_return(request):
    # Reject ambiguous query parameters rather than picking a signed value.
    if any(len(request.GET.getlist(key)) != 1 for key in request.GET):
        return HttpResponse("Invalid payment return parameters.", status=400)
    values, error = verified_values(request, request.GET.dict(), redirect=True)
    if error is not None:
        return error
    if request.GET.get("state") or request.GET.get("payment_attempt_id"):
        import hmac
        import uuid
        from core_apps.features.models import CheckoutSession

        try:
            identity = uuid.UUID(request.GET.get("payment_attempt_id", ""))
        except ValueError:
            return HttpResponse("Invalid payment return parameters.", status=400)
        session = (
            CheckoutSession.objects.select_related("attempt__paymob_payment")
            .filter(attempt__id=identity)
            .first()
        )
        if not session or not hmac.compare_digest(
            session.return_state, request.GET.get("state", "")
        ):
            return HttpResponse("Invalid payment return state.", status=403)
        payment = getattr(session.attempt, "paymob_payment", None)
        if (
            not payment
            or payment.order_id != values["order"]
            or session.attempt.amount_minor != int(values["amount_cents"])
        ):
            return HttpResponse("Invalid payment return identity.", status=403)
    # This browser return is display-only. It never creates a callback event
    # or changes an invoice, subscription, booking or payment state.
    response = render(
        request,
        "payments/paymob_return.html",
        {
            "payment_status": reported_status(values),
        },
    )
    response["Referrer-Policy"] = "no-referrer"
    response["X-Robots-Tag"] = "noindex, nofollow"
    return response
