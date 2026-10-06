import pytest
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import AnonymousUser

from core_apps.common.consumers import WS_UNAUTHENTICATED, EchoConsumer


def _build_communicator(scope_user):
    # ? Drive the consumer directly so we exercise its logic, not the middleware
    communicator = WebsocketCommunicator(EchoConsumer.as_asgi(), "/ws/echo/")
    communicator.scope["user"] = scope_user
    return communicator


@pytest.mark.asyncio
async def test_unauthenticated_connection_is_rejected():
    communicator = _build_communicator(AnonymousUser())

    connected, code = await communicator.connect()

    assert connected is False
    assert code == WS_UNAUTHENTICATED


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_authenticated_connection_echoes(user):
    communicator = _build_communicator(user)

    connected, _ = await communicator.connect()
    assert connected is True

    greeting = await communicator.receive_json_from()
    assert greeting == {"type": "connected", "user": str(user.id)}

    await communicator.send_json_to({"ping": 1})
    echoed = await communicator.receive_json_from()
    assert echoed == {"type": "echo", "data": {"ping": 1}}

    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_group_broadcast_reaches_user(user):
    communicator = _build_communicator(user)

    await communicator.connect()
    await communicator.receive_json_from()  # ? drain the initial "connected" frame

    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f"user_{user.id}",
        {"type": "broadcast.message", "data": {"hello": "world"}},
    )

    message = await communicator.receive_json_from()
    assert message == {"type": "broadcast", "data": {"hello": "world"}}

    await communicator.disconnect()
