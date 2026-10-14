from django.core import signing
from rest_framework.exceptions import ValidationError
from .group_limits import ChatResync, limits


def encode_cursor(conversation, participant, direction, position, snapshot=None):
    return signing.dumps(
        {
            "c": str(conversation.id),
            "p": str(participant.membership_period),
            "d": direction,
            "n": position,
            "s": snapshot,
        },
        salt="group-chat-v1",
    )


def decode_cursor(value, conversation, participant, direction):
    try:
        data = signing.loads(value, salt="group-chat-v1", max_age=7 * 86400)
        if (
            data["c"] != str(conversation.id)
            or data["p"] != str(participant.membership_period)
            or data["d"] != direction
            or type(data["n"]) is not int
        ):
            raise ValueError()
        return data
    except (signing.BadSignature, ValueError, KeyError, TypeError):
        raise ChatResync()


def page_limit(query):
    if "page" in query or "page_size" in query:
        raise ValidationError(
            "Group chat uses cursor pagination; do not combine page and cursor."
        )
    try:
        count = int(query.get("limit", limits()["history_page_size"]))
    except (ValueError, TypeError):
        raise ValidationError({"limit": "Supply a positive integer."})
    if not 1 <= count <= limits()["history_max_page_size"]:
        raise ValidationError({"limit": "The requested page is too large."})
    return count
