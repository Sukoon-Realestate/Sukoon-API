"""Five-minute dirty windows, durable leases, fenced completion and bounded retry."""

import hashlib
import json
import uuid
from datetime import timedelta
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from core_apps.chat.models import (
    ChatPolicyConsent,
    Conversation,
    ChatModerationInput,
    ChatModerationBatch,
    ChatAttachment,
    ChatMediaAnalysis,
)
from .policy import VERSION, enrolled, mode
from .sealed import seal, unseal
from .provider import GeminiReviewer, ProviderUnavailable


def enqueue(message):
    if (
        mode() == "off"
        or message.kind == "system"
        or message.deleted_at
        or not enrolled(message.conversation)
    ):
        return
    if not ChatPolicyConsent.objects.filter(
        user=message.sender, version=VERSION
    ).exists():
        return
    # Caller owns the conversation lock and message transaction. The first dirty
    # message starts the window; subsequent traffic cannot postpone it forever.
    earliest = (
        ChatModerationInput.objects.filter(
            conversation=message.conversation, state="pending"
        )
        .order_by("due_at")
        .first()
    )
    snapshot = {
        "message_id": str(message.id),
        "revision": message.revision,
        "actor_id": str(message.sender.id),
        "sequence": message.sequence,
        "created_at": timezone.now().isoformat(),
        "text": message.content,
        "attachments": [
            {"id": str(a.id), "fingerprint": a.fingerprint}
            for a in message.attachments.all()
        ],
    }
    ChatModerationInput.objects.get_or_create(
        message=message,
        revision=message.revision,
        defaults={
            "conversation": message.conversation,
            "ciphertext": seal(snapshot),
            "due_at": (
                earliest.due_at if earliest else timezone.now() + timedelta(minutes=5)
            ),
        },
    )


@transaction.atomic
def claim():
    now = timezone.now()
    # A retry retains exactly the same inputs. Expired workers cannot commit.
    retry = (
        ChatModerationBatch.objects.select_for_update(skip_locked=True)
        .filter(
            Q(state="running", lease_until__lte=now)
            | Q(state="retry", next_attempt_at__lte=now)
        )
        .order_by("created_at")
        .first()
    )
    if retry:
        batch = retry
    else:
        first = (
            ChatModerationInput.objects.filter(state="pending", due_at__lte=now)
            .exclude(
                conversation_id__in=ChatModerationBatch.objects.filter(
                    state__in=["running", "retry"]
                ).values("conversation_id")
            )
            .order_by("due_at")
            .first()
        )
        if not first:
            return None
        conversation = (
            Conversation.objects.select_for_update(skip_locked=True)
            .filter(pk=first.conversation_id)
            .first()
        )
        if (
            not conversation
            or ChatModerationBatch.objects.filter(
                conversation=conversation, state__in=["running", "retry"]
            ).exists()
        ):
            return None
        rows = list(
            ChatModerationInput.objects.select_for_update()
            .filter(conversation=conversation, state="pending", due_at__lte=now)
            .order_by("created_at")[:12]
        )
        if not rows:
            return None
        ids = [r.pk for r in rows]
        fingerprint = hashlib.sha256(
            (VERSION + ":" + ",".join(map(str, ids))).encode()
        ).hexdigest()
        batch = ChatModerationBatch.objects.create(
            conversation=conversation,
            fingerprint=fingerprint,
            input_ids=ids,
            policy_version=VERSION,
        )
        ChatModerationInput.objects.filter(pk__in=ids).update(state="claimed")
    batch.state, batch.lease_token = "running", uuid.uuid4()
    batch.lease_until = now + timedelta(seconds=90)
    batch.attempts += 1
    batch.save()
    return batch


def heartbeat(batch):
    if not ChatModerationBatch.objects.filter(
        pk=batch.pk,
        state="running",
        lease_token=batch.lease_token,
        lease_until__gt=timezone.now(),
    ).update(lease_until=timezone.now() + timedelta(seconds=90)):
        raise ProviderUnavailable("lease_lost")


def materialize(batch, reviewer):
    current = list(
        ChatModerationInput.objects.filter(pk__in=batch.input_ids)
        .select_related("message")
        .order_by("created_at")
    )
    before = current[0].created_at
    previous = list(
        ChatModerationInput.objects.filter(
            conversation=batch.conversation, created_at__lt=before
        )
        .exclude(ciphertext="")
        .select_related("message")
        .order_by("-created_at")[:20]
    )
    result = []
    for row in reversed(previous):
        if row.message.deleted_at or row.message.revision != row.revision:
            continue
        data = unseal(row.ciphertext)
        media = []
        for ref in data["attachments"]:
            cached = (
                ChatMediaAnalysis.objects.filter(
                    attachment__id=ref["id"],
                    fingerprint=ref["fingerprint"],
                    version=f"{reviewer.model}:extract-v1",
                )
                .select_related("attachment")
                .first()
            )
            if cached:
                media.append(
                    {
                        "source": ref["id"],
                        "kind": cached.attachment.kind,
                        **unseal(cached.ciphertext),
                    }
                )
        result.append({**data, "new": False, "media": media})
    for row in current:
        data = unseal(row.ciphertext)
        # Deleted/edited messages invalidate automatic evidence. The encrypted
        # revision remains for review, but an older revision cannot sanction.
        fresh = row.message.revision == row.revision and row.message.deleted_at is None
        media = []
        for ref in data["attachments"]:
            attachment = ChatAttachment.objects.filter(
                id=ref["id"],
                fingerprint=ref["fingerprint"],
                message=row.message,
                state="attached",
            ).first()
            if not attachment:
                raise ProviderUnavailable("media_unavailable")
            media.append(
                {
                    "source": ref["id"],
                    "kind": attachment.kind,
                    **reviewer.extract(attachment),
                }
            )
        result.append({**data, "new": fresh, "media": media})
    return result


def validated_verdicts(raw, messages):
    if (
        not isinstance(raw, dict)
        or not isinstance(raw.get("verdicts"), list)
        or len(raw["verdicts"]) > 2
    ):
        raise ProviderUnavailable("invalid_verdict")
    by_id = {m["message_id"]: m for m in messages if m["new"]}
    actors = {m["actor_id"] for m in messages}
    seen, output = set(), []
    for v in raw["verdicts"]:
        if (
            not isinstance(v, dict)
            or v.get("actor_id") not in actors
            or v["actor_id"] in seen
            or v.get("label")
            not in {"compliant", "off_topic", "uncertain", "circumvention"}
        ):
            raise ProviderUnavailable("invalid_verdict")
        seen.add(v["actor_id"])
        confidence = v.get("confidence")
        if (
            isinstance(confidence, bool)
            or not isinstance(confidence, (int, float))
            or not 0 <= confidence <= 1
        ):
            raise ProviderUnavailable("invalid_confidence")
        evidence = v.get("evidence")
        if not isinstance(evidence, list):
            raise ProviderUnavailable("invalid_evidence")
        valid = []
        for ref in evidence:
            m = by_id.get(ref.get("message_id")) if isinstance(ref, dict) else None
            if not m or m["actor_id"] != v["actor_id"]:
                raise ProviderUnavailable("invalid_evidence")
            source, quote = ref.get("source"), ref.get("quote")
            media = next((x for x in m["media"] if x["source"] == source), None)
            text = (
                m["text"]
                if source == "text"
                else media["text"] if media and not media["uncertain"] else ""
            )
            if (
                not isinstance(quote, str)
                or len(quote.strip()) < 4
                or quote not in text
            ):
                raise ProviderUnavailable("invalid_quote")
            valid.append(ref)
        if v["label"] == "circumvention" and (confidence < 0.95 or not valid):
            v = {**v, "label": "uncertain"}
        output.append(v)
    return output


def process_one(reviewer_factory=GeminiReviewer):
    if mode() == "off":
        return False
    batch = claim()
    if not batch:
        return False
    try:
        reviewer = reviewer_factory(heartbeat=lambda: heartbeat(batch))
        messages = materialize(batch, reviewer)
        if len(json.dumps(messages, ensure_ascii=False)) > 120000:
            raise ProviderUnavailable("input_limit")
        verdicts = validated_verdicts(reviewer.classify(messages), messages)
        verified = []
        if any(v["label"] == "circumvention" for v in verdicts):
            verified = validated_verdicts(
                reviewer.classify(messages, verify=True), messages
            )
        from .decisions import complete

        complete(
            batch, messages, verdicts, verified, getattr(reviewer, "model", "test")
        )
    except Exception as exc:
        # Only stable codes reach diagnostics. Never log provider payloads,
        # exception bodies, user media, transcripts or prompts.
        code = (
            str(exc) if isinstance(exc, ProviderUnavailable) else "review_unavailable"
        )
        code = (
            code
            if code.replace("_", "").isalnum() and len(code) < 80
            else "review_unavailable"
        )
        with transaction.atomic():
            row = ChatModerationBatch.objects.select_for_update().get(pk=batch.pk)
            if row.state == "running" and row.lease_token == batch.lease_token:
                row.state = (
                    "failed"
                    if row.attempts >= 6 or code in {"input_limit", "media_limit"}
                    else "retry"
                )
                row.next_attempt_at = timezone.now() + timedelta(
                    seconds=min(3600, 30 * 2**row.attempts)
                )
                row.diagnostics = {"code": code}
                row.lease_until = None
                row.save()
                if row.state == "failed":
                    ChatModerationInput.objects.filter(pk__in=row.input_ids).update(
                        state="failed"
                    )
    return True
