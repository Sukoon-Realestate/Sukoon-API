"""Mentions use account identity and UTF-16 spans, never a name-only lookup."""

from difflib import SequenceMatcher
from uuid import UUID
from rest_framework.exceptions import ValidationError
from .group_access import eligible_participants


def mention_span(content, start, end):
    if type(start) is not int or type(end) is not int or not 0 <= start < end:
        raise ValidationError({"mentions": "Choose a member from the mention list."})
    encoded = content.encode("utf-16-le")
    if end * 2 > len(encoded):
        raise ValidationError({"mentions": "Choose a member from the mention list."})
    try:
        return encoded[start * 2 : end * 2].decode("utf-16-le")
    except UnicodeDecodeError:
        raise ValidationError({"mentions": "Choose a member from the mention list."})


def normalize_mentions(content, raw):
    if not isinstance(raw, list) or len(raw) > 20:
        raise ValidationError({"mentions": "A message can mention up to 20 members."})
    result = []
    previous_end = 0
    for item in raw:
        if not isinstance(item, dict):
            raise ValidationError(
                {"mentions": "Choose a member from the mention list."}
            )
        try:
            identity = str(UUID(str(item["user_id"])))
        except (KeyError, ValueError, TypeError):
            raise ValidationError(
                {"mentions": "Choose a member from the mention list."}
            )
        start, end = item.get("start"), item.get("end")
        label = mention_span(content, start, end)
        if start < previous_end or not label.startswith("@") or len(label) < 2:
            raise ValidationError(
                {"mentions": "Choose a member from the mention list."}
            )
        result.append({"user_id": identity, "start": start, "end": end})
        previous_end = end
    return result


def resolve_mentions(conversation, content, mentions):
    from .group_projection import sender_payload

    if not mentions:
        return []
    if conversation.kind == "direct":
        raise ValidationError(
            {"mentions": "Mentions are available in group conversations only."}
        )
    members = {
        str(p.user.id): p
        for p in eligible_participants(conversation).select_related("user")
    }
    resolved = []
    for mention in mentions:
        member = members.get(mention["user_id"])
        if member is None:
            raise ValidationError(
                {"mentions": "A mentioned member is no longer in this conversation."}
            )
        name = sender_payload(member.user)["name"]
        if mention_span(content, mention["start"], mention["end"]) != f"@{name}":
            raise ValidationError(
                {
                    "mentions": "A mentioned member changed. Choose them again from the list."
                }
            )
        resolved.append(
            {
                **mention,
                "name": name,
                "membership_period": str(member.membership_period),
            }
        )
    return resolved


def mentions_payload(message):
    return (
        []
        if message.deleted_at
        else [
            {key: item[key] for key in ("user_id", "name", "start", "end")}
            for item in message.mentions
        ]
    )


def is_mentioned(message, participant):
    return not message.deleted_at and any(
        item["user_id"] == str(participant.user.id)
        and item["membership_period"] == str(participant.membership_period)
        for item in message.mentions
    )


def retained_mentions(message, content):
    # Preserve identities only inside unchanged text blocks when editing.
    old, new = message.content, content
    blocks = SequenceMatcher(a=old, b=new, autojunk=False).get_matching_blocks()
    result = []
    for item in message.mentions:
        for a, b, size in blocks:
            start = len(old[:a].encode("utf-16-le")) // 2
            end = len(old[: a + size].encode("utf-16-le")) // 2
            if start <= item["start"] and item["end"] <= end:
                shift = len(new[:b].encode("utf-16-le")) // 2 - start
                result.append(
                    {**item, "start": item["start"] + shift, "end": item["end"] + shift}
                )
                break
    return result
