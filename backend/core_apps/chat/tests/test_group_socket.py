import uuid
import pytest
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from core_apps.chat.consumers import ChatConsumer
from core_apps.chat.models import ChatEvent, Message
from core_apps.common.testing import WebsocketCommunicator
from .conftest import message_request

pytestmark = [pytest.mark.asyncio, pytest.mark.django_db(transaction=True)]


async def test_group_socket_ack_rest_replay_and_revocation(chat_group):
    from rest_framework.test import APIClient
    from django.urls import reverse

    group, conversation, user, member = chat_group
    socket = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/")
    socket.scope["user"] = user
    assert (await socket.connect())[0]
    body = message_request("Group socket")
    packet = {
        "type": "message.send",
        "protocol": "group.v1",
        "conversation_id": str(conversation.id),
        **body,
    }
    await socket.send_json_to(packet)
    ack = await socket.receive_json_from()
    assert ack["type"] == "message.ack" and ack["payload"]["sequence"] == 1
    assert ack["payload"]["sender"]["id"] == str(user.id)
    assert "email" not in ack["payload"]["sender"]

    @database_sync_to_async
    def replay():
        client = APIClient()
        client.force_authenticate(user)
        response = client.post(
            reverse("message-create", kwargs={"id": conversation.id}),
            body,
            format="json",
        )
        assert response.json()["data"]["id"] == ack["payload"]["id"]
        assert Message.objects.filter(conversation=conversation).count() == 1
        group.memberships.filter(user=user).update(status="removed")
        return str(ChatEvent.objects.get(conversation=conversation).id)

    event_id = await replay()
    await get_channel_layer().group_send(
        f"chat_user_{user.id}", {"type": "chat.group_event", "event_id": event_id}
    )
    assert await socket.receive_nothing(timeout=0.1)
    await socket.send_json_to({**packet, "client_message_id": str(uuid.uuid4())})
    error = await socket.receive_json_from()
    assert error["type"] == "chat.error" and error["payload"]["status"] == 403
    assert error["payload"]["conversation_id"] == str(conversation.id)
    await socket.disconnect()


async def test_read_only_open_and_typing_are_not_persisted_messages(chat_group):
    _, conversation, user, member = chat_group
    sockets = []
    for actor in (user, member):
        socket = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/")
        socket.scope["user"] = actor
        await socket.connect()
        sockets.append(socket)
    await sockets[0].send_json_to(
        {"type": "typing.started", "conversation_id": str(conversation.id)}
    )
    event = await sockets[1].receive_json_from()
    assert event["type"] == "typing.started" and "expires_at" in event["payload"]
    assert (
        await database_sync_to_async(
            lambda: Message.objects.filter(conversation=conversation).count()
        )()
        == 0
    )
    for socket in sockets:
        await socket.disconnect()
