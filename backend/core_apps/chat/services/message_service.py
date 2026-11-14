"""Stable public imports for message service.

Implementation modules separate domain responsibilities without changing routes.
"""

from .message_service_parts.get_or_create_direct_conversation import (
    logger,
    ChatMessageConflict,
    direct_message_blocked,
    get_or_create_direct_conversation,
)
from .message_service_parts.send_message import (
    send_message,
    _broadcast_read_receipt,
    mark_conversation_read,
)

from .presence import (
    ONLINE_KEY_PREFIX,
    ONLINE_TTL_SECONDS,
    set_user_online_status,
    is_user_online,
)

__all__ = [
    "logger",
    "ONLINE_KEY_PREFIX",
    "ONLINE_TTL_SECONDS",
    "ChatMessageConflict",
    "set_user_online_status",
    "is_user_online",
    "direct_message_blocked",
    "get_or_create_direct_conversation",
    "send_message",
    "_broadcast_read_receipt",
    "mark_conversation_read",
]
