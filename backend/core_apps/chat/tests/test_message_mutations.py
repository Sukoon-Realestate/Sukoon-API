"""Socket message changes: real authorization, revisions and canonical events."""

import uuid
import pytest
from channels.db import database_sync_to_async
from rest_framework.exceptions import PermissionDenied, ValidationError
from core_apps.chat.consumers import ChatConsumer
from core_apps.chat.models import ChatEvent
from core_apps.chat.services.group_access import authorize
from core_apps.chat.services.group_projection import message_payload
from core_apps.chat.services.group_send import send_group_message
from core_apps.chat.services.group_limits import ChatConflict
from core_apps.chat.services.message_mutations import mutate_message
from core_apps.common.testing import WebsocketCommunicator
from .conftest import message_request
from .test_direct_media import direct_chat  # noqa: F401


def packet(conversation, user, message, **overrides):
    _, participant, _ = authorize(conversation, user)
    return {
        "protocol": "group.v1",
        "type": "message.edit",
        "conversation_id": str(conversation.id),
        "message_id": str(message.id),
        "operation_id": str(uuid.uuid4()),
        "expected_revision": message.revision,
        "membership_period": str(participant.membership_period),
        "content": "Corrected text",
        **overrides,
    }


@pytest.mark.django_db
@pytest.mark.parametrize("chat", ["chat_group", "direct_chat"])
def test_edit_replay_original_send_and_delete_are_canonical(request, chat):
    fixture = request.getfixturevalue(chat)
    conversation, owner, peer = fixture[1:] if chat == "chat_group" else fixture
    original = message_request("Original text")
    message = send_group_message(conversation, owner, original)
    edit = packet(conversation, owner, message)
    changed = mutate_message(conversation, owner, edit)
    assert changed["content"] == "Corrected text"
    assert changed["revision"] == 2 and changed["edited_at"]
    assert mutate_message(conversation, owner, edit)["revision"] == 2
    assert ChatEvent.objects.filter(kind="message.edited", message=message).count() == 1
    assert send_group_message(conversation, owner, original).content == "Corrected text"
    with pytest.raises(ChatConflict):
        mutate_message(conversation, owner, {**edit, "content": "Different operation"})
    message.refresh_from_db()
    delete = packet(conversation, owner, message, type="message.delete")
    delete.pop("content")
    tombstone = mutate_message(conversation, owner, delete)
    assert tombstone["is_deleted"] and tombstone["content"] == ""
    assert tombstone["attachments"] == [] and tombstone["revision"] == 3
    assert mutate_message(conversation, owner, delete)["revision"] == 3
    # A delayed retry of an old edit returns the current tombstone, never resurrects it.
    assert mutate_message(conversation, owner, edit)["is_deleted"]


@pytest.mark.django_db
def test_group_admin_cannot_rewrite_another_members_message(chat_group):
    _, conversation, admin, member = chat_group
    message = send_group_message(conversation, member, message_request())
    with pytest.raises(PermissionDenied):
        mutate_message(conversation, admin, packet(conversation, admin, message))
    _, participant, membership = authorize(conversation, admin)
    actions = message_payload(message, participant, membership)["allowed_actions"]
    assert "delete_message" in actions and "edit_message" not in actions


@pytest.mark.django_db
def test_stale_revision_removed_member_and_invalid_text(chat_group):
    group, conversation, _, member = chat_group
    message = send_group_message(conversation, member, message_request())
    edit = packet(conversation, member, message)
    for content in ("", "a" * 4001, "bad\x00text"):
        with pytest.raises(ValidationError):
            mutate_message(conversation, member, {**edit, "content": content})
    mutate_message(conversation, member, edit)
    with pytest.raises(ChatConflict):
        mutate_message(
            conversation, member, {**edit, "operation_id": str(uuid.uuid4())}
        )
    group.memberships.filter(user=member).update(status="removed")
    with pytest.raises(PermissionDenied):
        mutate_message(conversation, member, edit)


@pytest.mark.django_db
def test_voice_cannot_be_edited_but_image_caption_can(chat_group):
    _, conversation, user, _ = chat_group
    message = send_group_message(conversation, user, message_request())
    message.kind = "voice"
    message.save(update_fields=["kind"])
    with pytest.raises(ValidationError):
        mutate_message(conversation, user, packet(conversation, user, message))
    message.kind = "image"
    message.save(update_fields=["kind"])
    assert (
        mutate_message(
            conversation, user, packet(conversation, user, message, content="")
        )["content"]
        == ""
    )


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("chat", ["chat_group", "direct_chat"])
async def test_edit_and_delete_reach_both_sockets_without_http(request, chat):
    fixture = await database_sync_to_async(request.getfixturevalue)(chat)
    conversation, owner, peer = fixture[1:] if chat == "chat_group" else fixture
    message = await database_sync_to_async(send_group_message)(
        conversation, owner, message_request()
    )
    change = await database_sync_to_async(packet)(conversation, owner, message)
    sockets = []
    try:
        for user in (owner, peer):
            socket = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/")
            socket.scope["user"] = user
            assert (await socket.connect())[0]
            sockets.append(socket)
        for operation, event in (
            ("message.edit", "message.edited"),
            ("message.delete", "message.deleted"),
        ):
            if operation == "message.delete":
                change.update(
                    type=operation, expected_revision=2, operation_id=str(uuid.uuid4())
                )
                change.pop("content")
            await sockets[0].send_json_to(change)
            received = [await sockets[0].receive_json_from() for _ in range(3)]
            ack = next(p for p in received if p["type"] == "message.mutation_ack")
            assert ack["payload"]["operation_id"] == change["operation_id"]
            delivered = [await sockets[1].receive_json_from() for _ in range(2)]
            updated = next(p for p in delivered if p["type"] == event)["payload"]
            assert updated["is_deleted"] == (operation == "message.delete")
            assert updated["revision"] == (3 if operation == "message.delete" else 2)
        await sockets[0].send_json_to(change)
        assert (await sockets[0].receive_json_from())["type"] == "message.mutation_ack"
        assert await sockets[1].receive_nothing(timeout=0.1)
    finally:
        for socket in sockets:
            await socket.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("same_operation", [True, False])
def test_concurrent_edits_are_serialized(chat_group, same_operation):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from django.db import close_old_connections

    _, conversation, user, _ = chat_group
    message = send_group_message(conversation, user, message_request())
    first = packet(conversation, user, message)
    second = (
        first
        if same_operation
        else {**first, "operation_id": str(uuid.uuid4()), "content": "Competing edit"}
    )
    barrier = Barrier(2)

    def apply(change):
        close_old_connections()
        try:
            barrier.wait(timeout=5)
            return mutate_message(conversation, user, change)["revision"]
        except ChatConflict:
            return "conflict"
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(apply, [first, second]))
    assert results == [2, 2] if same_operation else set(results) == {2, "conflict"}
    message.refresh_from_db()
    assert message.revision == 2
    assert ChatEvent.objects.filter(message=message, kind="message.edited").count() == 1
