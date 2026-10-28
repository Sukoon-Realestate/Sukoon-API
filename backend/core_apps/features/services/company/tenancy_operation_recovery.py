"""Fence an uncertain local review/handover without executing the intention.

The same actor and domain locks as company commands serialize this endpoint
with a delayed original request. Provider operations are deliberately excluded.
"""

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers
from ...models import IdempotencyRecord
from ..rental_lifecycle.common import require_actor, audit
from ..rental_phase2 import RentalConflict
from . import tenancy_access as access


class RecoveryBody(serializers.Serializer):
    request_key = serializers.UUIDField()
    action = serializers.ChoiceField(choices=["review", "handover"])
    role = serializers.ChoiceField(choices=["owner", "signer"], required=False)

    def validate(self, attrs):
        if set(self.initial_data) - set(self.fields):
            raise serializers.ValidationError("Unsupported recovery fields.")
        if attrs["action"] == "review" and "role" not in attrs:
            raise serializers.ValidationError({"role": "Required."})
        if attrs["action"] == "handover" and "role" in attrs:
            raise serializers.ValidationError({"role": "Not applicable."})
        return attrs


@transaction.atomic
def resolve(user, tenancy_id, body):
    actor = get_user_model().objects.select_for_update(no_key=True).get(pk=user.pk)
    require_actor(actor)
    item = access.get(actor, tenancy_id, lock=True)
    access.require_role(
        item,
        actor,
        {body["role"]} if body["action"] == "review" else {"owner", "coordinator"},
    )
    key = str(body["request_key"])
    operation = "company.tenancy." + body["action"]
    # Operation keys cannot be borrowed from another resource or command.
    records = list(IdempotencyRecord.objects.filter(user=actor, request_key=key))
    if any(
        row.operation != operation or str(row.request_subject_id) != str(item.id)
        for row in records
    ):
        raise RentalConflict(
            "This reference belongs to another operation.", code="idempotency_conflict"
        )
    record = records[0] if records else None
    if record is None:
        record = IdempotencyRecord.objects.create(
            user=actor,
            operation=operation,
            request_key=key,
            request_subject_id=item.id,
            result_subject_id=item.id,
            result_revision=item.revision,
            is_rental_operation=True,
            response_data={},
            response_status=409,
            recovery_status=IdempotencyRecord.RecoveryStatus.ABSENT_FINAL,
        )
        audit(
            item,
            actor,
            "company_operation_closed_without_execution",
            metadata={
                "operation": operation,
                "request_key": key,
            },
        )
    # No historical resource/contract/financial response is replayed here.
    return {
        "request_key": key,
        "request_subject_id": str(item.id),
        "status": record.recovery_status,
        "operation_receipt": {
            "id": str(record.id),
            "subject_id": str(record.result_subject_id),
            "request_key": key,
            "revision": record.result_revision,
            "status": record.recovery_status,
        },
    }
