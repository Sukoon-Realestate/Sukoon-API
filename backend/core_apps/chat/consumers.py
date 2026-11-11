import asyncio
import logging
from uuid import UUID

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from .group_consumer import GroupChatConsumerMixin

logger = logging.getLogger(__name__)


class ChatConsumer(GroupChatConsumerMixin, AsyncJsonWebsocketConsumer):
    """
    Personal websocket channel for a single authenticated user.

    All incoming messages from any conversation are pushed to this consumer
    via the user's personal group chat_user_<id>. The client routes events
    by conversation_id.

    Incoming event types (from client):
        {"type": "message.send", "conversation_id": "<uuid>", "content": "<text>"}
        {"type": "message.read", "conversation_id": "<uuid>"}

    Outgoing event types (to client):
        {"type": "message.new", "payload": <MessageSerializer data>}
        {"type": "message.read", "payload": {"conversation_id": "<uuid>", "reader_id": "<uuid>"}}
    """

    async def __call__(self, scope, receive, send):
        try:
            return await super().__call__(scope, receive, send)
        finally:
            # ASGI cancellation/worker shutdown may bypass disconnect entirely.
            await self._release_presence()

    async def _release_presence(self):
        if hasattr(self, "presence_task"):
            self.presence_task.cancel()
            try:
                await self.presence_task
            except asyncio.CancelledError:
                pass
        if getattr(self, "presence_registered", False):
            from core_apps.chat.services.presence import set_user_online_status
            await database_sync_to_async(set_user_online_status)(str(self.user.id), False, self.channel_name)
            self.presence_registered = False

    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        self.user = user
        self.group_name = f"chat_user_{user.id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        sid = (self.scope.get("auth_claims") or {}).get("session_id")
        if sid:
            self.session_group = f"chat_session_{UUID(str(sid))}"
            await self.channel_layer.group_add(self.session_group, self.channel_name)
        await self.accept()

        from core_apps.chat.services.message_service import set_user_online_status

        await database_sync_to_async(set_user_online_status)(str(user.id), True, self.channel_name)
        self.presence_registered = True
        self.presence_task = asyncio.create_task(self._renew_presence())

    async def _renew_presence(self):
        from core_apps.chat.services.presence import ONLINE_TTL_SECONDS, set_user_online_status
        from core_apps.common.ws_auth import _get_user
        from time import time
        while True:
            await asyncio.sleep(ONLINE_TTL_SECONDS / 3)
            claims = self.scope.get("auth_claims")
            if claims:
                current = await _get_user(claims["user_id"], claims)
                if not current.is_authenticated or claims.get("exp", 0) <= time():
                    await database_sync_to_async(set_user_online_status)(str(self.user.id), False, self.channel_name)
                    await self.close(code=4401)
                    return
            await database_sync_to_async(set_user_online_status)(str(self.user.id), True, self.channel_name)

    async def disconnect(self, close_code):
        await self._release_presence()
        if hasattr(self, "session_group"):
            await self.channel_layer.group_discard(
                self.session_group, self.channel_name
            )
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def session_revoked(self, event):
        await self._release_presence()
        await self.close(code=4401)

    async def receive_json(self, content, **kwargs):
        if not isinstance(content, dict):
            await self.send_json({"error": "Supply a message object."})
            return
        if await self.handle_group_request(content):
            return
        msg_type = content.get("type")

        if msg_type == "message.send":
            await self._handle_send(content)
        elif msg_type == "message.read":
            await self._handle_read(content)
        else:
            await self.send_json({"error": "Unknown message type."})

    async def _handle_send(self, content):
        from rest_framework.exceptions import PermissionDenied, ValidationError

        from core_apps.chat.models import Conversation, ConversationParticipant
        from core_apps.chat.services.message_service import (
            ChatMessageConflict,
            send_message,
        )

        from rest_framework.exceptions import Throttled

        from core_apps.chat.services.group_limits import validate_text
        from core_apps.chat.services.group_rate_limit import enforce_rate

        conversation_id = content.get("conversation_id")
        raw = content.get("content")
        client_message_id = content.get("client_message_id")

        if not conversation_id or raw is None or (isinstance(raw, str) and not raw.strip()):
            await self.send_json({"error": "conversation_id and content are required."})
            return
        # A5-02: the same typed text policy and send quota as REST and rich sends.
        # Invalid frames get a stable error and the socket stays open.
        try:
            text = validate_text(raw).strip()
        except ValidationError:
            await self.send_json(
                {"error": "Message text is invalid or too long.", "code": "invalid_message"}
            )
            return
        try:
            await sync_to_async(enforce_rate)(self.user, "send")
        except Throttled:
            await self.send_json(
                {"error": "Too many messages. Try again shortly.", "code": "rate_limited"}
            )
            return
        if client_message_id:
            try:
                client_message_id = UUID(str(client_message_id))
            except (TypeError, ValueError):
                await self.send_json(
                    {
                        "error": "client_message_id must be a valid UUID.",
                        "code": "invalid_client_message_id",
                    }
                )
                return

        try:
            conversation = await sync_to_async(
                lambda: Conversation.objects.get(id=conversation_id)
            )()
        except Exception:
            await self.send_json({"error": "Conversation not found."})
            return

        # Participant guard
        is_participant = await sync_to_async(
            lambda: ConversationParticipant.objects.filter(
                conversation=conversation, user=self.user
            ).exists()
        )()
        if not is_participant:
            await self.send_json({"error": "Not a participant."})
            return

        try:
            message = await sync_to_async(send_message)(
                conversation=conversation,
                sender=self.user,
                content=text,
                client_message_id=client_message_id,
            )
            if client_message_id:
                from core_apps.chat.serializers.message import MessageSerializer

                payload = await sync_to_async(
                    lambda: dict(MessageSerializer(message).data)
                )()
                await self.send_json({"type": "message.ack", "payload": payload})
        except (ValidationError, PermissionDenied):
            await self.send_json({"error": "You cannot message this user."})
        except ChatMessageConflict as exc:
            await self.send_json(
                {
                    "error": str(exc.detail),
                    "code": "client_message_conflict",
                    "client_message_id": str(client_message_id),
                }
            )

    async def _handle_read(self, content):
        from rest_framework.exceptions import PermissionDenied

        from core_apps.chat.models import Conversation
        from core_apps.chat.services.message_service import mark_conversation_read

        conversation_id = content.get("conversation_id")
        if not conversation_id:
            return

        try:
            conversation = await sync_to_async(
                lambda: Conversation.objects.get(id=conversation_id)
            )()
        except Exception:
            return

        try:
            await sync_to_async(mark_conversation_read)(
                conversation=conversation,
                user=self.user,
            )
        except PermissionDenied:
            await self.send_json({"error": "Not a participant."})

    # Group message handlers (called by channel layer from send_message / mark_conversation_read)

    async def chat_message(self, event):
        await self.send_json({"type": "message.new", "payload": event["payload"]})

    async def chat_read(self, event):
        await self.send_json({"type": "message.read", "payload": event["payload"]})
