"""A5-02: legacy REST/socket sends share the typed text policy and send quota (Sprint 01)."""

import uuid

import pytest
from channels.db import database_sync_to_async
from django.core.cache import cache
from rest_framework.test import APIClient

from core_apps.chat.models import Message
from core_apps.chat.services.message_service import get_or_create_direct_conversation
from .test_consumers import _build_communicator

LIMIT = 4000


@pytest.fixture(autouse=True)
def _fresh_quota():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("bad", [None, 7, ["x"], {"a": 1}, "x" * (LIMIT + 1), "bad\x00text", "   "])
async def test_bad_legacy_socket_input_is_refused_and_the_socket_stays_usable(user, another_user, bad):
    conv = await database_sync_to_async(get_or_create_direct_conversation)(user=user, other_user=another_user)
    socket = _build_communicator(user)
    assert (await socket.connect())[0]

    await socket.send_json_to({"type": "message.send", "conversation_id": str(conv.id), "content": bad})
    reply = await socket.receive_json_from()
    assert "error" in reply

    await socket.send_json_to({"type": "message.send", "conversation_id": str(conv.id), "content": "still works"})
    event = await socket.receive_json_from()
    assert event["type"] == "message.new" and event["payload"]["content"] == "still works"
    assert await database_sync_to_async(Message.objects.filter(conversation=conv).count)() == 1
    await socket.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_legacy_socket_consumes_the_send_quota(user, another_user, settings):
    settings.CHAT_RATE_LIMITS = {"send": 2}
    conv = await database_sync_to_async(get_or_create_direct_conversation)(user=user, other_user=another_user)
    socket = _build_communicator(user)
    assert (await socket.connect())[0]
    for text in ("one", "two"):
        await socket.send_json_to({"type": "message.send", "conversation_id": str(conv.id), "content": text})
        assert (await socket.receive_json_from())["type"] == "message.new"
    await socket.send_json_to({"type": "message.send", "conversation_id": str(conv.id), "content": "three"})
    assert (await socket.receive_json_from())["code"] == "rate_limited"
    assert await database_sync_to_async(Message.objects.filter(conversation=conv).count)() == 2
    await socket.disconnect()


@pytest.mark.django_db
def test_legacy_rest_uses_the_same_text_limit_and_quota(user, another_user, settings):
    conv = get_or_create_direct_conversation(user=user, other_user=another_user)
    client = APIClient()
    client.force_authenticate(user)
    url = f"/api/v1/chat/conversations/{conv.id}/messages/create/"

    assert client.post(url, {"content": "x" * LIMIT}, format="json").status_code == 201
    assert client.post(url, {"content": "x" * (LIMIT + 1)}, format="json").status_code == 400
    settings.CHAT_RATE_LIMITS = {"send": 2}
    assert client.post(url, {"content": "ok"}, format="json").status_code == 429
    assert Message.objects.filter(conversation=conv).count() == 1


@pytest.mark.django_db
def test_rest_and_rich_sends_share_one_quota(user, another_user, settings):
    settings.CHAT_RATE_LIMITS = {"send": 1}
    conv = get_or_create_direct_conversation(user=user, other_user=another_user)
    client = APIClient()
    client.force_authenticate(user)
    url = f"/api/v1/chat/conversations/{conv.id}/messages/create/"
    assert client.post(url, {"content": "legacy"}, format="json").status_code == 201
    rich = client.post(
        url, {"kind": "text", "content": "rich", "client_message_id": str(uuid.uuid4())}, format="json"
    )
    assert rich.status_code == 429
