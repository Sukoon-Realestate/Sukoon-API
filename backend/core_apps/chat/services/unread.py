"""Authoritative unread messages shared by chat projections and badge counts."""

from django.db.models import (
    BigIntegerField,
    Count,
    DateTimeField,
    ExpressionWrapper,
    F,
    IntegerField,
    OuterRef,
    Q,
    Subquery,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce
from core_apps.chat.models import Message


def _expression(value, field):
    if hasattr(value, "resolve_expression"):
        return ExpressionWrapper(value, output_field=field)
    return Value(value, output_field=field)


def _messages(*, conversation_id, user_id, read_sequence, visible_from, read_at):
    # Sequence cursors remain authoritative after an upgrade. Only messages
    # without a sequence use the old timestamp, and cleared history stays hidden.
    return (
        Message.objects.filter(conversation_id=conversation_id, deleted_at__isnull=True)
        .exclude(sender_id=user_id)
        .exclude(kind="system")
        .alias(
            unread_boundary=_expression(visible_from, BigIntegerField()),
            unread_timestamp=_expression(read_at, DateTimeField()),
        )
        .filter(
            Q(sequence__gt=read_sequence, sequence__gte=F("unread_boundary"))
            | (
                Q(sequence__isnull=True, unread_boundary__lte=1)
                & (
                    Q(unread_timestamp__isnull=True)
                    | Q(created_at__gt=F("unread_timestamp"))
                )
            )
        )
    )


def for_participant(participant):
    return _messages(
        conversation_id=participant.conversation_id,
        user_id=participant.user_id,
        read_sequence=participant.last_read_sequence,
        visible_from=participant.visible_from_sequence,
        read_at=participant.last_read_at,
    )


def with_unread_count(participants):
    counted = (
        _messages(
            conversation_id=OuterRef("conversation_id"),
            user_id=OuterRef("user_id"),
            read_sequence=OuterRef("last_read_sequence"),
            visible_from=OuterRef("visible_from_sequence"),
            read_at=OuterRef("last_read_at"),
        )
        .order_by()
        .values("conversation_id")
        .annotate(total=Count("pk"))
        .values("total")[:1]
    )
    return participants.annotate(
        effective_unread_count=Coalesce(
            Subquery(counted, output_field=IntegerField()), Value(0)
        )
    )


def total_for_participants(participants):
    return (
        with_unread_count(participants).aggregate(total=Sum("effective_unread_count"))[
            "total"
        ]
        or 0
    )
