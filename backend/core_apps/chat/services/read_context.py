"""One response's authorized message page; never a command or byte-access grant."""

from dataclasses import dataclass
from django.db.models import Prefetch, prefetch_related_objects
from rest_framework.exceptions import ValidationError
from core_apps.chat.models import MessageEdit
from .group_access import eligible_participants
from .property_sharing import properties_for_messages


@dataclass
class MessagePage:
    authorized: tuple
    roster: list
    properties: dict

    @classmethod
    def prepare(cls, rows, authorized, query=None):
        conversation, _, _ = authorized
        query = query or {}
        controls = {"edits_page", "edits_page_size"} & set(query)
        edits = "edits"
        if controls:
            values = []
            for name, default, maximum in (
                ("edits_page", 1, 10000),
                ("edits_page_size", 5, 20),
            ):
                value = str(query.get(name, default))
                if (
                    not value.isascii()
                    or not value.isdecimal()
                    or len(value) > 6
                    or not 1 <= int(value) <= maximum
                ):
                    raise ValidationError(
                        {name: f"Use an integer from 1 to {maximum}."}
                    )
                values.append(int(value))
            page, size = values
            start = (page - 1) * size
            edits = Prefetch(
                "edits",
                queryset=MessageEdit.objects.order_by("revision")[
                    start : start + size + 1
                ],
                to_attr="page_edits",
            )
        prefetch_related_objects(
            rows,
            "sender__profile",
            "reply_to__sender__profile",
            "attachments",
            "reply_to__attachments__conversation",
            "attachments__conversation",
            edits,
            "reactions",
            "stars",
            "poll__votes",
        )
        for message in rows:
            message.conversation = conversation
            if controls:
                message.edit_page = {
                    "page": page,
                    "page_size": size,
                    "has_more": len(message.page_edits) > size,
                }
                message.page_edits = message.page_edits[:size]
        return cls(
            authorized,
            list(eligible_participants(conversation)),
            properties_for_messages(rows),
        )

    def payload(self, message):
        from .group_projection import message_payload

        _, participant, member = self.authorized
        return message_payload(
            message, participant, member, roster=self.roster, properties=self.properties
        )


@dataclass
class ConversationRead:
    conversation: object
    participant: object
    grant: object
    latest: object
    preferences: dict

    @classmethod
    def prepare(cls, conversation, user):
        from django.db.models import Q
        from .group_access import authorize
        from .conversation_preferences import preferences_payload

        conversation, participant, grant = authorize(conversation, user)
        visible = Q(sequence__gte=participant.visible_from_sequence)
        if participant.visible_from_sequence <= 1:
            visible |= Q(sequence__isnull=True)
        latest = (
            conversation.messages.filter(visible).order_by("-created_at", "-pk").first()
        )
        return cls(
            conversation,
            participant,
            grant,
            latest,
            preferences_payload(conversation, user, participant),
        )
