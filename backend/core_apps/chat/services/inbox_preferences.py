"""Private inbox organization, independent of delivery/read receipts."""

from datetime import timedelta
from django.db.models import Exists, F, OuterRef, Subquery, Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from core_apps.chat.models import ConversationParticipant, Message

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
        inbox_read_sequence=Subquery(viewer.values("last_read_sequence")[:1]),
        inbox_visible_from=Subquery(viewer.values("visible_from_sequence")[:1]),
        inbox_reminder=Subquery(viewer.values("unread_reminder_sequence")[:1]),
        inbox_legacy_unread=Subquery(viewer.values("unread_count")[:1]),
    )
    if unread_only:
        incoming = (
            Message.objects.filter(
                conversation_id=OuterRef("pk"),
                sequence__gt=OuterRef("inbox_read_sequence"),
                sequence__gte=OuterRef("inbox_visible_from"),
                deleted_at__isnull=True,
            )
            .exclude(sender=user)
            .exclude(kind="system")
        )
        queryset = queryset.annotate(inbox_has_unread=Exists(incoming)).filter(
            Q(inbox_has_unread=True)
            | Q(inbox_reminder__isnull=False)
            | Q(kind="direct", inbox_legacy_unread__gt=0)
        )
    return queryset.order_by(
        F("inbox_pinned_at").desc(nulls_last=True),
        F("last_message_at").desc(nulls_last=True),
        "-id",
    )
