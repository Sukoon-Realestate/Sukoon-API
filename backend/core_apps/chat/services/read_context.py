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
    roster: list | None = None
    policy: dict | None = None

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


class ConversationPage:
    """Prepared current direct inbox facts; historical/group paths stay explicit."""

    @classmethod
    def prepare(cls, conversations, user):
        from collections import defaultdict
        from django.db.models import (
            F,
            Q,
            OuterRef,
            Subquery,
            ExpressionWrapper,
            BigIntegerField,
        )
        from django.utils import timezone
        from core_apps.chat.models import (
            Message,
            Conversation,
            ConversationWorkspace,
            ChatList,
            ChatPresenceLease,
            ConversationParticipant,
        )
        from core_apps.chat.moderation.policy import projection
        from .direct_access import authorize_page
        from .inbox_preferences import inbox_payload
        from .group_notification_preferences import payload as notification_payload

        grants = authorize_page(conversations, user)
        ids = list(grants)
        if not ids:
            return {}, {}
        viewer = ConversationParticipant.objects.filter(
            conversation_id=OuterRef("pk"), user=user
        )
        visible_latest = (
            Message.objects.filter(conversation_id=OuterRef("pk"))
            .annotate(
                page_boundary=ExpressionWrapper(
                    OuterRef("page_visible_from"), output_field=BigIntegerField()
                ),
            )
            .filter(
                Q(sequence__gte=F("page_boundary"))
                | Q(sequence__isnull=True, page_boundary__lte=1)
            )
            .order_by("-created_at", "-pkid")
        )
        latest_ids = (
            Conversation.objects.filter(pk__in=ids)
            .annotate(
                page_visible_from=Subquery(viewer.values("visible_from_sequence")[:1]),
            )
            .annotate(page_latest=Subquery(visible_latest.values("pkid")[:1]))
            .values("page_latest")
        )
        # One index-backed latest lookup per selected conversation, then only
        # those message rows. Do not rank/materialize each thread's full history.
        latest = Message.objects.filter(pkid__in=Subquery(latest_ids))
        latest = {message.conversation_id: message for message in latest}
        workspaces = defaultdict(list)
        for identity, workspace in ConversationWorkspace.objects.filter(
            user=user, conversation_id__in=ids
        ).values_list("conversation_id", "workspace"):
            workspaces[identity].append(workspace)
        lists = defaultdict(list)
        for identity, list_id in ChatList.objects.filter(
            user=user, conversations__in=ids
        ).values_list("conversations", "id"):
            lists[identity].append(str(list_id))
        people = {row.user_id for grant in grants.values() for row in grant["roster"]}
        online = set(
            ChatPresenceLease.objects.filter(
                user_id__in=people, expires_at__gt=timezone.now()
            ).values_list("user_id", flat=True)
        )
        policy = projection(next(iter(grants.values()))["authorized"][0], user)
        prepared = {}
        for original in conversations:
            if original.pk not in grants:
                continue
            facts = grants[original.pk]
            conversation, participant, grant = facts["authorized"]
            roster = facts["roster"]
            # Public participant and unread fields use these exact current rows.
            original._prefetched_objects_cache = {
                **getattr(original, "_prefetched_objects_cache", {}),
                "participants": [row.user for row in roster],
                "participant_set": roster,
            }
            workspace = workspaces[original.pk]
            preferences = {
                "workspace": workspace[0] if len(workspace) == 1 else "",
                "company_id": "",
                "can_block": True,
                "consent_revision": conversation.consent_revision,
                "delete_through_sequence": conversation.last_sequence,
                "is_favorite": participant.is_favorite,
                **inbox_payload(participant),
                **notification_payload(conversation, participant),
                "blocked_by_me": facts["blocked_by_me"],
                "is_blocked": facts["is_blocked"],
                "list_ids": lists[original.pk],
            }
            message = latest.get(original.pk)
            if message:
                message.conversation = conversation
            prepared[original.pk] = ConversationRead(
                conversation,
                participant,
                grant,
                message,
                preferences,
                roster=[row for row in roster if row.user.is_active],
                policy=policy,
            )
        return prepared, {
            str(row.user.id): row.user_id in online
            for facts in grants.values()
            for row in facts["roster"]
        }
