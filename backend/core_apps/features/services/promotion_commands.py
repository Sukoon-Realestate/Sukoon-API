"""Create one promotion or resolve its original command without creating one."""

from datetime import timedelta
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from core_apps.properties.models import Property
from core_apps.properties.services.public_access import public_properties
from core_apps.chat.moderation.policy import require_new_business as require_policy
from core_apps.users.services.new_business import require_new_business
from ..catalog_models import PromotionOption
from ..models import BoostCampaign, IdempotencyRecord
from ..views_parts.rental_operation_lookup import Conflict, _remember, _replay


class Identity(serializers.Serializer):
    property_id = serializers.UUIDField()
    request_key = serializers.CharField(max_length=100)


class Selection(Identity):
    option_id = serializers.CharField(max_length=40)
    option_revision = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        unknown = set(self.initial_data) - set(self.fields)
        if unknown:
            raise ValidationError({key: "Unsupported field." for key in unknown})
        return attrs


def validated(schema, payload):
    serializer = schema(data=payload)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


@transaction.atomic
def create(user, payload):
    body = validated(Selection, payload)
    # Same ordering as deletion review and recovery fencing, before property/FK locks.
    get_user_model().objects.select_for_update(no_key=True).get(pk=user.pk)
    replay = _replay(user, "boost.create", body["request_key"], body)
    if replay:
        return replay.data, replay.status_code
    require_new_business(user.pk)
    require_policy(user)
    prop = get_object_or_404(
        Property.objects.select_for_update(), id=body["property_id"], owner=user
    )
    option = (
        PromotionOption.objects.select_for_update()
        .filter(id=body["option_id"], active=True)
        .first()
    )
    if not option:
        raise ValidationError({"option_id": "Unsupported promotion option."})
    if body["option_revision"] != option.revision:
        raise Conflict(
            "The promotion option changed. Review its current price and duration.",
            code="catalog_changed",
        )
    if (
        not prop.is_verified
        or not public_properties(Property.objects.filter(pk=prop.pk)).exists()
    ):
        raise ValidationError("Only published, verified properties can be promoted.")
    now = timezone.now()
    if (
        BoostCampaign.objects.filter(property=prop, status="pending").exists()
        or BoostCampaign.objects.filter(
            property=prop, status="active", ends_at__gt=now
        ).exists()
    ):
        raise ValidationError("This property already has an active campaign.")
    campaign = BoostCampaign.objects.create(
        owner=user,
        property=prop,
        option_id=option.id,
        duration_days=option.duration_days,
        starts_at=now,
        ends_at=now + timedelta(days=option.duration_days),
        status="pending" if option.amount_minor else "active",
    )
    from .billing_sources import promotion_invoice, source_invoices

    if option.amount_minor:
        promotion_invoice(campaign, option)
    data = {
        "billing_invoices": source_invoices("promotion", campaign.id),
        "id": str(campaign.id),
        "subject_id": str(prop.id),
        "status": campaign.status,
        "message": (
            "Awaiting promotion payment."
            if option.amount_minor
            else "Promotion activated."
        ),
    }
    _remember(
        user,
        "boost.create",
        body["request_key"],
        body,
        data,
        201,
        request_subject_id=prop.id,
        result_subject_id=campaign.id,
    )
    return data, 201


@transaction.atomic
def resolve(user, payload):
    body = validated(Identity, payload)
    get_user_model().objects.select_for_update(no_key=True).get(pk=user.pk)
    record = IdempotencyRecord.objects.filter(
        user=user, operation="boost.create", request_key=body["request_key"]
    ).first()
    result = {
        "request_key": body["request_key"],
        "property_id": str(body["property_id"]),
    }
    if record:
        subject = record.request_subject_id or record.response_data.get("subject_id")
        if str(subject) != result["property_id"]:
            raise Conflict(
                "The original operation belongs to a different property.",
                code="idempotency_conflict",
            )
        if record.recovery_status == IdempotencyRecord.RecoveryStatus.ABSENT_FINAL:
            return {**result, "status": "absent_final"}
        if record.recovery_status != IdempotencyRecord.RecoveryStatus.CONFIRMED:
            return {**result, "status": record.recovery_status}
        return {**result, "status": "confirmed", "receipt": record.response_data}
    prop = get_object_or_404(
        Property.objects.select_for_update(), id=body["property_id"], owner=user
    )
    IdempotencyRecord.objects.create(
        user=user,
        operation="boost.create",
        request_key=body["request_key"],
        request_subject_id=prop.id,
        response_data={},
        response_status=409,
        recovery_status=IdempotencyRecord.RecoveryStatus.ABSENT_FINAL,
    )
    return {**result, "status": "absent_final"}
