"""Server-owned sanctions, participant-scoped warnings and review receipts."""

import hashlib
import json
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError
from core_apps.chat.models import (
    Conversation,
    ChatModerationBatch,
    ChatModerationCase,
    ChatModerationInput,
    ChatPolicyNotice,
    ChatPolicyConsent,
    AccountRestriction,
    ChatModerationAppeal,
    ChatModerationAction,
)
from core_apps.chat.services.group_limits import ChatConflict
from core_apps.users.models import User
from core_apps.admin_api.models import UserReport
from .policy import VERSION, mode, projection
from .sealed import seal, unseal
from .provider import ProviderUnavailable


def _publish_account(user_pk):
    # Called after commit: never lock other users while holding conversation locks.
    from core_apps.chat.services.group_events import record_event

    for pk in Conversation.objects.filter(participants__pk=user_pk).values_list(
        "pk", flat=True
    ):
        with transaction.atomic():
            conversation = Conversation.objects.select_for_update().get(pk=pk)
            record_event(conversation, "conversation.updated")


def _changed(user):
    transaction.on_commit(lambda pk=user.pk: _publish_account(pk))
    from django.core.cache import cache

    # Property list caches use versions; authorization is also checked at read/write.
    transaction.on_commit(lambda: cache.delete("public_property_list"))


@transaction.atomic
def complete(batch, messages, verdicts, verified, model):
    people = list(
        User.objects.select_for_update()
        .filter(conversation_participants__conversation=batch.conversation)
        .order_by("pk")
    )
    conversation = Conversation.objects.select_for_update().get(
        pk=batch.conversation_id
    )
    row = ChatModerationBatch.objects.select_for_update().get(pk=batch.pk)
    if (
        row.state != "running"
        or row.lease_token != batch.lease_token
        or row.lease_until <= timezone.now()
    ):
        raise ProviderUnavailable("lease_lost")
    mode_now = mode()
    by_actor = {str(p.id): p for p in people}
    by_id = {m["message_id"]: m for m in messages if m["new"]}
    for v in verdicts:
        user = by_actor.get(v["actor_id"])
        if not user or mode_now not in {"warn", "enforce"} or v["label"] == "compliant":
            continue
        key = hashlib.sha256(f"{row.fingerprint}:{user.id}".encode()).hexdigest()
        if v["label"] == "off_topic":
            if not ChatPolicyNotice.objects.filter(
                user=user,
                conversation=conversation,
                kind="off_topic",
                created_at__gt=timezone.now() - timedelta(days=1),
            ).exists():
                ChatPolicyNotice.objects.get_or_create(
                    dedupe_key=key,
                    defaults={
                        "user": user,
                        "conversation": conversation,
                        "kind": "off_topic",
                    },
                )
                _changed(user)
            continue
        # Recheck revisions after the provider call while the send/edit lock is held.
        refs = [ref["message_id"] for ref in v["evidence"]]
        current = {str(m.id): m for m in conversation.messages.filter(id__in=refs)}
        fresh = bool(refs) and all(
            identity in current
            and not current[identity].deleted_at
            and current[identity].revision == by_id[identity]["revision"]
            for identity in refs
        )
        second = next(
            (
                x
                for x in verified
                if x["actor_id"] == v["actor_id"] and x["label"] == "circumvention"
            ),
            None,
        )
        confirmed = fresh and v["label"] == "circumvention" and second is not None
        # A verifier must ground its finding in the same newly evaluated messages.
        confirmed = confirmed and bool(
            set(refs) & {ref["message_id"] for ref in second["evidence"]}
        )
        pending = ChatPolicyNotice.objects.filter(
            user=user, kind="warning", acknowledged_at__isnull=True
        ).exists()
        if confirmed and pending:
            continue  # No extra warnings or strikes before the first is acknowledged.
        prior = (
            ChatPolicyNotice.objects.filter(
                user=user,
                kind="warning",
                acknowledged_at__gte=timezone.now() - timedelta(days=30),
                case__state="warning",
            )
            .order_by("-acknowledged_at")
            .first()
        )
        repeated = bool(
            prior
            and confirmed
            and all(
                by_id[identity]["created_at"] > prior.acknowledged_at.isoformat()
                for identity in refs
            )
        )
        state = (
            "pending_review"
            if repeated and mode_now == "enforce"
            else "warning" if confirmed else "review"
        )
        if AccountRestriction.objects.filter(
            user=user, state__in=["pending_review", "permanent"]
        ).exists():
            continue
        report = UserReport.objects.create(
            reported_user=user,
            reason="Rental chat policy review",
            reason_type="other",
            automation_level="auto",
        )
        case = ChatModerationCase.objects.create(
            report=report,
            conversation=conversation,
            subject=user,
            batch=row,
            dedupe_key=key,
            state=state,
            policy_version=VERSION,
            evidence_ciphertext=seal(
                {
                    "verdict": v,
                    "verification": second,
                    "messages": messages[-32:],
                    "previous_warning_id": str(prior.id) if prior else None,
                }
            ),
        )
        if state == "warning":
            ChatPolicyNotice.objects.create(
                conversation=conversation,
                user=user,
                case=case,
                kind="warning",
                dedupe_key=key,
            )
        elif state == "pending_review":
            AccountRestriction.objects.create(user=user, case=case)
            report.status = "suspended"
            report.save(update_fields=["status", "updated_at"])
        from .notifications import create_notice

        create_notice(case)
        _changed(user)
    row.state, row.model, row.lease_until = "complete", model, None
    row.diagnostics = {"actors_reviewed": len(verdicts), "mode": mode_now}
    row.save()
    ChatModerationInput.objects.filter(pk__in=row.input_ids).update(state="complete")


@transaction.atomic
def acknowledge(user, conversation, data):
    from core_apps.chat.services.direct_access import authorize

    conversation, _, _ = authorize(conversation, user, lock=True)
    if data.get("policy_version") != VERSION:
        raise ChatConflict("Chat policy changed. Refresh and review it again.")
    notice_id = data.get("notice_id")
    if notice_id:
        notice = (
            ChatPolicyNotice.objects.select_for_update()
            .filter(id=notice_id, user=user)
            .first()
        )
        if not notice:
            raise NotFound()
        if not notice.acknowledged_at:
            notice.acknowledged_at = timezone.now()
            notice.acknowledged_sequence = conversation.last_sequence
            notice.save(
                update_fields=["acknowledged_at", "acknowledged_sequence", "updated_at"]
            )
    else:
        ChatPolicyConsent.objects.get_or_create(user=user, version=VERSION)
    _changed(user)
    return projection(conversation, user)


def case_payload(case, *, admin=False):
    appeal = ChatModerationAppeal.objects.filter(case=case).first()
    result = {
        "id": str(case.id),
        "state": case.state,
        "revision": case.revision,
        "policy_version": case.policy_version,
        "reason": "rental_off_platform_review",
        "created_at": case.created_at.isoformat(),
        "appeal_submitted": bool(appeal),
        "can_appeal": case.state in {"pending_review", "permanent", "warning", "review"}
        and not appeal,
        "review_overdue": case.state in {"pending_review", "review"}
        and case.created_at < timezone.now() - timedelta(hours=48),
    }
    if admin:
        result.update(
            subject_id=str(case.subject.id),
            conversation_id=str(case.conversation.id),
            evidence=unseal(case.evidence_ciphertext),
            appeal=unseal(appeal.ciphertext) if appeal else None,
            actions=[
                {
                    "action": a.action,
                    "notes": a.notes,
                    "revision": a.result_revision,
                    "actor_id": str(a.actor.id),
                }
                for a in case.actions.select_related("actor")
            ],
        )
    return result


@transaction.atomic
def appeal(user, case_id, client_id, text):
    User.objects.select_for_update().get(pk=user.pk)
    case = (
        ChatModerationCase.objects.select_for_update()
        .filter(id=case_id, subject=user)
        .first()
    )
    if not case:
        raise NotFound()
    existing = ChatModerationAppeal.objects.filter(case=case).first()
    if existing:
        if (
            existing.client_id != client_id
            or unseal(existing.ciphertext).get("text") != text
        ):
            raise ChatConflict("An appeal already exists for this case.")
        return case_payload(case)
    if case.resolved_at:
        raise ChatConflict("This case is closed.")
    ChatModerationAppeal.objects.create(
        case=case, client_id=client_id, ciphertext=seal({"text": text})
    )
    case.revision += 1
    case.save(update_fields=["revision", "updated_at"])
    return case_payload(case)


@transaction.atomic
def review(actor, case_id, client_id, expected_revision, action, notes):
    from core_apps.admin_api.permissions import require_staff_actor

    require_staff_actor(actor, {"system_owner", "main_admin"}, lock=False)
    case = ChatModerationCase.objects.filter(id=case_id).first()
    if not case:
        raise NotFound()
    # Same root lock as send/restriction creation; lock the reviewer in sorted order.
    list(
        User.objects.select_for_update()
        .filter(pk__in=[case.subject_id, actor.pk])
        .order_by("pk")
    )
    require_staff_actor(actor, {"system_owner", "main_admin"}, lock=True)
    case = ChatModerationCase.objects.select_for_update().get(pk=case.pk)
    fingerprint = hashlib.sha256(
        json.dumps(
            {"revision": expected_revision, "action": action, "notes": notes},
            sort_keys=True,
        ).encode()
    ).hexdigest()
    previous = ChatModerationAction.objects.filter(
        case=case, client_id=client_id
    ).first()
    if previous:
        if previous.fingerprint != fingerprint:
            raise ChatConflict(
                "This operation ID was already used with different content."
            )
        return case_payload(case, admin=True)
    if case.revision != expected_revision:
        raise ChatConflict(
            "Another reviewer changed the case. Refresh it before deciding."
        )
    if (
        action not in {"dismiss", "release", "keep_restricted", "ban"}
        or not notes.strip()
    ):
        raise ValidationError("Choose a review action and explain the decision.")
    if case.resolved_at and action not in {"release", "dismiss"}:
        raise ChatConflict("This case is closed.")
    now = timezone.now()
    if action in {"dismiss", "release"}:
        AccountRestriction.objects.filter(case=case).update(
            state="released", released_at=now
        )
        ChatPolicyNotice.objects.filter(case=case, acknowledged_at__isnull=True).update(
            acknowledged_at=now
        )
        case.state, case.resolved_at = (
            "dismissed" if action == "dismiss" else "released"
        ), now
        case.report.status = "dismissed"
    else:
        state = "permanent" if action == "ban" else "pending_review"
        AccountRestriction.objects.update_or_create(
            case=case,
            defaults={"user": case.subject, "state": state, "released_at": None},
        )
        case.state = state
        case.report.status = "banned" if action == "ban" else "suspended"
    case.revision += 1
    case.save()
    case.report.reviewed_by, case.report.reviewed_at, case.report.notes = (
        actor,
        now,
        notes,
    )
    case.report.save()
    ChatModerationAction.objects.create(
        case=case,
        actor=actor,
        client_id=client_id,
        fingerprint=fingerprint,
        action=action,
        notes=notes,
        result_revision=case.revision,
    )
    _changed(case.subject)
    return case_payload(case, admin=True)
