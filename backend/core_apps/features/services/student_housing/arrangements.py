from rest_framework.exceptions import PermissionDenied, ValidationError
from ...student_models import SharedLivingAgreement
from ...models import RentalConsentRecord
from ..planning import check_revision
from ..rental_phase2 import RentalConflict, fingerprint
from ..rental_lifecycle.common import audit
from .access import participant_current
from .plans import json_value


def current_rows(plan):
    return list(
        plan.participants.exclude(status="withdrawn").select_related(
            "user", "membership"
        )
    )


def can_propose(user, plan):
    return bool(
        plan.group_id
        and plan.status != "completed"
        and any(
            row.user_id == user.pk and participant_current(row)
            for row in current_rows(plan)
        )
    )


def propose(user, plan, data, previous=None):
    check_revision(plan.revision, data["plan_revision"])
    if plan.status == "completed":
        raise RentalConflict("This academic period is complete.", code="plan_completed")
    check_revision(previous.revision if previous else 0, data["expected_revision"])
    rows = current_rows(plan)
    if not plan.group_id or not any(
        row.user_id == user.pk and participant_current(row) for row in rows
    ):
        raise PermissionDenied(
            "Only an intended resident may propose shared arrangements."
        )
    if any(not participant_current(row) for row in rows):
        raise RentalConflict("Review the intended residents.", code="roster_changed")
    if (
        not plan.starts_on
        <= data["starts_on"]
        < data["ends_on_exclusive"]
        <= plan.ends_on_exclusive
    ):
        raise ValidationError(
            {"ends_on_exclusive": "Choose a period within the accommodation dates."}
        )
    item = previous or SharedLivingAgreement(plan=plan, proposed_by=user)
    if previous:
        item.revision += 1
        item.terms_revision += 1
    item.kind, item.rules = data["kind"], data["rules"]
    item.starts_on, item.ends_on_exclusive = (
        data["starts_on"],
        data["ends_on_exclusive"],
    )
    item.plan_revision, item.roster_revision = (
        plan.requirements_revision,
        plan.group.roster_revision,
    )
    item.participant_ids = sorted(str(row.user.id) for row in rows)
    item.digest = fingerprint(
        {
            "revision": item.terms_revision,
            "kind": item.kind,
            "plan_revision": plan.requirements_revision,
            "roster_revision": item.roster_revision,
            "participants": item.participant_ids,
            "rules": item.rules,
            "starts_on": str(item.starts_on),
            "ends_on_exclusive": str(item.ends_on_exclusive),
        }
    )
    item.status = "proposed"
    item.save()
    audit(
        item,
        user,
        "student_arrangement.proposed",
        metadata=audit_snapshot(item, user),
    )
    return item


def is_current(item):
    return (
        item.plan.status != "completed"
        and item.plan.requirements_revision == item.plan_revision
        and item.plan.group_id
        and item.plan.group.roster_revision == item.roster_revision
        and all(participant_current(row) for row in current_rows(item.plan))
    )


def decide(user, item, data):
    check_revision(item.revision, data["expected_revision"])
    if not is_current(item) or data["digest"] != item.digest:
        raise RentalConflict(
            "Review changed arrangements or residents.", code="stale_revision"
        )
    if str(user.id) not in item.participant_ids:
        raise PermissionDenied("Only an affected resident can decide for themselves.")
    decision = "accept" if data["consent"] else "discuss"
    existing = RentalConsentRecord.objects.filter(
        actor=user,
        subject_kind="student_arrangement",
        subject_id=item.id,
        subject_revision=item.terms_revision,
    )
    if existing.exists() and not existing.filter(decision=decision).exists():
        raise RentalConflict(
            "Propose a new version to change an existing decision.",
            code="new_revision_required",
        )
    RentalConsentRecord.objects.get_or_create(
        actor=user,
        subject_kind="student_arrangement",
        subject_id=item.id,
        subject_revision=item.terms_revision,
        decision=decision,
        defaults={
            "terms_digest": item.digest,
            "policy_version": "social-arrangements-v1",
            "snapshot": json_value(
                {
                    "rules": item.rules,
                    "participants": item.participant_ids,
                    "starts_on": item.starts_on,
                    "ends_on_exclusive": item.ends_on_exclusive,
                }
            ),
        },
    )
    decisions = RentalConsentRecord.objects.filter(
        subject_kind="student_arrangement",
        subject_id=item.id,
        subject_revision=item.terms_revision,
    )
    if decisions.filter(decision="discuss").exists():
        item.status = "discussion"
    elif decisions.filter(decision="accept").count() == len(item.participant_ids):
        item.status = "accepted"
    item.revision += 1
    item.save(update_fields=["status", "revision", "updated_at"])
    audit(
        item,
        user,
        "student_arrangement." + decision,
        metadata=audit_snapshot(item, user),
    )
    return item


def payload(item, user):
    decisions = RentalConsentRecord.objects.filter(
        subject_kind="student_arrangement",
        subject_id=item.id,
        subject_revision=item.terms_revision,
    ).select_related("actor")
    return {
        "id": str(item.id),
        "plan_id": str(item.plan.id),
        "revision": item.revision,
        "terms_revision": item.terms_revision,
        "kind": item.kind,
        "status": item.status if is_current(item) else "review_required",
        "starts_on": str(item.starts_on),
        "ends_on_exclusive": str(item.ends_on_exclusive),
        "rules": item.rules,
        "digest": item.digest,
        "participant_ids": item.participant_ids,
        "decisions": [
            {"user_id": str(d.actor.id), "decision": d.decision} for d in decisions
        ],
        "allowed_actions": (
            ["approve", "discuss", "revise"]
            if is_current(item) and str(user.id) in item.participant_ids
            else []
        ),
        "lease_effect": "none",
        "grants_access": False,
        "creates_financial_obligation": False,
    }


def history(item):
    from ...models import RentalAuditEvent

    return RentalAuditEvent.objects.filter(
        subject_kind=item._meta.model_name,
        subject_id=item.id,
        action__in=[
            "student_arrangement.proposed",
            "student_arrangement.accept",
            "student_arrangement.discuss",
        ],
    ).order_by("-created_at", "-pkid")


def audit_snapshot(item, user):
    return {
        "snapshot": payload(item, user),
        "membership_periods": {
            str(row.user.id): row.membership_period
            for row in current_rows(item.plan)
            if str(row.user.id) in item.participant_ids and participant_current(row)
        },
    }


def history_payload(event, user, membership_period):
    # Historical content requires the same affected membership period.
    # Older audit records remain intact; missing evidence never grants content.
    snapshot = event.metadata.get("snapshot") or {}
    visible = bool(
        membership_period is not None
        and str(user.id) in snapshot.get("participant_ids", [])
        and event.metadata.get("membership_periods", {}).get(str(user.id))
        == membership_period
    )
    result = {
        "revision": event.subject_revision,
        "terms_revision": snapshot.get("terms_revision"),
        "action": event.action.split(".")[-1],
        "created_at": event.created_at.isoformat(),
        "content_available": visible,
    }
    if visible:
        result.update(
            rules=snapshot.get("rules", {}),
            starts_on=snapshot.get("starts_on", ""),
            ends_on_exclusive=snapshot.get("ends_on_exclusive", ""),
        )
    return result
