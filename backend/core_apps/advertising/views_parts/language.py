"""Views: language."""

from datetime import timezone as datetime_timezone
from rest_framework import status
from rest_framework.response import Response


MESSAGES = {
    "plans": {"en": "Available plans.", "ar": "الخطط المتاحة."},
    "created": {
        "en": "Advertisement created, awaiting simulated payment.",
        "ar": "تم إنشاء الإعلان وهو بانتظار الدفع التجريبي.",
    },
    "owners": {"en": "Owner advertisements.", "ar": "إعلانات المالك."},
    "detail": {"en": "Advertisement details.", "ar": "تفاصيل الإعلان."},
    "paid": {
        "en": "Simulated payment succeeded. No money collected.",
        "ar": "نجح الدفع التجريبي. لم يتم تحصيل أي أموال.",
    },
    "active": {"en": "Active advertisements.", "ar": "الإعلانات النشطة."},
    "found": {"en": "Operation found.", "ar": "تم العثور على العملية."},
    "processing": {
        "en": "Operation is still processing.",
        "ar": "ما زالت العملية قيد التنفيذ.",
    },
    "not_found": {
        "en": "No committed advertisement. Retry is safe.",
        "ar": "لا يوجد إعلان مثبت. إعادة المحاولة آمنة.",
    },
    "rejected": {
        "en": "Rejected before creation. Correct the input.",
        "ar": "رُفض الطلب قبل الإنشاء. صحح البيانات.",
    },
}


ERROR_MESSAGES_AR = {
    "Please correct the invalid fields.": "يرجى تصحيح الحقول غير الصالحة.",
    "The banner must not exceed 10 MiB.": "يجب ألا يتجاوز حجم البانر 10 ميبيبايت.",
    "The banner is not a valid supported image.": "ملف البانر ليس صورة صالحة ومدعومة.",
    "Only JPEG, PNG, and WebP banners are supported.": "تُدعم صور JPEG وPNG وWebP فقط.",
    "The selected property is not eligible for publication.": "العقار المحدد غير مؤهل للنشر.",
    "The selected offer is not eligible for publication.": "العرض المحدد غير مؤهل للنشر.",
    "This operation ID was already used with different data.": "استُخدم معرف العملية هذا سابقًا ببيانات مختلفة.",
    "This operation is still processing.": "ما زالت هذه العملية قيد التنفيذ.",
    "This operation is already being processed.": "هذه العملية قيد التنفيذ بالفعل.",
    "The selected plan is unavailable.": "الخطة المحددة غير متاحة.",
    "The selected plan changed. Review the current plan before continuing.": (
        "تغيرت الخطة المحددة. راجع الخطة الحالية قبل المتابعة."
    ),
    "Advertisement not found.": "الإعلان غير موجود.",
    "This account is not eligible to publish advertisements.": "هذا الحساب غير مؤهل لنشر الإعلانات.",
    "This advertisement cannot be activated from its current state.": "لا يمكن تفعيل هذا الإعلان من حالته الحالية.",
    "The payment operation ID does not match this advertisement.": "معرف عملية الدفع لا يطابق هذا الإعلان.",
    "Only simulated payment is available.": "الدفع التجريبي هو الوضع المتاح فقط.",
    "The advertisement destination is no longer eligible.": "وجهة الإعلان لم تعد مؤهلة.",
    "The advertisement media is unavailable.": "وسائط الإعلان غير متاحة.",
}


def language(request):
    from core_apps.common.locale_middleware import resolve_request_language

    return resolve_request_language(request)


def message(request, key):
    return MESSAGES[key][language(request)]


def envelope(data, text, *, status_code=200):
    return Response(
        {"key": "success", "message": text, "data": data}, status=status_code
    )


def error_response(error, request=None):
    text = error.message
    if request is not None and language(request) == "ar":
        text = ERROR_MESSAGES_AR.get(text, text)
    response = Response(
        {
            "key": "error",
            "message": text,
            "data": None,
            "errors": error.errors,
        },
        status=error.status_code,
    )

    codes = {
        "invoice_required",
        "too_large",
        "invalid_image",
        "unsupported_type",
        "not_eligible",
        "idempotency_conflict",
        "operation_processing",
        "not_available",
        "plan_changed",
        "invalid_payment_operation",
        "unsupported",
        "invalid_transition",
        "unavailable",
    }
    if isinstance(error.errors, dict):
        for errors in error.errors.values():
            for code in errors if isinstance(errors, list) else []:
                if code in codes:
                    response["X-App-Error-Code"] = code
                    return response
    return response


def validation_error_response(serializer, request):
    return Response(
        {
            "key": "error",
            "message": (
                ERROR_MESSAGES_AR["Please correct the invalid fields."]
                if language(request) == "ar"
                else "Please correct the invalid fields."
            ),
            "data": None,
            "errors": serializer.errors,
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


def finalize(response, request, *, private=False, public_ttl=None):
    eff_lang = language(request)
    response["Content-Language"] = eff_lang
    response["Vary"] = "Accept-Language"
    if private:
        response["Cache-Control"] = "no-store"
    elif public_ttl is not None:
        # Crucial for edge proxies / CDNs: use private, max-age so edge caches
        # never serve English-cached responses to Arabic-accepting users.
        response["Cache-Control"] = (
            f"private, max-age={max(0, int(public_ttl))}, must-revalidate"
        )
    return response


def iso8601(value):
    if value is None:
        return None
    value = value.astimezone(datetime_timezone.utc)
    return value.isoformat().replace("+00:00", "Z")
