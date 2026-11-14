"""Durable event names are protocol contracts, distinct from client commands."""

MESSAGE_NEW = "message.new"
MESSAGE_EDITED = "message.edited"
MESSAGE_DELETED = "message.deleted"
MESSAGE_READ = "message.read"
CONVERSATION_UPDATED = "conversation.updated"
MODERATED_MESSAGE_EVENTS = frozenset({MESSAGE_NEW, MESSAGE_EDITED})
