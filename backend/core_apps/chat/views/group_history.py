from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from core_apps.chat.models import ChatEvent, Conversation
from core_apps.chat.services.group_access import authorize, visible_messages
from core_apps.chat.services.group_cursors import (
    decode_cursor,
    encode_cursor,
    page_limit,
)
from core_apps.chat.services.group_events import event_payload
from core_apps.chat.services.group_limits import ChatResync, ChatUnavailable
from core_apps.chat.services.group_projection import message_payload, summary


def history_response(conversation, user, query):
    with transaction.atomic():
        conversation, participant, member = authorize(conversation, user, lock=True)
        count = page_limit(query)
        cursor = (
            decode_cursor(query["older_cursor"], conversation, participant, "older")
            if query.get("older_cursor")
            else None
        )
        snapshot = cursor["s"] if cursor else conversation.last_sequence
        before = cursor["n"] if cursor else snapshot + 1
        rows = list(
            visible_messages(conversation, participant)
            .filter(
                sequence__lt=before,
                sequence__lte=snapshot,
            )
            .select_related("sender", "reply_to__sender")
            .prefetch_related("attachments")
            .order_by("-sequence")[: count + 1]
        )
        more = len(rows) > count
        rows = rows[:count]
        response = Response(
            [message_payload(m, participant, member) for m in reversed(rows)]
        )
        response["X-Chat-Older-Cursor"] = (
            encode_cursor(
                conversation, participant, "older", rows[-1].sequence, snapshot
            )
            if more
            else ""
        )
        response["X-Chat-Event-Cursor"] = encode_cursor(
            conversation, participant, "events", conversation.last_event_sequence
        )
        response["X-Chat-Has-More"] = str(more).lower()
        response["Cache-Control"] = "private, no-store"
        return response


class GroupChatSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def get(self, request, group_id):
        from core_apps.features.planning_models import HousingGroup

        group = get_object_or_404(
            HousingGroup.objects.select_for_update(),
            id=group_id,
            memberships__user=request.user,
            memberships__status="active",
        )
        conversation = Conversation.objects.filter(housing_group=group).first()
        if not conversation:
            raise ChatUnavailable("Group chat is being prepared. Please try again.")
        return Response(
            summary(conversation, request.user),
            headers={"Cache-Control": "private, no-store"},
        )


class DirectChatSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def get(self, request, id):
        conversation, _, _ = authorize(
            get_object_or_404(Conversation, id=id, kind="direct"),
            request.user,
            lock=True,
        )
        return Response(
            summary(conversation, request.user),
            headers={"Cache-Control": "private, no-store"},
        )


class GroupMessageLookupAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def get(self, request, id, client_id):
        conversation, participant, member = authorize(
            get_object_or_404(Conversation, id=id), request.user, lock=True
        )
        message = (
            visible_messages(conversation, participant)
            .filter(sender=request.user, client_message_id=client_id)
            .first()
        )
        if not message:
            raise NotFound(
                "No committed message is currently visible.",
                code="chat_message_not_found",
            )
        return Response(message_payload(message, participant, member))


class GroupMessageContextAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def get(self, request, id, message_id):
        conversation, participant, member = authorize(
            get_object_or_404(Conversation, id=id), request.user, lock=True
        )
        count = page_limit(request.query_params)
        visible = visible_messages(conversation, participant)
        target = get_object_or_404(visible, id=message_id)
        older = list(
            visible.filter(sequence__lt=target.sequence).order_by("-sequence")[
                : count // 2
            ]
        )
        newer = list(
            visible.filter(sequence__gte=target.sequence).order_by("sequence")[
                : count - len(older)
            ]
        )
        rows = list(reversed(older)) + newer
        response = Response([message_payload(m, participant, member) for m in rows])
        more = visible.filter(sequence__lt=rows[0].sequence).exists()
        response["X-Chat-Older-Cursor"] = (
            encode_cursor(
                conversation,
                participant,
                "older",
                rows[0].sequence,
                conversation.last_sequence,
            )
            if more
            else ""
        )
        response["X-Chat-Has-More"] = str(more).lower()
        response["X-Chat-Event-Cursor"] = encode_cursor(
            conversation, participant, "events", conversation.last_event_sequence
        )
        return response


class GroupEventsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def get(self, request, id):
        conversation, participant, _ = authorize(
            get_object_or_404(Conversation, id=id), request.user, lock=True
        )
        count = page_limit(request.query_params)
        if not request.query_params.get("after_cursor"):
            raise ValidationError(
                {"after_cursor": "Supply the last acknowledged event cursor."}
            )
        cursor = decode_cursor(
            request.query_params["after_cursor"], conversation, participant, "events"
        )
        if cursor["n"] > conversation.last_event_sequence:
            raise ChatResync()
        rows = list(
            ChatEvent.objects.filter(
                conversation=conversation, sequence__gt=cursor["n"]
            ).order_by("sequence")[: count + 1]
        )
        if any(
            row.sequence != cursor["n"] + index + 1 for index, row in enumerate(rows)
        ) or (not rows and cursor["n"] < conversation.last_event_sequence):
            raise ChatResync()
        more, rows = len(rows) > count, rows[:count]
        result = [
            payload
            for event in rows
            if (payload := event_payload(event, request.user)) is not None
        ]
        response = Response(result)
        response["X-Chat-Event-Cursor"] = encode_cursor(
            conversation,
            participant,
            "events",
            rows[-1].sequence if rows else cursor["n"],
        )
        response["X-Chat-Has-More"] = str(more).lower()
        return response
