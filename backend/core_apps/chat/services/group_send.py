"""Compatible rich-send entry point; the domain command owns creation."""

from .commands import SendCommand, normalize_request as normalize_request
from .commands import send


def send_group_message(conversation, sender, data):
    return send(conversation, sender, SendCommand.parse(data))
