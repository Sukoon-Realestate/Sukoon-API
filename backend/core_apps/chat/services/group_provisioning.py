"""Only commands provision chat. Reads never change membership or history."""

import uuid
from django.db import transaction
from core_apps.chat.models import Conversation, ConversationParticipant, Message
from core_apps.features.planning_models import HousingGroup


@transaction.atomic
def provision_group(group):
    group = HousingGroup.objects.select_for_update().get(pk=group.pk)
    conversation, _ = Conversation.objects.get_or_create(
        housing_group=group,
        defaults={"kind": "housing_group"},
    )
    conversation = Conversation.objects.select_for_update().get(pk=conversation.pk)
    for member in group.memberships.filter(status="active"):
        participant, created = ConversationParticipant.objects.get_or_create(
            conversation=conversation,
            user=member.user,
            defaults={
                "membership": member,
                "membership_revision": member.joined_revision,
                "membership_period": uuid.uuid4(),
                "visible_from_sequence": conversation.last_sequence + 1,
                "last_read_sequence": conversation.last_sequence,
            },
        )
        if not created and (
            participant.membership_revision != member.joined_revision
            or participant.membership_id != member.pk
        ):
            participant.membership = member
            participant.membership_revision = member.joined_revision
            participant.membership_period = uuid.uuid4()
            participant.visible_from_sequence = conversation.last_sequence + 1
            participant.last_read_sequence = conversation.last_sequence
            participant.unread_count = 0
            participant.unread_reminder_sequence = None
            participant.pinned_at = None
            participant.save()
    return conversation


@transaction.atomic
def roster_changed(group, *, actor, kind, subject=None):
    from .group_events import record_event

    conversation = provision_group(group)
    # group revision is owned by the roster transaction; chat never changes it.
    identity = uuid.uuid5(
        uuid.NAMESPACE_URL, f"sokoun:group:{group.id}:{group.revision}:{kind}"
    )
    if Message.objects.filter(
        conversation=conversation, sender=actor, client_message_id=identity
    ).exists():
        return
    conversation.last_sequence += 1
    conversation.save(update_fields=["last_sequence", "updated_at"])
    message = Message.objects.create(
        conversation=conversation,
        sender=actor,
        kind="system",
        content="",
        sequence=conversation.last_sequence,
        client_message_id=identity,
        system_data={
            "event": kind,
            "actor_name": _name(actor),
            "subject_name": _name(subject) if subject else "",
        },
    )
    record_event(conversation, "message.new", message=message, actor=actor)
    record_event(conversation, "conversation.updated", actor=actor)
    if kind in {"member_left", "member_removed"} and subject:
        record_event(
            conversation,
            "conversation.access_revoked",
            actor=actor,
            data={"user_id": str(subject.id)},
        )


def _name(user):
    return (
        " ".join(x for x in [user.first_name, user.last_name] if x).strip() or "Member"
    )
