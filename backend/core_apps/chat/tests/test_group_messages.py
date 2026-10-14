import uuid
import pytest
from django.core.management import call_command
from django.urls import reverse
from rest_framework.exceptions import PermissionDenied, ValidationError
from core_apps.chat.models import Conversation, Message
from core_apps.chat.services.group_access import authorize
from core_apps.chat.services.group_limits import ChatConflict
from core_apps.chat.services.group_operations import (
    delete_group_message,
    mark_group_read,
    set_preference,
)
from core_apps.chat.services.group_projection import message_payload, summary
from core_apps.chat.services.group_provisioning import provision_group, roster_changed
from core_apps.chat.services.group_send import send_group_message
from .conftest import message_request

pytestmark = pytest.mark.django_db


def test_canonical_backfill_never_changes_existing_period(chat_group):
    group, conversation, user, _ = chat_group
    before = summary(conversation, user)
    call_command("backfill_group_chats", verbosity=0)
    assert provision_group(group).id == conversation.id
    assert Conversation.objects.filter(housing_group=group).count() == 1
    assert (
        summary(conversation, user)["membership_period"] == before["membership_period"]
    )


def test_idempotent_unicode_normalization_conflict_and_lost_ack(chat_group, api_client):
    _, conversation, user, _ = chat_group
    payload = message_request("أهلا\r\n  👨‍👩‍👧  ")
    first = send_group_message(conversation, user, payload)
    assert first.content == "أهلا\n  👨‍👩‍👧  "
    assert send_group_message(conversation, user, payload).id == first.id
    with pytest.raises(ChatConflict):
        send_group_message(conversation, user, {**payload, "content": "Changed"})
    api_client.force_authenticate(user)
    base = reverse("message-list", kwargs={"id": conversation.id}).removesuffix(
        "messages/"
    )
    response = api_client.get(
        f"{base}messages/by-client-id/{payload['client_message_id']}/"
    )
    assert response.status_code == 200
    assert response.json()["data"]["id"] == str(first.id)
    assert Message.objects.filter(conversation=conversation).count() == 1


@pytest.mark.parametrize(
    "condition",
    ["outsider", "left", "removed", "unverified", "disabled", "unknown_state"],
)
def test_current_access_fails_closed(chat_group, superuser, settings, condition):
    group, conversation, user, _ = chat_group
    if condition == "outsider":
        user = superuser
        user.is_verified = True
        user.save()
    elif condition in {"left", "removed"}:
        group.memberships.filter(user=user).update(status=condition)
    elif condition == "unverified":
        type(user).objects.filter(pk=user.pk).update(is_verified=False)
    elif condition == "disabled":
        settings.PLANNING_ENABLED_SERVICES = []
    else:
        group.status = "future_state"
        group.save()
    with pytest.raises(PermissionDenied):
        summary(conversation, user)
    with pytest.raises(PermissionDenied):
        send_group_message(conversation, user, message_request())


def test_rejoin_hides_old_history_reply_media_and_preview(chat_group):
    group, conversation, user, member = chat_group
    old = send_group_message(conversation, user, message_request("Hidden"))
    reply = send_group_message(
        conversation, user, message_request("Reply", reply_to_message_id=str(old.id))
    )
    group.memberships.filter(user=member).update(status="left")
    group.revision += 1
    group.save()
    roster_changed(group, actor=member, subject=member, kind="member_left")
    group.memberships.filter(user=member).update(
        status="active", joined_revision=group.revision + 1
    )
    provision_group(group)
    conversation.refresh_from_db()
    fresh = summary(conversation, member)
    assert fresh["last_message"] is None and fresh["unread_count"] == 0
    with pytest.raises(ValidationError):
        send_group_message(
            conversation, member, message_request(reply_to_message_id=str(reply.id))
        )
    # An older member can reply to old history; the new member sees only unavailable.
    new_reply = send_group_message(
        conversation, user, message_request("New", reply_to_message_id=str(old.id))
    )
    _, participant, membership = authorize(conversation, member)
    projected = message_payload(new_reply, participant, membership)
    assert projected["reply_to"] == {"id": str(old.id), "availability": "unavailable"}
    assert "Hidden" not in str(projected)


def test_monotonic_reads_tombstone_permissions_and_muting(chat_group):
    _, conversation, admin, member = chat_group
    first = send_group_message(conversation, admin, message_request("One"))
    second = send_group_message(conversation, admin, message_request("Two"))
    assert summary(conversation, member)["unread_count"] == 2
    assert set_preference(conversation, member, True)["unread_count"] == 2
    mark_group_read(conversation, member, second.sequence)
    assert (
        mark_group_read(conversation, member, first.sequence)["last_read_sequence"]
        == second.sequence
    )
    with pytest.raises(ValidationError):
        mark_group_read(conversation, member, 999)
    _, participant, membership = authorize(conversation, admin)
    assert message_payload(first, participant, membership)["read_by_count"] == 1
    with pytest.raises(PermissionDenied):
        delete_group_message(conversation, member, first.id)
    deleted = delete_group_message(conversation, admin, first.id)
    assert (
        deleted["is_deleted"]
        and deleted["content"] == ""
        and deleted["attachments"] == []
    )
    assert delete_group_message(conversation, admin, first.id)["id"] == deleted["id"]


def test_group_inbox_opt_in_and_direct_identity(chat_group, api_client):
    from core_apps.chat.services.message_service import (
        get_or_create_direct_conversation,
    )

    _, conversation, user, member = chat_group
    direct = get_or_create_direct_conversation(user=user, other_user=member)
    assert direct.id != conversation.id and direct.kind == "direct"
    api_client.force_authenticate(user)
    assert len(api_client.get(reverse("conversation-list")).json()["data"]) == 1
    data = api_client.get(
        reverse("conversation-list"), {"include_groups": "true"}
    ).json()["data"]
    assert {x["conversation_type"] for x in data} == {"direct", "housing_group"}


def test_cursor_snapshot_reconnect_and_explicit_resync(chat_group, api_client):
    _, conversation, user, member = chat_group
    for index in range(5):
        send_group_message(conversation, user, message_request(str(index)))
    api_client.force_authenticate(member)
    url = reverse("message-list", kwargs={"id": conversation.id})
    first = api_client.get(url, {"limit": 2})
    cursor = first["X-Chat-Older-Cursor"]
    event_cursor = first["X-Chat-Event-Cursor"]
    send_group_message(conversation, user, message_request("After snapshot"))
    second = api_client.get(url, {"limit": 3, "older_cursor": cursor})
    assert [m["sequence"] for m in second.json()["data"] + first.json()["data"]] == [
        1,
        2,
        3,
        4,
        5,
    ]
    delete_group_message(conversation, user, conversation.messages.get(sequence=1).id)
    events = api_client.get(
        url.removesuffix("messages/") + "events/", {"after_cursor": event_cursor}
    )
    assert "message.deleted" in [e["type"] for e in events.json()["data"]]
    bad = api_client.get(url, {"older_cursor": "corrupt"})
    assert bad.status_code == 409 and bad.json()["data"] is None
    assert bad["X-App-Error-Code"] == "chat_resync_required"
    assert api_client.get(url, {"page": 1}).status_code == 400
