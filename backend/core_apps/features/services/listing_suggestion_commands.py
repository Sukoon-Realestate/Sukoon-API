"""One provider attempt per receipt, without holding a database lock over HTTP."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError

from core_apps.properties.models import Property
from core_apps.users.models import User
from ..models import IdempotencyRecord, ListingSuggestion
from . import listing_assistant
from .planning_providers import DiscoveryUnavailable, provider_budget
from .rental_phase2 import fingerprint, replay_operation


OPERATION = "suggestion.create"


def message(language, english, arabic):
    return arabic if language == "ar" else english


def authorized(user, property_id, *, expected_epoch, auth_claims):
    if (
        not user.is_active
        or not user.is_verified
        or user.security_epoch != expected_epoch
    ):
        raise PermissionDenied("An active verified account is required.")
    if auth_claims is not None:
        from core_apps.users.services.sessions import validate_session

        validate_session(user, auth_claims)
    return (
        get_object_or_404(Property, id=property_id, owner=user) if property_id else None
    )


def create(user, payload, *, auth_claims=None):
    if not isinstance(payload, dict) or set(payload) - {
        "facts",
        "language",
        "request_key",
        "property_id",
    }:
        raise ValidationError("Supply only supported suggestion fields.")
    language, key = payload.get("language"), payload.get("request_key")
    if (
        not isinstance(language, str)
        or language not in {"ar", "en"}
        or not isinstance(key, str)
        or not key.strip()
        or len(key) > 100
    ):
        raise ValidationError(
            "Use language ar/en and a non-empty request key up to 100 characters."
        )
    facts = listing_assistant.public_facts(payload.get("facts"))
    property_id = payload.get("property_id")
    if property_id:
        from uuid import UUID

        try:
            UUID(str(property_id))
        except (ValueError, TypeError, AttributeError):
            raise ValidationError(
                {"property_id": "Supply a valid property ID."}
            ) from None

    with transaction.atomic():
        current = User.objects.select_for_update().get(pk=user.pk)
        prop = authorized(
            current,
            property_id,
            expected_epoch=user.security_epoch,
            auth_claims=auth_claims,
        )
        replay = replay_operation(current, OPERATION, key, payload)
        if replay:
            return replay
        if not listing_assistant.configured():
            return {
                "code": "assistant_not_configured",
                "message": message(
                    language,
                    "The writing assistant is unavailable. Continue writing and saving manually.",
                    "مساعد الكتابة غير متاح. يمكنك مواصلة الكتابة والحفظ يدويًا.",
                ),
            }, 503
        provider_budget(current, "listing_assistant")
        receipt = IdempotencyRecord.objects.create(
            user=current,
            operation=OPERATION,
            request_key=key,
            fingerprint=fingerprint(payload),
            request_subject_id=prop.id if prop else None,
            recovery_status=IdempotencyRecord.RecoveryStatus.PENDING,
            response_status=409,
            response_data={
                "code": "operation_in_progress",
                "message": message(
                    language,
                    "This suggestion is still processing. Check its result again, or continue writing manually.",
                    "هذا الاقتراح قيد المعالجة. تحقق من نتيجته مجددًا أو واصل الكتابة يدويًا.",
                ),
            },
        )

    try:
        title, description = listing_assistant.generate(facts, language)
    except DiscoveryUnavailable as error:
        # A timeout cannot prove that the provider did not process the prompt.
        # Replaying this key never makes a second paid/quota-consuming call.
        data = {
            "code": str(error.get_codes()),
            "message": message(
                language,
                "No usable suggestion was saved. You can continue writing manually or explicitly start a new suggestion.",
                "لم يُحفظ اقتراح صالح للاستخدام. يمكنك مواصلة الكتابة يدويًا أو بدء اقتراح جديد صراحةً.",
            ),
        }
        IdempotencyRecord.objects.filter(pk=receipt.pk).update(
            recovery_status=IdempotencyRecord.RecoveryStatus.UNKNOWN,
            response_data=data,
            response_status=503,
        )
        return data, 503

    with transaction.atomic():
        current = User.objects.select_for_update().get(pk=user.pk)
        # A suspended account or transferred property cannot receive a new result.
        prop = authorized(
            current,
            property_id,
            expected_epoch=user.security_epoch,
            auth_claims=auth_claims,
        )
        receipt = IdempotencyRecord.objects.select_for_update().get(pk=receipt.pk)
        warnings = [
            message(
                language,
                "Review every claim before applying this AI draft. It has not changed or published your property.",
                "راجع كل معلومة قبل تطبيق مسودة الذكاء الاصطناعي. لم تُعدّل العقار أو تنشره.",
            )
        ]
        suggestion = ListingSuggestion.objects.create(
            owner=current,
            property=prop,
            language=language,
            facts=facts,
            suggested_title=title,
            suggested_description=description,
            warnings=warnings,
        )
        data = {
            "id": str(suggestion.id),
            "property_id": str(prop.id) if prop else "",
            "suggested_title": title,
            "suggested_description": description,
            "warnings": warnings,
        }
        receipt.recovery_status = IdempotencyRecord.RecoveryStatus.CONFIRMED
        receipt.response_data, receipt.response_status = data, 201
        receipt.result_subject_id = suggestion.id
        receipt.save(
            update_fields=[
                "recovery_status",
                "response_data",
                "response_status",
                "result_subject_id",
                "updated_at",
            ]
        )
    return data, 201
