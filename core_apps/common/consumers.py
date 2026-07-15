import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)

# * Per-user group name pattern -> lets services broadcast to a specific user later
USER_GROUP_PREFIX = "user"
WS_UNAUTHENTICATED = 4001  # ? custom close code: not authenticated


class EchoConsumer(AsyncWebsocketConsumer):
    """Demo consumer proving the Channels + Redis stack works end-to-end.

    Rejects anonymous connections, joins a per-user group (backed by Redis),
    echoes received JSON, and forwards group broadcasts to the client.
    """

    async def connect(self):
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close(code=WS_UNAUTHENTICATED)
            return

        if not self.channel_layer:
            logger.error("Channel layer not configured")
            await self.close()
            return

        self.group_name = f"{USER_GROUP_PREFIX}_{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json({"type": "connected", "user": str(user.id)})

    async def disconnect(self, code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        # ! Only accept text data with valid JSON
        if not text_data:
            logger.warning("WS received non-text data, closing")
            await self.close()
            return

        try:
            content = json.loads(text_data)
        except json.JSONDecodeError as e:
            logger.error(f"WS JSON decode error: {e}")
            await self.send_json({"type": "error", "message": "Invalid JSON"})
            await self.close()
            return

        await self.receive_json(content)

    async def receive_json(self, content):
        # ? Echo back to confirm the round trip works
        await self.send_json({"type": "echo", "data": content})

    async def broadcast_message(self, event):
        # ? Handler invoked when something does group_send(type="broadcast.message")
        await self.send_json({"type": "broadcast", "data": event["data"]})

    async def send_json(self, content):
        # ? Helper to send JSON; wraps text_data send
        await self.send(text_data=json.dumps(content))
