"""One atomic, ordered, idempotent send across the reviewed destinations."""

import hashlib
import json
import uuid
from django.db import transaction, connection
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from core_apps.chat.models import Conversation, ChatForwardBatch
from .group_access import authorize
from .group_limits import ChatConflict
from .forwarding import forward_message, lock_roots


class SourceMessage(serializers.Serializer):
    id = serializers.UUIDField()
    expected_revision = serializers.IntegerField(min_value=1)


class Destination(serializers.Serializer):
    id = serializers.UUIDField()
    membership_period = serializers.UUIDField()


class BatchBody(serializers.Serializer):
    operation_id = serializers.UUIDField()
    source_membership_period = serializers.UUIDField()
    messages = SourceMessage(many=True, min_length=1, max_length=20)
    destinations = Destination(many=True, min_length=1, max_length=5)

    def validate(self, values):
        for key in ["messages", "destinations"]:
            if len({v["id"] for v in values[key]}) != len(values[key]):
                raise serializers.ValidationError("Choose each message and conversation only once.")
        return values


@transaction.atomic
def forward_batch(source, user, data):
    body = BatchBody(data=data)
    body.is_valid(raise_exception=True)
    values = body.validated_data
    targets = [get_object_or_404(Conversation, id=t["id"]) for t in values["destinations"]]
    # Serialize reuse of one operation identity without locking group users.
    # Group sends hold their group root and take FK key-share locks on users.
    if connection.vendor == "postgresql":
        key = int.from_bytes(
            hashlib.sha256(f"chat-forward:{user.pk}:{values['operation_id']}".encode()).digest()[:8], "big", signed=True
        )
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [key])
    lock_roots([source, *targets])
    grants = {
        c.pk: authorize(c, user, action="read_chat" if c.pk == source.pk else "send_message", lock=True)
        for c in sorted({c.pk: c for c in [source, *targets]}.values(), key=lambda c: c.pk)
    }
    if grants[source.pk][1].membership_period != values["source_membership_period"]:
        raise ChatConflict("Refresh the current chat membership before retrying.")
    for target, requested in zip(targets, values["destinations"]):
        if target.pk == source.pk or grants[target.pk][1].membership_period != requested["membership_period"]:
            raise ChatConflict("Refresh the selected conversations before forwarding.")
    fingerprint = hashlib.sha256(json.dumps([str(source.id), values], default=str, sort_keys=True).encode()).hexdigest()
    receipt = ChatForwardBatch.objects.filter(user=user, operation_id=values["operation_id"]).first()
    if receipt:
        if receipt.fingerprint != fingerprint:
            raise ChatConflict()
        return receipt.result
    messages = {str(m["id"]): m for m in values["messages"]}
    ordered = list(source.messages.filter(id__in=messages).order_by("sequence"))
    if len(ordered) != len(messages):
        raise serializers.ValidationError("A selected message is unavailable.")
    result = []
    for target, requested in zip(targets, values["destinations"]):
        copied = []
        for message in ordered:
            forwarded = forward_message(
                source,
                user,
                message.id,
                {
                    "client_message_id": str(
                        uuid.uuid5(values["operation_id"], str(target.id) + ":" + str(message.id))
                    ),
                    "destination_id": str(target.id),
                    "source_membership_period": str(values["source_membership_period"]),
                    "destination_membership_period": str(requested["membership_period"]),
                    "expected_revision": messages[str(message.id)]["expected_revision"],
                },
            )
            copied.append(str(forwarded.id))
        result.append({"conversation_id": str(target.id), "message_ids": copied})
    response = {"operation_id": str(values["operation_id"]), "destinations": result, "message_count": len(ordered)}
    ChatForwardBatch.objects.create(
        user=user, operation_id=values["operation_id"], fingerprint=fingerprint, result=response
    )
    return response
