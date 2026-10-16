"""Operational ownership and resolution; domain execution remains authoritative."""

from datetime import timedelta
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError
from ...models import RentalOperationalCase, RentalEvidence
from .common import audit, require_revision, require_staff, staff_role
from ..rental_phase2 import RentalConflict


ROLES = {
    "support",
    "dispute_resolver",
    "psp_reconciliation",
    "financial_approver",
    "refund_operator",
    "payout_operator",
}
CASE_KINDS = {
    "move_in_mismatch",
    "access_failure",
    "owner_cancellation",
    "tenant_no_show",
    "payment_unknown",
    "capture_after_release",
    "beneficiary_issue",
    "refund_failure",
    "payout_failure",
    "deposit_dispute",
    "group_incomplete",
    "inventory_conflict",
    "verification_issue",
}


def open_system_case(
    *,
    kind,
    source_key,
    reason,
    next_action,
    lease=None,
    hold=None,
    attempt=None,
    actor=None,
    evidence=None,
):
    prop = lease.property if lease else (hold.property if hold else None)
    from .common import lifecycle_policy

    try:
        _, rules = lifecycle_policy()
        case_hours = rules["case_hours"]
    except RentalConflict:
        case_hours = 24  # Operational fallback; does not enable commercial actions.
    item, created = RentalOperationalCase.objects.get_or_create(
        source_key=source_key,
        defaults={
            "kind": kind,
            "lease": lease,
            "property": prop,
            "hold": hold,
            "payment_attempt": attempt,
            "opened_by": actor,
            "reason": reason,
            "next_action": next_action,
            "team": (
                "finance"
                if kind
                in {
                    "payment_unknown",
                    "capture_after_release",
                    "beneficiary_issue",
                    "refund_failure",
                    "payout_failure",
                }
                else "support"
            ),
            "due_at": (
                hold.reconciliation_deadline
                if hold and hold.reconciliation_deadline
                else timezone.now() + timedelta(hours=case_hours)
            ),
            "baseline": (
                {
                    "lease_revision": lease.revision,
                    "selection": lease.offer_snapshot,
                    "terms": lease.terms,
                }
                if lease
                else {}
            ),
        },
    )
    if created:
        if evidence:
            item.evidence.set(evidence)
        audit(item, actor, "case.opened", reason)
        notify_case_participants(item, "case.opened")
    return item


def notify_case_participants(item, action):
    from .notifications import record_rental_event

    recipients = {
        user
        for user in [
            item.opened_by,
            item.lease.owner if item.lease else None,
            item.lease.tenant if item.lease else None,
            item.hold.actor if item.hold else None,
        ]
        if user
    }
    record_rental_event(item, recipients, action, "open_rental_case")


def case_queryset(user):
    if staff_role(user, ROLES):
        qs = RentalOperationalCase.objects.all()
        role = getattr(getattr(user, "staff_profile", None), "role_name", "")
        if not user.is_superuser and role in {"support", "dispute_resolver"}:
            qs = qs.filter(team="support")
        elif not user.is_superuser:
            qs = qs.filter(team="finance")
        return qs
    return RentalOperationalCase.objects.filter(
        Q(opened_by=user)
        | Q(lease__owner=user)
        | Q(lease__tenant=user)
        | Q(hold__actor=user)
    )


def case_payload(item, user):
    operator = staff_role(user, ROLES)
    from ...models import RentalAuditEvent

    replies = RentalAuditEvent.objects.filter(
        subject_kind=item._meta.model_name, subject_id=item.id, action="case.reply"
    ).order_by("created_at")
    return {
        "id": str(item.id),
        "revision": item.revision,
        "kind": item.kind,
        "status": item.status,
        "lease_id": str(item.lease.id) if item.lease else None,
        "reason": item.reason,
        "next_action": item.next_action,
        "responsible_team": item.team,
        "assigned": item.assigned_to_id is not None,
        "due_at": item.due_at.isoformat(),
        "escalated_at": item.escalated_at.isoformat() if item.escalated_at else None,
        "resolution_code": item.resolution_code,
        "resolution": item.resolution,
        "replies": [
            {
                "text": row.reason,
                "created_at": row.created_at.isoformat(),
                "is_current_user": row.actor_id == user.pk,
            }
            for row in replies
        ],
        "allowed_actions": (
            ["assign", "triage", "resolve", "reopen", "reply"]
            + (["link_remedy"] if item.team == "finance" else [])
            if operator
            else ["reply"]
        ),
        "blocking_reasons": [],
        "evidence_ids": [
            str(value) for value in item.evidence.values_list("id", flat=True)
        ],
    }


def case_action(item, user, data):
    require_revision(item, data.get("expected_revision"))
    action = data.get("action")
    reason = str(data.get("reason", "")).strip()
    if not reason:
        raise ValidationError({"reason": "Explain the action."})
    if action == "reply":
        audit(item, user, "case.reply", reason)
    else:
        require_staff(user, ROLES)
        if action == "assign":
            from core_apps.users.models import User

            target = User.objects.filter(id=data.get("assignee_id")).first()
            if (
                not target
                or not target.is_active
                or not staff_role(target, ROLES)
                or not case_queryset(target).filter(pk=item.pk).exists()
            ):
                raise ValidationError(
                    {"assignee_id": "An active authorized operator is required."}
                )
            item.assigned_to = target
        elif action == "triage":
            if data.get("status") not in {
                "triaged",
                "waiting_for_tenant",
                "waiting_for_owner",
                "waiting_for_provider",
                "under_review",
                "action_pending",
            }:
                raise ValidationError({"status": "Unsupported case transition."})
            item.status = data["status"]
        elif action == "reopen":
            item.status = "reopened"
            item.resolution_code = ""
            item.resolution = ""
        elif action == "link_remedy":
            require_staff(
                user,
                {
                    "financial_approver",
                    "refund_operator",
                    "payout_operator",
                    "psp_reconciliation",
                },
            )
            from ...models import RefundRequest, RentalPayout

            if data.get("refund_id"):
                item.refund = RefundRequest.objects.filter(
                    id=data["refund_id"], lease=item.lease
                ).first()
                if not item.refund or (
                    item.payment_attempt_id
                    and item.refund.payment_attempt_id != item.payment_attempt_id
                ):
                    raise ValidationError(
                        {
                            "refund_id": "The remedy must belong to this case's payment and agreement."
                        }
                    )
            elif data.get("payout_id"):
                item.payout = RentalPayout.objects.filter(
                    id=data["payout_id"], lease=item.lease
                ).first()
                if not item.payout:
                    raise ValidationError(
                        {"payout_id": "The remedy must belong to this agreement."}
                    )
            else:
                raise ValidationError({"action": "Supply a linked financial remedy."})
        elif action == "resolve":
            if item.team == "finance":
                require_staff(
                    user,
                    {
                        "financial_approver",
                        "refund_operator",
                        "payout_operator",
                        "psp_reconciliation",
                    },
                )
            if not item.assigned_to_id:
                raise RentalConflict(
                    "Assign responsibility before resolving this case."
                )
            if item.payment_attempt and item.payment_attempt.payment_status in {
                "created",
                "pending",
                "authorized",
            }:
                raise RentalConflict(
                    "The payment outcome is still unresolved.",
                    code="reconciliation_required",
                )
            if item.refund and item.refund.status != "succeeded":
                raise RentalConflict(
                    "The refund has not executed.", code="reconciliation_required"
                )
            if item.payout and item.payout.status != "paid":
                raise RentalConflict(
                    "The payout has not executed.", code="reconciliation_required"
                )
            if item.kind == "capture_after_release" and not item.refund_id:
                raise RentalConflict(
                    "Link and execute the authorized financial remedy before resolution.",
                    code="reconciliation_required",
                )
            if data.get("resolution_code") not in {
                "corrected",
                "mutually_resolved",
                "refund_executed",
                "payout_executed",
                "no_action_required",
            }:
                raise ValidationError(
                    {"resolution_code": "A supported resolution is required."}
                )
            if data["resolution_code"] == "refund_executed" and (
                not item.refund or item.refund.status != "succeeded"
            ):
                raise RentalConflict("No executed refund supports this resolution.")
            if data["resolution_code"] == "payout_executed" and (
                not item.payout or item.payout.status != "paid"
            ):
                raise RentalConflict("No executed payout supports this resolution.")
            item.status = "resolved"
            item.resolution_code = data["resolution_code"]
            item.resolution = reason
        else:
            raise ValidationError({"action": "Unsupported case action."})
        item.next_action = str(data.get("next_action", item.next_action)).strip()
        audit(item, user, f"case.{action}", reason)
    item.revision += 1
    item.save()
    notify_case_participants(item, f"case.{action}")
    return item
