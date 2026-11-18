"""Private inbox organization, independent of delivery/read receipts."""

from datetime import timedelta
from django.db.models import F, OuterRef, Subquery, Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from core_apps.chat.models import ConversationParticipant
from .unread import with_unread_count

MUTE_DURATIONS = {"off": 0, "hour": 3600, "day": 86400, "week": 604800, "forever": None}


def notifications_muted(participant):
    return participant.is_muted and (
        participant.muted_until is None or participant.muted_until > timezone.now()
    )


def inbox_payload(participant):
    return {
        "is_pinned": participant.pinned_at is not None,
        "is_marked_unread": participant.unread_reminder_sequence is not None,
        "is_muted": notifications_muted(participant),
        "muted_until": (
            participant.muted_until.isoformat() if participant.muted_until else None
        ),
        "membership_period": str(participant.membership_period or ""),
    }


def apply_inbox_preferences(participant, conversation, data):
    for field in ("is_pinned", "is_marked_unread"):
        if field in data and type(data[field]) is not bool:
            raise ValidationError({field: "Supply a boolean."})
    if "is_pinned" in data:
        participant.pinned_at = (
            (participant.pinned_at or timezone.now()) if data["is_pinned"] else None
        )
    if "is_marked_unread" in data:
        participant.unread_reminder_sequence = (
            conversation.last_sequence if data["is_marked_unread"] else None
        )
    if "is_muted" in data:
        participant.muted_until = None
    if "mute_duration" in data:
        choice = data["mute_duration"]
        if (
            not isinstance(choice, str)
            or choice not in MUTE_DURATIONS
            or "is_muted" in data
        ):
            raise ValidationError(
                {"mute_duration": "Choose a supported mute duration."}
            )
        seconds = MUTE_DURATIONS[choice]
        participant.is_muted = choice != "off"
        participant.muted_until = (
            timezone.now() + timedelta(seconds=seconds) if seconds else None
        )


def organize_inbox(queryset, user, *, unread_only=False):
    viewer = ConversationParticipant.objects.filter(
        conversation_id=OuterRef("pk"), user=user
    )
    queryset = queryset.annotate(
        inbox_pinned_at=Subquery(viewer.values("pinned_at")[:1]),
        inbox_reminder=Subquery(viewer.values("unread_reminder_sequence")[:1]),
    )
    if unread_only:
        queryset = queryset.annotate(
            inbox_unread_count=Subquery(
                with_unread_count(viewer).values("effective_unread_count")[:1]
            )
        ).filter(
            Q(inbox_unread_count__gt=0) | Q(inbox_reminder__isnull=False)
        )
    return queryset.order_by(
        F("inbox_pinned_at").desc(nulls_last=True),
        F("last_message_at").desc(nulls_last=True),
        "-id",
    )
