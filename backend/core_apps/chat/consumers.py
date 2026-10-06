import logging

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncJsonWebsocketConsumer):
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

    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        self.user = user
        self.group_name = f"chat_user_{user.id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        from core_apps.chat.services.message_service import set_user_online_status

        await sync_to_async(set_user_online_status)(str(user.id), True)

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            from core_apps.chat.services.message_service import set_user_online_status

            await sync_to_async(set_user_online_status)(str(self.user.id), False)

    async def receive_json(self, content, **kwargs):
        msg_type = content.get("type")

        if msg_type == "message.send":
            await self._handle_send(content)
        elif msg_type == "message.read":
            await self._handle_read(content)
        else:
            await self.send_json({"error": "Unknown message type."})

    async def _handle_send(self, content):
        from rest_framework.exceptions import ValidationError

        from core_apps.chat.models import Conversation, ConversationParticipant
        from core_apps.chat.services.message_service import send_message

        conversation_id = content.get("conversation_id")
        text = content.get("content", "").strip()

        if not conversation_id or not text:
            await self.send_json({"error": "conversation_id and content are required."})
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
            await sync_to_async(send_message)(
                conversation=conversation,
                sender=self.user,
                content=text,
            )
        except ValidationError:
            await self.send_json({"error": "You cannot message this user."})

    async def _handle_read(self, content):
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

        await sync_to_async(mark_conversation_read)(
            conversation=conversation,
            user=self.user,
        )

    # Group message handlers (called by channel layer from send_message / mark_conversation_read)

    async def chat_message(self, event):
        await self.send_json({"type": "message.new", "payload": event["payload"]})

    async def chat_read(self, event):
        await self.send_json({"type": "message.read", "payload": event["payload"]})
