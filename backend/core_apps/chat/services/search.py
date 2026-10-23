import hashlib
import json

from django.core import signing
from django.db import transaction
from django.db.models import Exists, F, OuterRef, Q, Value
from django.db.models.functions import Concat, Lower, Replace
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.serializers import UUIDField

from core_apps.chat.models import ConversationParticipant, Message
from core_apps.chat.serializers.conversation import ConversationSerializer
from .group_access import authorize
from .group_projection import message_payload
from .search_index import normalize
from .workspace_inbox import scoped


def query_text(query):
    value = query.get("q", "").strip()
    if not 2 <= len(value) <= 200:
        raise ValidationError({"q": "Enter between 2 and 200 characters."})
    value = normalize(value)
    if len(value) < 2:
        raise ValidationError({"q": "Enter at least 2 searchable characters."})
    return value


def normalized_field(expression):
    value = Lower(expression)
    for char in "ًٌٍَُِّْـٰ":
        value = Replace(value, Value(char), Value(""))
    for source, target in zip("أإآٱى", "ااااي"):
        value = Replace(value, Value(source), Value(target))
    return value


def filter_conversations(queryset, value, user):
    # Search only disclosed names. Emails/phone numbers are never search keys.
    # Use a separate correlated participant query: the outer membership join is
    # already restricted to the viewer and cannot also find the counterparty.
    people = (
        ConversationParticipant.objects.filter(
            conversation_id=OuterRef("pk"), conversation__kind="direct"
        )
        .exclude(user=user)
        .annotate(
            search_name=normalized_field(
                Concat("user__first_name", Value(" "), "user__last_name")
            )
        )
    )
    context_match = Q()
    for word in value.split():
        people = people.filter(search_name__contains=word)
        context_match &= Q(search_context__contains=word)
    return (
        queryset.annotate(
            search_participant=Exists(people),
            search_context=normalized_field(
                Concat(
                    "housing_group__name",
                    Value(" "),
                    "company_request__title",
                    Value(" "),
                    "rental_context__properties__title",
                )
            ),
        )
        .filter(Q(search_participant=True) | context_match)
        .distinct()
    )


def discover(request, conversation_id=None):
    query = request.query_params
    kind = query.get("kind", "") if conversation_id else "search"
    if conversation_id and kind not in {"media", "file", "voice", "link"}:
        raise ValidationError({"kind": "Choose media, file, voice or link."})
    text = query_text(query) if kind == "search" else ""
    scope, company = query.get("workspace", "all"), query.get("company_id", "")
    conversations = scoped(request.user, scope, company)
    selected = conversation_id or query.get("conversation_id")
    if selected:
        selected = UUIDField().run_validation(selected)
        conversation = get_object_or_404(conversations, id=selected)
        authorize(conversation, request.user)
        conversations = conversations.filter(pk=conversation.pk)
    rows = (
        Message.objects.filter(
            conversation__in=conversations,
            deleted_at__isnull=True,
            conversation__participant_set__user=request.user,
        )
        .exclude(kind="system")
        .filter(
            Q(sequence__gte=F("conversation__participant_set__visible_from_sequence"))
            | Q(sequence__isnull=True, conversation__kind="direct")
        )
    )
    if kind == "search":
        for word in text.split():
            rows = rows.filter(search_document__body__contains=word)
    elif kind == "link":
        rows = rows.filter(search_document__isnull=False).exclude(
            search_document__links=[]
        )
    else:
        kinds = ["image", "video"] if kind == "media" else [kind]
        rows = rows.filter(attachments__kind__in=kinds, attachments__state="attached")
    binding = hashlib.sha256(
        json.dumps(
            [
                str(request.user.pk),
                request.user.security_epoch,
                scope,
                company,
                str(selected or ""),
                kind,
                text,
            ],
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    cursor = query.get("cursor")
    before = None
    snapshot = (
        Message.objects.order_by("-pkid").values_list("pkid", flat=True).first() or 0
    )
    if cursor:
        try:
            decoded = signing.loads(cursor, salt="chat-discovery", max_age=1800)
            if decoded["binding"] != binding:
                raise ValueError()
            before = int(decoded["before"])
            snapshot = int(decoded["snapshot"])
        except (signing.BadSignature, KeyError, TypeError, ValueError) as error:
            raise ValidationError({"cursor": "Refresh this search."}) from error
    rows = rows.filter(pkid__lte=snapshot)
    if before is not None:
        rows = rows.filter(pkid__lt=before)
    rows = (
        rows.select_related(
            "sender", "conversation", "reply_to__sender", "search_document"
        )
        .prefetch_related("attachments")
        .distinct()
        .order_by("-pkid")
    )
    results, last, more = [], None, False
    # Fresh authorization per candidate prevents stale membership projections
    # from leaking either snippets or attachments. Work is bounded per page.
    candidates = list(rows[:101])
    for message in candidates[:100]:
        last = message.pkid
        try:
            conversation, participant, member = authorize(
                message.conversation, request.user
            )
        except APIException:
            continue
        if message.sequence is None:
            with transaction.atomic():
                conversation, participant, member = authorize(
                    conversation, request.user, lock=True
                )
            message.refresh_from_db()
        if message.sequence < participant.visible_from_sequence:
            continue
        payload = message_payload(message, participant, member)
        if kind not in {"search", "link"}:
            payload["attachments"] = [
                a for a in payload["attachments"] if a["kind"] in kinds
            ]
        results.append(
            {
                "conversation": ConversationSerializer(
                    conversation, context={"request": request}
                ).data,
                "message": payload,
                "links": message.search_document.links if kind == "link" else [],
            }
        )
        if len(results) == 20:
            more = rows.filter(pkid__lt=last).exists()
            break
    else:
        more = len(candidates) > 100
    next_cursor = (
        signing.dumps(
            {"binding": binding, "before": last, "snapshot": snapshot},
            salt="chat-discovery",
        )
        if more and last
        else None
    )
    return {
        "results": results,
        "next_cursor": next_cursor,
        "has_more": bool(next_cursor),
    }
