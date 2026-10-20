"""Group protocol on the existing personal socket; direct handlers stay intact."""

from uuid import UUID
from channels.db import database_sync_to_async
from rest_framework.exceptions import APIException, NotFound, ValidationError


class GroupChatConsumerMixin:
    async def handle_group_request(self, content):
        try:
            result = await database_sync_to_async(self._group_operation)(content)
        except APIException as exc:
            await self.send_json(
                {
                    "type": "chat.error",
                    "payload": {
                        "conversation_id": str(content.get("conversation_id", "")),
                        "client_message_id": content.get("client_message_id"),
                        "operation": content.get("type"),
                        "code": (
                            exc.get_codes()
                            if isinstance(exc.get_codes(), str)
                            else exc.default_code
                        ),
                        "status": exc.status_code,
                        "message": str(exc.detail),
                    },
                }
            )
            return True
        if result is None:
            return False
        if result:
            await self.send_json(result)
        return True

    def _group_operation(self, content):
        from core_apps.chat.models import Conversation
        from .services.group_access import authorize
        from .services.group_projection import message_payload
        from .services.group_rate_limit import enforce_rate

        try:
            identity = UUID(str(content.get("conversation_id")))
        except (ValueError, TypeError):
            if content.get("protocol") in {"group.v1", "chat.v1"}:
                raise ValidationError("Supply a valid conversation identity.")
            return None
        conversation = Conversation.objects.filter(id=identity).first()
        rich_direct = (
            conversation
            and conversation.kind == "direct"
            and content.get("protocol") in {"group.v1", "chat.v1"}
        )
        if not conversation or (
            not rich_direct
            and conversation.kind
            not in {
                "housing_group",
                "company_request",
            }
        ):
            if content.get("protocol") in {"group.v1", "chat.v1"}:
                raise NotFound()
            return None
        kind = content.get("type")
        if kind == "message.send":
            from .services.group_send import send_group_message

            enforce_rate(self.user, "send")
            data = {
                k: v
                for k, v in content.items()
                if k not in {"type", "conversation_id", "protocol"}
            }
            message = send_group_message(conversation, self.user, data)
            _, participant, member = authorize(conversation, self.user)
            return {
                "type": "message.ack",
                "payload": message_payload(message, participant, member),
            }
        if kind == "message.read":
            from .services.group_operations import mark_group_read

            payload = mark_group_read(
                conversation, self.user, content.get("last_read_sequence")
            )
            return {
                "type": "message.read",
                "payload": {**payload, "reader_id": str(self.user.id)},
            }
        if kind in {"typing.started", "typing.stopped"}:
            from .services.group_typing import broadcast_typing

            broadcast_typing(conversation, self.user, started=kind == "typing.started")
            return {}
        raise ValidationError("Unsupported group chat operation.")

    async def chat_group_event(self, event):
        payload = await database_sync_to_async(self._group_event_payload)(
            event["event_id"]
        )
        if payload:
            await self.send_json(payload)

    def _group_event_payload(self, identity):
        from core_apps.chat.models import ChatEvent
        from .services.group_events import event_payload

        event = (
            ChatEvent.objects.select_related("conversation", "message", "actor")
            .filter(id=identity)
            .first()
        )
        return event_payload(event, self.user) if event else None

    async def chat_group_typing(self, event):
        payload = await database_sync_to_async(self._typing_payload)(event)
        if payload:
            await self.send_json(payload)

    def _typing_payload(self, event):
        from .services.group_typing import typing_payload

        return typing_payload(event, self.user)
