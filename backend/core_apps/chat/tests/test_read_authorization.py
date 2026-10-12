from unittest.mock import patch

import pytest
from channels.db import database_sync_to_async
from rest_framework.exceptions import PermissionDenied

from core_apps.chat.consumers import ChatConsumer
from core_apps.chat.models import ConversationParticipant
from core_apps.chat.services.message_service import (
    get_or_create_direct_conversation,
    mark_conversation_read,
)
from core_apps.common.testing import WebsocketCommunicator


@pytest.mark.django_db
def test_nonparticipant_cannot_update_read_state_or_schedule_a_receipt(
    user, another_user, superuser, django_capture_on_commit_callbacks
):
    conversation = get_or_create_direct_conversation(user=user, other_user=another_user)
    participants = ConversationParticipant.objects.filter(
        conversation=conversation
    ).order_by("user_id")
    participants.update(unread_count=2)
    before = list(participants.values_list("user_id", "unread_count", "last_read_at"))

    with patch(
        "core_apps.chat.services.message_service._broadcast_read_receipt"
    ) as broadcast:
        with django_capture_on_commit_callbacks(execute=True) as callbacks:
            with pytest.raises(PermissionDenied, match="Not a participant"):
                mark_conversation_read(conversation=conversation, user=superuser)

    assert callbacks == []
    broadcast.assert_not_called()
    assert (
        list(participants.values_list("user_id", "unread_count", "last_read_at"))
        == before
    )


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_nonparticipant_socket_read_is_denied_without_broadcast(
    user, another_user, superuser
):
    conversation = await database_sync_to_async(get_or_create_direct_conversation)(
        user=user, other_user=another_user
    )
    communicators = []
    for actor in (user, another_user, superuser):
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/")
        communicator.scope["user"] = actor
        assert (await communicator.connect())[0] is True
        communicators.append(communicator)
    sender, recipient, outsider = communicators

    try:
        await outsider.send_json_to(
            {"type": "message.read", "conversation_id": str(conversation.id)}
        )
        assert await sender.receive_nothing(timeout=0.1)
        assert await recipient.receive_nothing(timeout=0.1)
        assert await outsider.receive_json_from() == {"error": "Not a participant."}

        # A denied action must not terminate the authenticated connection.
        await outsider.send_json_to({"type": "unknown"})
        assert await outsider.receive_json_from() == {"error": "Unknown message type."}
    finally:
        for communicator in communicators:
            await communicator.disconnect()
