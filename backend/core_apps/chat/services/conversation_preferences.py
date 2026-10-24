"""Per-viewer organization; a workspace never grants business authorization."""

import hashlib
import uuid
from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from rest_framework.exceptions import PermissionDenied, ValidationError
from core_apps.chat.models import Conversation, ConversationParticipant, ConversationWorkspace, ChatBlock, ChatList

WORKSPACES = {"individual", "student", "owner"}


def viewer_workspace(conversation, user):
    if conversation.kind == "housing_group":
        return "student"
    if conversation.kind == "company_request":
        return "company"
    values = list(conversation.workspace_contexts.filter(user=user).values_list("workspace", flat=True))
    return values[0] if len(values) == 1 else ""


def contextual_conversation(user, other, workspace, context=None):
    if workspace not in WORKSPACES:
        raise ValidationError({"workspace": "Choose a personal message workspace."})
    if context is not None and not isinstance(context, dict):
        raise ValidationError({"rental_context": "Supply a rental context object."})
    peer_workspace = workspace
    if context and context.get("property_id"):
        from core_apps.properties.models import Property, PropertyVisit
        try:
            prop = Property.objects.filter(id=context["property_id"]).first()
        except (ValueError, TypeError, DjangoValidationError):
            raise ValidationError({"rental_context": "Invalid property identity."})
        if not prop or prop.owner_id not in {user.pk, other.pk}:
            raise PermissionDenied("The rental context does not belong to either participant.")
        if prop.owner_id == other.pk:
            if workspace == "owner":
                raise ValidationError({"workspace": "Open this rental conversation from your renter workspace."})
            peer_workspace = "owner"
        else:
            if workspace != "owner":
                raise ValidationError({"workspace": "Open your listing conversation from the owner workspace."})
            # Reopening from an owner visit must reuse the renter's actual context.
            visits = PropertyVisit.objects.filter(property=prop, tenant=other)
            if context.get("visit_id"):
                try:
                    visit = visits.filter(id=context["visit_id"]).first()
                except (ValueError, TypeError, DjangoValidationError):
                    raise ValidationError({"rental_context": "Invalid visit identity."})
                if not visit:
                    raise PermissionDenied("The visit does not belong to this rental context.")
            else:
                visit = visits.order_by("-created_at").first()
            if not visit:
                matches = Conversation.objects.filter(kind="direct", direct_context_key__isnull=False,
                    workspace_contexts__user=user, workspace_contexts__workspace="owner",
                    participant_set__user=other, rental_context__properties=prop)
                if matches.count() == 1:
                    return matches.first()
            peer_workspace = ("student" if visit.academic_plan_id or visit.context_kind == "group" else visit.renter_workspace) if visit else "individual"
    identities = sorted([(str(user.id), workspace), (str(other.id), peer_workspace)])
    key = hashlib.sha256(repr(identities).encode()).hexdigest()
    conversation = Conversation.objects.filter(direct_context_key=key).first()
    if conversation:
        return conversation
    from .message_service_parts.get_or_create_direct_conversation import direct_message_blocked
    if direct_message_blocked(user, other, lock=True):
        raise PermissionDenied("Messaging consent is not active for this connection.")
    from core_apps.chat.moderation.policy import require_new_business
    require_new_business(user)
    require_new_business(other)
    conversation = Conversation.objects.create(direct_context_key=key)
    ConversationParticipant.objects.bulk_create([
        ConversationParticipant(conversation=conversation, user=person, membership_period=uuid.uuid4())
        for person in (user, other)
    ])
    ConversationWorkspace.objects.bulk_create([
        ConversationWorkspace(conversation=conversation, user=user, workspace=workspace),
        ConversationWorkspace(conversation=conversation, user=other, workspace=peer_workspace),
    ])
    return conversation


def preferences_payload(conversation, user, participant=None):
    participant = participant or conversation.participant_set.get(user=user)
    other = conversation.participants.exclude(pk=user.pk).first() if conversation.kind == "direct" else None
    own = bool(other and ChatBlock.objects.filter(user=user, blocked_user=other).exists())
    blocked = bool(other and ChatBlock.objects.filter(Q(user=user, blocked_user=other) | Q(user=other, blocked_user=user)).exists())
    return {
        "workspace": viewer_workspace(conversation, user),
        "company_id": str(conversation.company_request.company.id) if conversation.kind == "company_request" else "",
        "can_block": conversation.kind == "direct",
        "consent_revision": conversation.consent_revision,
        "delete_through_sequence": conversation.last_sequence,
        "is_favorite": participant.is_favorite,
        "is_muted": participant.is_muted,
        "blocked_by_me": own,
        "is_blocked": blocked,
        "list_ids": [str(x) for x in conversation.private_lists.filter(user=user).values_list("id", flat=True)],
    }


@transaction.atomic
def update_preferences(conversation, user, data):
    from .group_access import authorize
    from .group_events import record_event
    if not isinstance(data, dict):
        raise ValidationError("Supply a conversation preference object.")
    # Pair locks have the same order as conversation creation. Acquiring them
    # before thread locks avoids reciprocal block/classification deadlocks.
    authorize(conversation, user)
    if "blocked" in data:
        from django.contrib.auth import get_user_model
        list(get_user_model().objects.select_for_update().filter(
            pk__in=conversation.participants.values_list("pk", flat=True)
        ).order_by("pk"))
    conversation, participant, _ = authorize(conversation, user, lock=True)
    allowed = {"is_favorite", "is_muted", "blocked", "delete_for_me", "list_ids", "delete_through_sequence"}
    if set(data) - allowed:
        raise ValidationError("Unsupported conversation preference.")
    for field in ("is_favorite", "is_muted", "blocked", "delete_for_me"):
        if field in data and type(data[field]) is not bool:
            raise ValidationError({field: "Supply a boolean."})
    for field in ("is_favorite", "is_muted"):
        if field in data:
            setattr(participant, field, data[field])
    if data.get("delete_for_me"):
        cutoff = data.get("delete_through_sequence")
        if type(cutoff) is not int or not 0 <= cutoff <= conversation.last_sequence:
            raise ValidationError({"delete_through_sequence": "Refresh the conversation before clearing history."})
        cutoff = max(cutoff, participant.hidden_through_sequence or 0)
        participant.hidden_through_sequence = cutoff
        participant.visible_from_sequence = cutoff + 1
        participant.last_read_sequence = max(participant.last_read_sequence, cutoff)
        from .group_access import unread_count
        participant.unread_count = unread_count(conversation, participant)
    if "blocked" in data:
        if conversation.kind != "direct":
            raise ValidationError("Select a person to block in a direct conversation.")
        other = conversation.participants.exclude(pk=user.pk).get()
        if data["blocked"]:
            _, changed = ChatBlock.objects.get_or_create(user=user, blocked_user=other)
        else:
            changed = ChatBlock.objects.filter(user=user, blocked_user=other).delete()[0] > 0
        if changed:
            conversation.consent_revision += 1
            conversation.save(update_fields=["consent_revision"])
        # Invalidate every open thread between these people, across workspaces.
        for thread in Conversation.objects.select_for_update().filter(kind="direct", participant_set__user=user).filter(participant_set__user=other).exclude(pk=conversation.pk).order_by("pk"):
            if changed:
                thread.consent_revision += 1
                thread.save(update_fields=["consent_revision"])
            record_event(thread, "conversation.updated", actor=user)
    if "list_ids" in data:
        ids = data["list_ids"]
        if not isinstance(ids, list) or any(not isinstance(x, str) for x in ids):
            raise ValidationError({"list_ids": "Supply your list identities."})
        try:
            organization = str(conversation.company_request.company.id) if conversation.kind == "company_request" else ""
            rows = list(ChatList.objects.filter(user=user, workspace=viewer_workspace(conversation, user), organization=organization, id__in=ids))
        except (ValueError, TypeError, DjangoValidationError):
            raise ValidationError({"list_ids": "Invalid list identity."})
        if len(rows) != len(set(ids)):
            raise PermissionDenied("A list is unavailable in this workspace.")
        conversation.private_lists.remove(*conversation.private_lists.filter(user=user))
        conversation.private_lists.add(*rows)
    participant.save()
    record_event(conversation, "conversation.updated", actor=user)
    return preferences_payload(conversation, user, participant)
