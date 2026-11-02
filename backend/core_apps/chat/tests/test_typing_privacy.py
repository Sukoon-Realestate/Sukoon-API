from datetime import timedelta

import pytest
from channels.db import database_sync_to_async
from django.core.cache import cache
from django.utils import timezone

from core_apps.chat.consumers import ChatConsumer
from core_apps.chat.models import ConversationParticipant
from core_apps.chat.services.group_typing import typing_payload
from core_apps.common.testing import WebsocketCommunicator
from core_apps.profiles.models import UserSettings

pytestmark = pytest.mark.django_db


def _set_typing(actor, value):
    UserSettings.objects.update_or_create(
        user=actor,
        defaults={"typing_indicator": value},
    )


async def _set_typing_async(actor, value):
    await database_sync_to_async(_set_typing)(actor, value)


async def _clear_typing_cache():
    await database_sync_to_async(cache.clear)()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_typing_respects_sender_and_recipient_privacy(chat_group):
    _, conversation, user, member = chat_group
    sockets = []
    try:
        for actor in (user, member):
            socket = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/")
            socket.scope["user"] = actor
            assert (await socket.connect())[0]
            sockets.append(socket)

        packet = {"type": "typing.started", "conversation_id": str(conversation.id)}

        await _set_typing_async(user, False)
        await sockets[0].send_json_to(packet)
        assert await sockets[1].receive_nothing(timeout=0.15)

        await _clear_typing_cache()
        await _set_typing_async(user, True)
        await _set_typing_async(member, False)
        await sockets[0].send_json_to(packet)
        assert await sockets[1].receive_nothing(timeout=0.15)

        await _clear_typing_cache()
        await _set_typing_async(member, True)
        await sockets[0].send_json_to(packet)
        event = await sockets[1].receive_json_from()
        assert event["type"] == "typing.started"
    finally:
        for socket in sockets:
            await socket.disconnect()


@pytest.mark.django_db
def test_typing_payload_rechecks_privacy_on_delivery(chat_group):
    _, conversation, user, member = chat_group
    participant = ConversationParticipant.objects.get(
        conversation=conversation,
        user=user,
    )
    event = {
        "conversation_id": str(conversation.id),
        "actor_id": str(user.id),
        "membership_period": str(participant.membership_period),
        "started": True,
        "expires_at": (timezone.now() + timedelta(seconds=5)).isoformat(),
    }

    assert typing_payload(event, member) is not None

    _set_typing(member, False)
    assert typing_payload(event, member) is None

    _set_typing(member, True)
    _set_typing(user, False)
    assert typing_payload(event, member) is None
