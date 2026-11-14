"""Sprint 09 transport compatibility, prepared pages and bounded scan evidence."""

from unittest.mock import patch
from uuid import uuid4

import pytest
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.test import APIClient

from core_apps.chat.models import (
    Conversation,
    ConversationParticipant,
    Message,
    MessageEdit,
)
from core_apps.chat.serializers.message import MessageCreateSerializer
from core_apps.chat.services.commands import SendCommand, send
from core_apps.chat.services.forwarding import destination_page
from core_apps.chat.services.message_service import (
    get_or_create_direct_conversation,
    send_message,
)
from core_apps.chat.views.group_history import history_response
from tools.qa.performance import measured

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("bad", [None, False, 12, [], {}, "bad\x00text", "x" * 4001])
def test_shared_typed_text_rejects_invalid_legacy_and_rich(bad):
    with pytest.raises(ValidationError):
        SendCommand.legacy_text(bad)
    with pytest.raises(ValidationError):
        SendCommand.parse({"client_message_id": str(uuid4()), "content": bad})
    assert not MessageCreateSerializer(data={"content": bad}).is_valid()


def test_shared_send_keeps_optional_legacy_identity_and_original_rich_retry(
    user, another_user
):
    chat = get_or_create_direct_conversation(user=user, other_user=another_user)
    first = send_message(conversation=chat, sender=user, content="hello\r\nworld")
    second = send_message(conversation=chat, sender=user, content="hello\r\nworld")
    assert first.client_message_id is None and second.pk != first.pk
    identity = uuid4()
    command = SendCommand.parse(
        {"client_message_id": str(identity), "content": "hello\r\nworld"}
    )
    rich = send(chat, user, command)
    assert rich.content == "hello\nworld"
    assert (
        send_message(
            conversation=chat,
            sender=user,
            content="hello\nworld",
            client_message_id=identity,
        ).pk
        == rich.pk
    )
    assert Message.objects.filter(conversation=chat).count() == 3


@pytest.mark.parametrize("size", [1, 30, 100])
def test_message_page_bounds_edit_expansion_without_losing_legacy_history(
    size, chat_group
):
    _, chat, owner, peer = chat_group
    messages = Message.objects.bulk_create(
        [
            Message(conversation=chat, sender=owner, sequence=i + 1, content="latest")
            for i in range(size)
        ]
    )
    MessageEdit.objects.bulk_create(
        [
            MessageEdit(
                message=message, revision=revision, before="before", after="after"
            )
            for message in messages
            for revision in range(2, 42)
        ]
    )
    chat.last_sequence = size
    chat.save(update_fields=["last_sequence"])
    response, report = measured(
        "sprint09-edit-pages",
        size,
        lambda: history_response(
            chat, peer, {"limit": str(size), "edits_page": "2", "edits_page_size": "5"}
        ).data,
    )
    assert len(response) == size
    assert all(len(row["edit_history"]) == 5 for row in response)
    assert all(row["edit_history"][0]["revision"] == 7 for row in response)
    assert all(
        row["edit_history_page"] == {"page": 2, "page_size": 5, "has_more": True}
        for row in response
    )
    assert report["queries"] <= 22
    assert report["payload_bytes"] < 2200 * size
    legacy = history_response(chat, peer, {"limit": "1"}).data
    assert len(legacy[0]["edit_history"]) == 40 and "edit_history_page" not in legacy[0]


def test_forward_cursor_advances_after_rejected_candidates_and_refreshes_authority(
    user, another_user
):
    source = get_or_create_direct_conversation(user=user, other_user=another_user)
    message = send_message(conversation=source, sender=user, content="Forward me")
    chats = Conversation.objects.bulk_create([Conversation() for _ in range(125)])
    ConversationParticipant.objects.bulk_create(
        [
            ConversationParticipant(
                conversation=chat, user=actor, membership_period=uuid4()
            )
            for chat in chats
            for actor in (user, another_user)
        ]
    )
    rejected = {
        chat.pk for chat in sorted(chats, key=lambda c: c.id, reverse=True)[:100]
    }
    from core_apps.chat.services.group_access import authorize

    inspected = []

    def current(chat, actor, **kwargs):
        if chat.pk != source.pk:
            inspected.append(chat.pk)
            if chat.pk in rejected:
                raise PermissionDenied()
        return authorize(chat, actor, **kwargs)

    with patch("core_apps.chat.services.forwarding.authorize", side_effect=current):
        first = destination_page(source, user, message.id, {})
        assert first["results"] == [] and first["has_more"] and len(inspected) == 100
        inspected.clear()
        second = destination_page(
            source, user, message.id, {"cursor": first["next_cursor"]}
        )
        assert (
            len(second["results"]) == 20 and len(inspected) == 20 and second["has_more"]
        )
        last = destination_page(
            source, user, message.id, {"cursor": second["next_cursor"]}
        )
        assert len(last["results"]) == 5 and not last["has_more"]
    assert len({row["id"] for row in second["results"] + last["results"]}) == 25
    user.security_epoch += 1
    user.save(update_fields=["security_epoch"])
    with pytest.raises(ValidationError):
        destination_page(source, user, message.id, {"cursor": first["next_cursor"]})


def test_inbox_reuses_authority_and_contact_within_one_response(user, another_user):
    from core_apps.chat.serializers.conversation import ConversationSerializer
    from core_apps.chat.services import group_access
    from types import SimpleNamespace

    chat = get_or_create_direct_conversation(user=user, other_user=another_user)
    with patch(
        "core_apps.chat.services.group_access.authorize", wraps=group_access.authorize
    ) as authorize, patch(
        "core_apps.chat.serializers.conversation.counterpart_phone_payload",
        return_value={
            "phone_number": "",
            "masked_phone_number": "",
            "is_phone_revealed": False,
            "phone_notice": "",
        },
    ) as contact:
        value = ConversationSerializer(
            chat, context={"request": SimpleNamespace(user=user)}
        ).data
    assert authorize.call_count == contact.call_count == 1
    assert value["other_participant"]["email"] == ""


def test_invalid_edit_controls_and_non_object_mentions_are_client_errors(chat_group):
    _, chat, owner, _ = chat_group
    with pytest.raises(ValidationError):
        history_response(chat, owner, {"edits_page_size": "21"})
    api = APIClient()
    api.force_authenticate(owner)
    response = api.put(
        f"/api/v1/chat/conversations/{chat.id}/mentions/{uuid4()}/seen/",
        [],
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.requires_postgres
def test_large_read_receipt_projection_uses_one_statement_and_original_times(
    chat_group,
):
    from django.utils import timezone
    from core_apps.chat.models import MessageReadReceipt
    from core_apps.chat.services.group_access import authorize
    from core_apps.chat.services.message_tools import record_reads

    _, chat, owner, peer = chat_group
    Message.objects.bulk_create(
        [
            Message(conversation=chat, sender=owner, sequence=i + 1, content="Unread")
            for i in range(10000)
        ]
    )
    _, participant, _ = authorize(chat, peer)
    stamp = timezone.now()
    _, report = measured(
        "sprint09-read-receipts",
        10000,
        lambda: record_reads(chat, participant, 10000, stamp),
    )
    assert report["queries"] == 1 and report["seconds"] < 5
    assert report["peak_python_bytes"] < 2_000_000
    assert MessageReadReceipt.objects.filter(read_at=stamp).count() == 10000
    record_reads(chat, participant, 10000, timezone.now())
    assert MessageReadReceipt.objects.filter(read_at=stamp).count() == 10000
