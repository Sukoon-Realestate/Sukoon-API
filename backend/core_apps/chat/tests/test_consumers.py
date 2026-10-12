import pytest
import uuid
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken

from core_apps.chat.consumers import ChatConsumer
from core_apps.chat.services.message_service import get_or_create_direct_conversation
from core_apps.common.ws_auth import JWTCookieAuthMiddleware
from core_apps.common.testing import WebsocketCommunicator

_async_get_or_create_conv = database_sync_to_async(get_or_create_direct_conversation)


def _build_communicator(scope_user):
    communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/")
    communicator.scope["user"] = scope_user
    return communicator


@pytest.mark.asyncio
@pytest.mark.django_db
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
async def test_chat_consumer_ack_replay_and_content_conflict(user, another_user):
    from core_apps.chat.models import Message

    conv = await _async_get_or_create_conv(user=user, other_user=another_user)
    client_message_id = uuid.uuid4()
    communicator = _build_communicator(user)
    connected, _ = await communicator.connect()
    assert connected is True

    payload = {
        "type": "message.send",
        "conversation_id": str(conv.id),
        "client_message_id": str(client_message_id),
        "content": "Durable message",
    }
    await communicator.send_json_to(payload)
    first_events = [
        await communicator.receive_json_from(),
        await communicator.receive_json_from(),
    ]
    new_event = next(event for event in first_events if event["type"] == "message.new")
    ack = next(event for event in first_events if event["type"] == "message.ack")

    assert ack["payload"]["id"] == new_event["payload"]["id"]
    assert ack["payload"]["client_message_id"] == str(client_message_id)

    await communicator.send_json_to(payload)
    replay_ack = await communicator.receive_json_from()
    assert replay_ack["type"] == "message.ack"
    assert replay_ack["payload"]["id"] == ack["payload"]["id"]

    await communicator.send_json_to({**payload, "content": "Changed"})
    conflict = await communicator.receive_json_from()
    assert conflict["code"] == "client_message_conflict"
    assert conflict["client_message_id"] == str(client_message_id)

    count = await database_sync_to_async(
        lambda: Message.objects.filter(conversation=conv).count()
    )()
    assert count == 1
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


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_two_authenticated_connections_receive_broadcast_and_rest_persistence(user, another_user):
    """Verifies OBS001: Counterpart delivery across two authenticated WebSocket connections."""
    conv = await _async_get_or_create_conv(user=user, other_user=another_user)

    # 1. Connect user (sender)
    sender_comm = _build_communicator(user)
    assert (await sender_comm.connect())[0] is True

    # 2. Connect another_user (recipient)
    recipient_comm = _build_communicator(another_user)
    assert (await recipient_comm.connect())[0] is True

    # 3. Sender sends message
    client_msg_id = str(uuid.uuid4())
    await sender_comm.send_json_to(
        {
            "type": "message.send",
            "conversation_id": str(conv.id),
            "content": "Broadcast across both authenticated connections",
            "client_message_id": client_msg_id,
        }
    )

    # 4. Sender receives ack and message.new broadcast
    sender_events = [
        await sender_comm.receive_json_from(),
        await sender_comm.receive_json_from(),
    ]
    sender_ack = next(event for event in sender_events if event["type"] == "message.ack")
    sender_new = next(event for event in sender_events if event["type"] == "message.new")
    assert sender_ack["payload"]["client_message_id"] == client_msg_id
    assert sender_new["payload"]["client_message_id"] == client_msg_id

    # 5. Counterpart receives broadcast reliably
    recipient_event = await recipient_comm.receive_json_from()
    assert recipient_event["type"] == "message.new"
    assert recipient_event["payload"]["content"] == "Broadcast across both authenticated connections"
    assert recipient_event["payload"]["client_message_id"] == client_msg_id

    # 6. Verify REST/DB recovery can read the committed message
    @database_sync_to_async
    def _check_db():
        from core_apps.chat.models import Message
        return Message.objects.filter(conversation=conv, client_message_id=client_msg_id).exists()

    assert await _check_db() is True

    await sender_comm.disconnect()
    await recipient_comm.disconnect()

