"""Forward a server-owned snapshot without disclosing its original conversation."""

import hashlib
import json
import uuid

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import APIException, NotFound, ValidationError
from rest_framework import serializers

from core_apps.chat.models import ChatAttachment, Conversation, Message
from .group_access import authorize, visible_messages
from .group_limits import ChatConflict
from .group_projection import sender_payload
from .group_send import send_group_message
from .workspace_inbox import visible


class ForwardBody(serializers.Serializer):
    client_message_id = serializers.UUIDField()
    destination_id = serializers.UUIDField()
    source_membership_period = serializers.UUIDField()
    destination_membership_period = serializers.UUIDField()
    expected_revision = serializers.IntegerField(min_value=1)


def source_message(conversation, user, message_id):
    conversation, participant, _ = authorize(conversation, user)
    message = get_object_or_404(visible_messages(conversation, participant), id=message_id, deleted_at__isnull=True)
    if message.kind == "system":
        raise ValidationError("System messages cannot be forwarded.")
    return message, participant


def destinations(conversation, user, message_id, query):
    message, _ = source_message(conversation, user, message_id)
    candidates = visible(user).exclude(pk=conversation.pk).select_related("housing_group", "company_request")
    if message.kind == "property":
        candidates = candidates.filter(kind="housing_group")
    if query.get("q", "").strip():
        from .search import filter_conversations, query_text

        candidates = filter_conversations(candidates, query_text(query), user)
    result = []
    for candidate in candidates.order_by("-last_message_at", "-id"):
        try:
            target, participant, _ = authorize(candidate, user, action="send_message")
        except APIException:
            continue
        title = (
            sender_payload(target.participants.exclude(pk=user.pk).get())["name"]
            if target.kind == "direct"
            else candidate.housing_group.name if target.kind == "housing_group" else candidate.company_request.title
        )
        result.append(
            {
                "id": str(target.id),
                "title": title,
                "conversation_type": target.kind,
                "membership_period": str(participant.membership_period),
            }
        )
    return result


def lock_roots(conversations):
    # Direct operations lock people first. Acquire every shared root in a stable
    # order so simultaneous A->B and B->A forwards cannot invert those locks.
    from core_apps.users.models import User
    from core_apps.features.company_models import Company, CompanyHousingRequest
    from core_apps.features.planning_models import HousingGroup

    direct = [c.pk for c in conversations if c.kind == "direct"]
    people = User.objects.filter(conversation_participants__conversation_id__in=direct).values_list("pk", flat=True)
    list(User.objects.select_for_update().filter(pk__in=people).order_by("pk"))
    requests = CompanyHousingRequest.objects.filter(
        pk__in=[c.company_request_id for c in conversations if c.kind == "company_request"]
    )
    list(Company.objects.select_for_update().filter(pk__in=requests.values("company_id")).order_by("pk"))
    list(requests.select_for_update().order_by("pk"))
    list(
        HousingGroup.objects.select_for_update()
        .filter(pk__in=[c.housing_group_id for c in conversations if c.kind == "housing_group"])
        .order_by("pk")
    )


@transaction.atomic
def forward_message(conversation, user, message_id, data):
    body = ForwardBody(data=data)
    body.is_valid(raise_exception=True)
    body = body.validated_data
    target = get_object_or_404(Conversation, id=body["destination_id"])
    if target.pk == conversation.pk:
        raise ValidationError("Choose another conversation.")
    authorize(conversation, user)
    authorize(target, user, action="send_message")
    lock_roots([conversation, target])
    grants = {
        c.pk: authorize(c, user, action="send_message" if c.pk == target.pk else "read_chat", lock=True)
        for c in sorted([conversation, target], key=lambda c: c.pk)
    }
    conversation, source_member, _ = grants[conversation.pk]
    target, recipient, _ = grants[target.pk]
    if str(body["source_membership_period"]) != str(source_member.membership_period) or str(
        body["destination_membership_period"]
    ) != str(recipient.membership_period):
        raise ChatConflict("Refresh the current chat membership before retrying.")
    fingerprint = hashlib.sha256(
        json.dumps(
            ["forward", str(conversation.id), str(message_id), {k: str(v) for k, v in body.items()}], sort_keys=True
        ).encode()
    ).hexdigest()
    existing = Message.objects.filter(
        conversation=target, sender=user, client_message_id=body["client_message_id"]
    ).first()
    if existing:
        if existing.payload_fingerprint != fingerprint or not existing.is_forwarded:
            raise ChatConflict()
        if existing.sequence < recipient.visible_from_sequence:
            raise ChatConflict("This operation belongs to an earlier membership period.")
        return existing
    message = visible_messages(conversation, source_member).filter(id=message_id, deleted_at__isnull=True).first()
    if message is None:
        raise NotFound("This message is unavailable.")
    if message.kind == "system":
        raise ValidationError("System messages cannot be forwarded.")
    if message.revision != body["expected_revision"]:
        raise ChatConflict("This message changed. Reload it before continuing.")
    attachments = []
    for original in message.attachments.all():
        if original.state != "attached":
            raise ValidationError("An attachment is unavailable.")
        clone = ChatAttachment.objects.create(
            conversation=target,
            uploader=user,
            membership_period=recipient.membership_period,
            client_upload_id=uuid.uuid4(),
            kind=original.kind,
            state="ready",
            **{
                name: getattr(original, name)
                for name in (
                    "fingerprint",
                    "storage_key",
                    "thumbnail_key",
                    "mime_type",
                    "byte_size",
                    "width",
                    "height",
                    "duration_ms",
                    "original_name",
                    "waveform",
                )
            },
        )
        attachments.append(str(clone.id))
    payload = {
        "client_message_id": str(body["client_message_id"]),
        "membership_period": str(recipient.membership_period),
        "kind": message.kind,
        "content": message.content,
        "attachment_ids": attachments,
    }
    if message.kind == "location":
        payload["location"] = message.location
    if message.kind == "property":
        payload["property"] = message.property_reference
    forwarded = send_group_message(target, user, payload)
    forwarded.is_forwarded = True
    forwarded.payload_fingerprint = fingerprint
    forwarded.save(update_fields=["is_forwarded", "payload_fingerprint"])
    return forwarded
