"""Operational ownership and resolution; domain execution remains authoritative."""

from datetime import timedelta
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from ...models import RentalOperationalCase, RentalEvidence
from .common import audit, require_revision, require_staff, staff_role
from ..rental_phase2 import RentalConflict


ROLES = {
    "kyc_reviewer",
    "support",
    "dispute_resolver",
    "psp_reconciliation",
    "financial_approver",
    "refund_operator",
    "payout_operator",
}
CASE_KINDS = {
    "company_tenancy_review",
    "agreement_terms_review",
    "habitability",
    "habitability_impact",
    "student_verification",
    "maintenance",
    "roommate_support",
    "academic_transition",
    "admission_request",
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
        policy, rules = lifecycle_policy()
        case_hours = rules["case_hours"]
        deadline_policy = {
            "version": policy.version,
            "case_hours": case_hours,
            "basis": "elapsed_hours",
            "effect": "escalation_only",
        }
    except RentalConflict:
        case_hours = 24  # Existing operational fallback; never a commercial deadline.
        deadline_policy = {
            "version": None,
            "case_hours": case_hours,
            "basis": "elapsed_hours",
            "effect": "escalation_only",
            "source": "existing_operational_fallback",
        }
    if hold and hold.reconciliation_deadline:
        due_at = hold.reconciliation_deadline
        deadline_policy = {
            "version": hold.policy_version,
            "basis": "original_hold_reconciliation_deadline",
            "effect": "escalation_only",
            "source": "reservation_hold",
            "hold_id": str(hold.id),
            "hold_revision": hold.revision,
            "due_at": due_at.isoformat(),
        }
    else:
        due_at = timezone.now() + timedelta(hours=case_hours)
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
                "verification"
                if kind == "student_verification"
                else (
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
                )
            ),
            "due_at": due_at,
            "baseline": {
                "response_target": deadline_policy,
                **(
                    {
                        "lease_revision": lease.revision,
                        "selection": lease.offer_snapshot,
                        "terms": lease.terms,
                    }
                    if lease
                    else {}
                ),
            },
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
    own = RentalOperationalCase.objects.filter(
        Q(opened_by=user)
        | Q(lease__owner=user)
        | Q(lease__tenant=user)
        | Q(hold__actor=user)
    )
    from ..company.tenancy_access import visible, roles
    from core_apps.common.recovery import scope_available

    if scope_available("company_authority"):
        corporate_ids = [
            t.lease_id
            for t in visible(user)
            if roles(t, user) - {"employee", "incoming_employee"}
        ]
        own = own | RentalOperationalCase.objects.filter(lease_id__in=corporate_ids)
    if staff_role(user, ROLES):
        qs = RentalOperationalCase.objects.all()
        role = getattr(getattr(user, "staff_profile", None), "role_name", "")
        if not user.is_superuser and role == "kyc_reviewer":
            qs = qs.filter(team="verification")
        elif not user.is_superuser and role in {"support", "dispute_resolver"}:
            qs = qs.filter(team="support")
        elif not user.is_superuser:
            qs = qs.filter(team="finance")
        return qs | own
    return own


def agreement_case_blocker(item):
    if item.kind == "company_tenancy_review" and item.lease_id:
        lease = item.lease
        if (
            lease.company_tenancy.changes.filter(
                state__in=["pending", "waiting_departure"]
            ).exists()
            or lease.signing_sessions.filter(status="review_required").exists()
            or (item.hold_id and item.hold.status == "reconciliation_pending")
        ):
            return "Reconcile the pending company change or original provider instruction before closing this case."
    if item.kind != "agreement_terms_review":
        return None
    from uuid import UUID
    from ...models import RentalChange

    try:
        change_id = UUID(item.source_key.split(":")[1])
    except (ValueError, IndexError):
        change_id = None
    if (
        not change_id
        or not RentalChange.objects.filter(
            pk=change_id, lease_id=item.lease_id, status=RentalChange.Status.APPLIED
        ).exists()
    ):
        return "The signed change still requires an authorized correction; closing this case does not correct the agreement."
    return None


def case_payload(item, user):
    from .habitability import projection

    operator = independent_case_operator(item, user)
    blocker = agreement_case_blocker(item)
    from ...models import RentalAuditEvent

    replies = RentalAuditEvent.objects.filter(
        subject_kind=item._meta.model_name, subject_id=item.id, action="case.reply"
    ).order_by("created_at")
    return {
        "id": str(item.id),
        "revision": item.revision,
        "kind": item.kind,
        "habitability": projection(item),
        "status": item.status,
        "lease_id": str(item.lease.id) if item.lease else None,
        "reason": item.reason,
        "next_action": item.next_action,
        "responsible_team": item.team,
        "assigned": item.assigned_to_id is not None,
        "response_target": item.baseline.get("response_target"),
        "due_at": item.due_at.isoformat(),
        "escalated_at": item.escalated_at.isoformat() if item.escalated_at else None,
        "resolution_code": item.resolution_code,
        "resolution": item.resolution,
        "remedies": [
            {"kind": kind, "id": str(remedy.id), "status": remedy.status}
            for kind, remedy in [("refund", item.refund), ("payout", item.payout)]
            if remedy is not None
        ],
        "assignment_current": bool(
            item.assigned_to_id and independent_case_operator(item, item.assigned_to)
        ),
        "replies": [
            {
                "text": row.reason,
                "created_at": row.created_at.isoformat(),
                "is_current_user": row.actor_id == user.pk,
            }
            for row in replies
        ],
        "allowed_actions": (
            ["assign", "triage", "reopen", "reply"]
            + (["resolve"] if item.assigned_to_id == user.pk and not blocker else [])
            + (["link_remedy"] if item.team == "finance" else [])
            if operator
            else ["reply"]
        ),
        "blocking_reasons": [blocker] if blocker else [],
        "evidence_ids": [
            str(value) for value in item.evidence.values_list("id", flat=True)
        ],
    }


def independent_case_operator(item, user):
    if not staff_role(user, ROLES):
        return False
    interested = {item.opened_by_id}
    if item.lease_id:
        interested.update({item.lease.owner_id, item.lease.tenant_id})
        if (
            item.lease.renter_company_id
            and item.lease.renter_company.memberships.filter(user=user).exists()
        ):
            return False
    if item.hold_id:
        interested.add(item.hold.actor_id)
    if user.pk in interested:
        return False
    role = getattr(getattr(user, "staff_profile", None), "role_name", "")
    return user.is_superuser or (
        (item.team == "verification" and role == "kyc_reviewer")
        or (item.team == "support" and role in {"support", "dispute_resolver"})
        or (
            item.team == "finance"
            and role
            in {
                "financial_approver",
                "refund_operator",
                "payout_operator",
                "psp_reconciliation",
            }
        )
    )


def case_action(item, user, data):
    require_revision(item, data.get("expected_revision"))
    action = data.get("action")
    reason = str(data.get("reason", "")).strip()
    if not reason:
        raise ValidationError({"reason": "Explain the action."})
    if (
        action == "resolve"
        and item.habitability_restrictions.filter(cleared_at__isnull=True).exists()
    ):
        raise RentalConflict(
            "The approved restriction requires a separate inspected clearance.",
            code="habitability_restricted",
        )
    if action == "reply":
        audit(item, user, "case.reply", reason)
    else:
        require_staff(user, ROLES)
        if not independent_case_operator(item, user):
            raise PermissionDenied(
                "An independent operator authorized for this team is required."
            )
        if action == "assign":
            from core_apps.users.models import User

            target = User.objects.filter(id=data.get("assignee_id")).first()
            if (
                not target
                or not target.is_active
                or not independent_case_operator(item, target)
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
            blocker = agreement_case_blocker(item)
            if blocker:
                raise RentalConflict(blocker, code="reconciliation_required")
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
            if item.assigned_to_id != user.pk or not independent_case_operator(
                item, item.assigned_to
            ):
                raise RentalConflict(
                    "Assign this case to the current independent operator before resolving it."
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
