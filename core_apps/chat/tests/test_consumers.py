import pytest
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken

from core_apps.chat.consumers import ChatConsumer
from core_apps.chat.services.message_service import get_or_create_direct_conversation
from core_apps.common.ws_auth import JWTCookieAuthMiddleware

_async_get_or_create_conv = database_sync_to_async(get_or_create_direct_conversation)


def _build_communicator(scope_user):
    communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/")
    communicator.scope["user"] = scope_user
    return communicator


@pytest.mark.asyncio
async def test_unauthenticated_chat_connection_rejected():
    communicator = _build_communicator(AnonymousUser())
    connected, code = await communicator.connect()
    assert connected is False
    assert code == 4401


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_authenticated_chat_connects_and_receives_broadcast(user):
    communicator = _build_communicator(user)
    connected, _ = await communicator.connect()
    assert connected is True

    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f"chat_user_{user.id}",
        {"type": "chat.message", "payload": {"id": "123", "content": "Hello via WS!"}},
    )

    event = await communicator.receive_json_from()
    assert event["type"] == "message.new"
    assert event["payload"]["content"] == "Hello via WS!"

    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_chat_consumer_send_message(user, another_user):
    conv = await _async_get_or_create_conv(user=user, other_user=another_user)

    communicator = _build_communicator(user)
    connected, _ = await communicator.connect()
    assert connected is True

    # Send message from user
    await communicator.send_json_to(
        {
            "type": "message.send",
            "conversation_id": str(conv.id),
            "content": "Hello over websocket!",
        }
    )

    # The consumer will receive the group broadcast sent to its own chat_user_<id> group
    event = await communicator.receive_json_from()
    assert event["type"] == "message.new"
    assert event["payload"]["content"] == "Hello over websocket!"

    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_chat_consumer_non_participant_rejected(user, another_user, superuser):
    conv = await _async_get_or_create_conv(user=user, other_user=another_user)

    communicator = _build_communicator(superuser)
    connected, _ = await communicator.connect()
    assert connected is True

    await communicator.send_json_to(
        {
            "type": "message.send",
            "conversation_id": str(conv.id),
            "content": "Spying!",
        }
    )

    event = await communicator.receive_json_from()
    assert event["error"] == "Not a participant."

    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_chat_consumer_read_receipt(user, another_user):
    conv = await _async_get_or_create_conv(user=user, other_user=another_user)

    # Connect sender
    sender_comm = _build_communicator(user)
    await sender_comm.connect()

    # Connect recipient
    recipient_comm = _build_communicator(another_user)
    await recipient_comm.connect()

    # Recipient marks read
    await recipient_comm.send_json_to(
        {
            "type": "message.read",
            "conversation_id": str(conv.id),
        }
    )

    # Sender receives read receipt
    event = await sender_comm.receive_json_from()
    assert event["type"] == "message.read"
    assert event["payload"]["conversation_id"] == str(conv.id)
    assert event["payload"]["reader_id"] == str(another_user.id)

    await sender_comm.disconnect()
    await recipient_comm.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_jwt_auth_middleware_query_string_token(user):
    token = str(AccessToken.for_user(user))
    app = JWTCookieAuthMiddleware(ChatConsumer.as_asgi())
    communicator = WebsocketCommunicator(app, f"/ws/chat/?token={token}")

    connected, _ = await communicator.connect()
    assert connected is True

    await communicator.disconnect()
