import importlib
import uuid
import pytest
from django.apps import apps
from django.db import connection
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError, PermissionDenied
from core_apps.chat.models import MessageMention, ChatEvent, ChatNotificationDelivery
from core_apps.chat.services.group_access import authorize
from core_apps.chat.services.group_events import event_payload
from core_apps.chat.services.group_send import send_group_message
from core_apps.chat.services.group_outbox import _notify
from core_apps.chat.services.group_operations import mark_group_read, delete_group_message
from core_apps.chat.services.group_provisioning import provision_group
from core_apps.chat.services.group_limits import ChatConflict
from core_apps.chat.services.mention_navigation import navigation_payload, see_mention
from core_apps.chat.services.mentions import is_mentioned, mentions_payload
from core_apps.chat.services.message_mutations import mutate_message
from core_apps.features.planning_models import GroupMembership
from .conftest import message_request
from .test_reactions_mentions import mention_request
from .test_direct_media import direct_chat  # noqa: F401


def all_request():
    return message_request("😀 @all أهلاً بالجميع", mentions=[{"kind": "all", "start": 3, "end": 7}])


@pytest.mark.django_db
def test_all_notifies_every_current_member_once_even_when_muted(chat_group, superuser):
    group, conversation, owner, peer = chat_group
    superuser.is_verified = True
    superuser.save(update_fields=["is_verified"])
    GroupMembership.objects.create(group=group, user=superuser)
    provision_group(group)
    conversation.participant_set.exclude(user=owner).update(is_muted=True)
    body = all_request()
    message = send_group_message(conversation, owner, body)
    assert send_group_message(conversation, owner, body).pk == message.pk
    assert message.mention_receipts.count() == 2
    assert mentions_payload(message) == [{"kind": "all", "name": "all", "start": 3, "end": 7}]
    event = ChatEvent.objects.get(message=message, kind="message.new")
    for person in [peer, superuser]:
        _notify(event, person)
        _notify(event, person)
        delivery = ChatNotificationDelivery.objects.get(event=event, user=person)
        assert delivery.notification.data["is_mention"] == "true"
        assert delivery.notification.data["message_id"] == str(message.id)
    assert ChatNotificationDelivery.objects.filter(event=event).count() == 2


@pytest.mark.django_db
def test_five_mentions_survive_normal_chat_read_then_advance_exactly_one(chat_group):
    _, conversation, owner, peer = chat_group
    messages = [send_group_message(conversation, owner, mention_request(peer)) for _ in range(5)]
    mark_group_read(conversation, peer, messages[-1].sequence)
    _, participant, _ = authorize(conversation, peer)
    assert navigation_payload(conversation, participant)["count"] == 5
    for index, message in enumerate(messages):
        pending = navigation_payload(conversation, participant)
        assert pending["next_message_id"] == str(message.id)
        seen = see_mention(conversation, peer, message.id, participant.membership_period)
        assert seen["count"] == 4 - index
        assert see_mention(conversation, peer, message.id, participant.membership_period) == seen
        event = ChatEvent.objects.filter(conversation=conversation, kind="mentions.updated").latest("pkid")
        assert event_payload(event, owner) is None
        assert event_payload(event, peer)["type"] == "mentions.updated"
    assert navigation_payload(conversation, participant)["next_message_id"] is None


@pytest.mark.django_db
def test_all_uses_send_time_membership_and_rejoin_never_inherits_old_queue(chat_group, superuser):
    group, conversation, owner, peer = chat_group
    message = send_group_message(conversation, owner, all_request())
    _, old, _ = authorize(conversation, peer)
    group.memberships.filter(user=peer).update(status="removed")
    with pytest.raises(PermissionDenied):
        see_mention(conversation, peer, message.id, old.membership_period)
    group.memberships.filter(user=peer).update(status="active", joined_revision=2)
    superuser.is_verified = True
    superuser.save(update_fields=["is_verified"])
    GroupMembership.objects.create(group=group, user=superuser)
    provision_group(group)
    for person in [peer, superuser]:
        _, participant, _ = authorize(conversation, person)
        assert not is_mentioned(message, participant)
        assert navigation_payload(conversation, participant)["count"] == 0
    with pytest.raises(ChatConflict):
        see_mention(conversation, peer, message.id, old.membership_period)


@pytest.mark.django_db
def test_removed_mentions_and_deleted_messages_leave_the_queue(chat_group):
    _, conversation, owner, peer = chat_group
    message = send_group_message(conversation, owner, all_request())
    _, participant, _ = authorize(conversation, peer)
    _, author, _ = authorize(conversation, owner)
    mutate_message(
        conversation,
        owner,
        {
            "type": "message.edit",
            "message_id": str(message.id),
            "operation_id": str(uuid.uuid4()),
            "membership_period": str(author.membership_period),
            "expected_revision": 1,
            "content": "Changed without a mention",
        },
    )
    assert navigation_payload(conversation, participant)["count"] == 0
    newer = send_group_message(conversation, owner, mention_request(peer))
    delete_group_message(conversation, owner, newer.id)
    assert navigation_payload(conversation, participant)["count"] == 0


@pytest.mark.django_db
def test_mention_api_is_authorized_period_fenced_and_does_not_consume_other_users(chat_group, superuser):
    _, conversation, owner, peer = chat_group
    message = send_group_message(conversation, owner, all_request())
    _, participant, _ = authorize(conversation, peer)
    client = APIClient()
    url = f"/api/v1/chat/conversations/{conversation.id}/mentions/"
    assert client.get(url).status_code == 401
    client.force_authenticate(superuser)
    assert client.get(url).status_code == 403
    client.force_authenticate(owner)
    assert client.get(url).json()["data"]["count"] == 0
    client.force_authenticate(peer)
    assert client.get(url).json()["data"]["count"] == 1
    seen_url = f"{url}{message.id}/seen/"
    assert client.put(seen_url, {"membership_period": str(uuid.uuid4())}, format="json").status_code == 409
    result = client.put(seen_url, {"membership_period": str(participant.membership_period)}, format="json")
    assert result.status_code == 200
    assert result.json()["data"]["count"] == 0
    assert result["Cache-Control"] == "private, no-store"


@pytest.mark.django_db
def test_direct_chat_and_forged_all_spans_do_not_broadcast(direct_chat, chat_group):
    conversation, owner, _ = direct_chat
    with pytest.raises(ValidationError):
        send_group_message(conversation, owner, all_request())
    _, conversation, owner, peer = chat_group
    with pytest.raises(ValidationError):
        send_group_message(conversation, owner, {**all_request(), "content": "😀 @bob hello"})
    ordinary = send_group_message(conversation, owner, message_request("mail@all.com"))
    assert not ordinary.mention_receipts.exists()


@pytest.mark.django_db
def test_existing_mentions_backfill_keeps_read_and_unread_progress(chat_group):
    _, conversation, owner, peer = chat_group
    seen = send_group_message(conversation, owner, mention_request(peer))
    mark_group_read(conversation, peer, seen.sequence)
    unseen = send_group_message(conversation, owner, mention_request(peer))
    MessageMention.objects.all().delete()
    migration = importlib.import_module("core_apps.chat.migrations.0023_messagemention_and_more")
    with connection.schema_editor() as editor:
        migration.import_existing_mentions(apps, editor)
        migration.import_existing_mentions(apps, editor)
    assert MessageMention.objects.count() == 2
    assert MessageMention.objects.get(message=seen).seen_at is not None
    assert MessageMention.objects.get(message=unseen).seen_at is None
