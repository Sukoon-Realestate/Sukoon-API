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
    "off_platform_payment_report",
    "company_service_request",
    "chargeback",
    "company_tenancy_review",
    "company_continuation_review",
    "company_continuation_signing",
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
    housing_request=None,
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
    from ..business_policies import current, snapshot

    response_policy = current("D01")
    if response_policy:
        urgent = kind in {
            "habitability",
            "habitability_impact",
            "access_failure",
            "move_in_mismatch",
        }
        case_hours = response_policy.rules[
            "urgent_case_hours" if urgent else "case_hours"
        ]
        deadline_policy = {
            "version": response_policy.version,
            "case_hours": case_hours,
            "basis": "elapsed_hours",
            "effect": "escalation_only",
            "business_policy": snapshot(response_policy),
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
            "housing_request": housing_request,
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
                        "chargeback",
                        "payment_unknown",
                        "capture_after_release",
                        "beneficiary_issue",
                        "refund_failure",
                        "payout_failure",
                        "off_platform_payment_report",
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
    if item.kind == "off_platform_payment_report":
        recipients = {item.opened_by} if item.opened_by else set()
    if item.housing_request_id:
        requirement = item.housing_request
        recipients = set()
        if requirement.company.memberships.filter(
            user=requirement.coordinator,
            is_active=True,
            is_coordinator=True,
            user__is_active=True,
        ).exists():
            recipients.add(requirement.coordinator)
        if item.assigned_to_id and independent_case_operator(item, item.assigned_to):
            recipients.add(item.assigned_to)
    record_rental_event(item, recipients, action, "open_rental_case")


def case_queryset(user):
    own = RentalOperationalCase.objects.filter(
        Q(opened_by=user)
        | Q(lease__owner=user)
        | Q(lease__tenant=user)
        | Q(hold__actor=user)
    ).filter(housing_request__isnull=True)
    from ..company.sourcing import visible_requests

    own = own | RentalOperationalCase.objects.filter(visible_requests(user))
    from ..company.tenancy_access import visible, roles, PRIVATE_ONLY

    corporate_ids = [t.lease_id for t in visible(user) if roles(t, user) - PRIVATE_ONLY]
    own = own | RentalOperationalCase.objects.filter(lease_id__in=corporate_ids)
    # A relationship to the agreement does not disclose another party's report.
    own = own.exclude(Q(kind="off_platform_payment_report") & ~Q(opened_by=user))
    if staff_role(user, ROLES):
        qs = RentalOperationalCase.objects.all()
        role = getattr(getattr(user, "staff_profile", None), "role_name", "")
        if not user.is_superuser and role == "kyc_reviewer":
            qs = qs.filter(team="verification")
        elif not user.is_superuser and role in {"support", "dispute_resolver"}:
            qs = qs.filter(team="support")
        elif not user.is_superuser:
            qs = qs.filter(team="finance")
        excluded_reports = [
            item.pk
            for item in qs.filter(kind="off_platform_payment_report").select_related(
                "lease"
            )
            if not independent_case_operator(item, user)
        ]
        qs = qs.exclude(pk__in=excluded_reports)
        return qs | own
    return own


def agreement_case_blocker(item):
    from ..company.service_requests import blocker

    service_blocker = blocker(item)
    if service_blocker:
        return service_blocker
    if item.kind == "chargeback" and item.payment_attempt_id:
        from ..chargebacks.projection import blockers
        from ...models import RentalChargeback

        chargeback = RentalChargeback.objects.filter(
            payment_attempt_id=item.payment_attempt_id
        ).first()
        reasons = (
            blockers(chargeback)
            if chargeback
            else ["Reconcile the original chargeback evidence."]
        )
        if reasons:
            return " ".join(reasons)
    if item.kind in {"company_continuation_review", "company_continuation_signing"}:
        from uuid import UUID
        from ...models import CompanyTenancyChange

        try:
            source_id = UUID(item.source_key.rsplit(":", 1)[-1])
        except (ValueError, TypeError):
            source_id = None
        query = CompanyTenancyChange.objects.filter(tenancy__lease=item.lease)
        change = None
        if source_id:
            change = (
                query.filter(id=source_id).first()
                if item.kind == "company_continuation_review"
                else query.filter(rental_change__signing_sessions__id=source_id).first()
            )
        if not change or change.state not in {"applied", "resolved_unapplied"}:
            return "Complete canonical continuation reconciliation or the separately signed mutual release before resolving this case."
    if item.kind == "company_tenancy_review" and item.lease_id:
        from ..company import tenancy_initial_recovery as initial_recovery

        lease = item.lease
        tenancy = lease.company_tenancy
        tenancy.lease = lease
        released = initial_recovery.applied(tenancy)
        if (
            tenancy.changes.filter(state__in=["pending", "waiting_departure"]).exists()
            or initial_recovery.pending(tenancy)
            or (
                not released
                and (
                    lease.signing_sessions.filter(status="review_required").exists()
                    or (item.hold_id and item.hold.status == "reconciliation_pending")
                )
            )
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
    from ..chargebacks.projection import payload as chargeback_payload
    from ...models import RentalChargeback

    chargeback = (
        RentalChargeback.objects.filter(
            payment_attempt_id=item.payment_attempt_id
        ).first()
        if item.kind == "chargeback"
        else None
    )

    operator = independent_case_operator(item, user)
    blocker = agreement_case_blocker(item)
    from ..business_policies import current

    can_review = bool(
        current("D25")
        and not item.baseline.get("review_pending")
        and (item.status == "resolved" or item.due_at <= timezone.now())
    )
    from ...models import RentalAuditEvent

    replies = RentalAuditEvent.objects.filter(
        subject_kind=item._meta.model_name,
        subject_id=item.id,
        action__in=["case.reply", "case.review_requested"],
    ).order_by("created_at")
    from ..company import service_requests, sourcing

    service = service_requests.projection(item, user)
    service_actions = []
    if service and item.status != "resolved" and not service["proposal_id"]:
        if operator and item.assigned_to_id == user.pk:
            service_actions.append("prepare_company_change")
        if item.opened_by_id == user.pk:
            service_actions.append("withdraw_company_request")
    return {
        "id": str(item.id),
        "revision": item.revision,
        "kind": item.kind,
        "company_service": service,
        "sourcing": sourcing.projection(item),
        "chargeback": chargeback_payload(chargeback) if chargeback else None,
        "habitability": projection(item),
        "status": item.status,
        "lease_id": str(item.lease.id) if item.lease else None,
        "reason": item.reason,
        "next_action": (
            "The canonical proposal is complete. The assigned operator must record its actual outcome and close the service request."
            if service
            and service["proposal_state"] in service_requests.TERMINAL
            and item.status != "resolved"
            else item.next_action
        ),
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
        "allowed_actions": service_actions
        + (
            ["assign", "triage", "reopen", "reply"]
            + (["resolve"] if item.assigned_to_id == user.pk and not blocker else [])
            + (
                ["link_remedy"]
                if item.team == "finance" and item.kind != "off_platform_payment_report"
                else []
            )
            if operator
            else ["reply"] + (["request_review"] if can_review else [])
        ),
        "blocking_reasons": [blocker] if blocker else [],
        "evidence_ids": [
            str(value) for value in item.evidence.values_list("id", flat=True)
        ],
        **(
            {
                "allowed_actions": (
                    []
                    if item.status == "resolved"
                    else (
                        ["reply", "assign", "triage"]
                        + (
                            ["recommend_offers", "resolve"]
                            if item.assigned_to_id == user.pk
                            else []
                        )
                        if operator
                        else ["reply", "withdraw_sourcing"]
                    )
                )
            }
            if item.kind == sourcing.KIND
            else {}
        ),
    }


def independent_case_operator(item, user):
    if not staff_role(user, ROLES):
        return False
    if (
        item.housing_request_id
        and item.housing_request.company.memberships.filter(user=user).exists()
    ):
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
    from ..company import sourcing

    sourcing.validate_case_action(item, data)
    from core_apps.support.services.payment_reports import validate_action, sync_review

    validate_action(item, data)
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
    if action in {"recommend_offers", "withdraw_sourcing"}:
        if item.kind != sourcing.KIND:
            raise ValidationError("This action requires a company sourcing case.")
        sourcing.action(item, user, data)
        audit(item, user, f"case.{action}", reason)
    elif action == "withdraw_company_request":
        from ..company.service_requests import withdraw

        withdraw(item, user)
        audit(item, user, "case.request_withdrawn", reason)
    elif action == "request_review":
        from ..policy_registry import approved_policy
        from ..business_policies import snapshot

        policy = approved_policy("D25", "cases.request_review")
        if item.baseline.get("review_pending") or (
            item.status != "resolved" and item.due_at > timezone.now()
        ):
            raise RentalConflict(
                "A review is already pending or the existing response target has not passed.",
                code="review_not_due",
            )
        item.baseline = {
            **item.baseline,
            "review_pending": True,
            "review_policy": snapshot(policy),
        }
        item.status = "reopened" if item.status == "resolved" else "under_review"
        item.resolution_code = ""
        item.resolution = ""
        item.due_at = timezone.now() + timedelta(
            hours=policy.rules["reassessment_hours"]
        )
        item.escalated_at = None
        item.next_action = "An independent operator must review the original evidence and remaining canonical obligations."
        audit(item, user, "case.review_requested", reason)
    elif action == "reply":
        audit(item, user, "case.reply", reason)
    else:
        require_staff(user, ROLES)
        if not independent_case_operator(item, user):
            raise PermissionDenied(
                "An independent operator authorized for this team is required."
            )
        if action == "prepare_company_change":
            from ..company.service_requests import prepare

            prepare(item, user, data)
        elif action == "assign":
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
                "waiting_for_company",
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
            from ..company.service_requests import validate_resolution

            validate_resolution(item, data)
            if (
                item.kind != sourcing.KIND
                and data.get("resolution_code") in sourcing.OUTCOMES
            ):
                raise ValidationError(
                    "This outcome belongs only to sourcing assistance."
                )
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
                "recommendations_delivered",
                "no_suitable_offer",
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
            item.baseline = {**item.baseline, "review_pending": False}
            item.resolution_code = data["resolution_code"]
            item.resolution = reason
        else:
            raise ValidationError({"action": "Unsupported case action."})
        item.next_action = str(data.get("next_action", item.next_action)).strip()
        audit(item, user, f"case.{action}", reason)
    item.revision += 1
    item.save()
    sync_review(item, user, action)
    notify_case_participants(item, f"case.{action}")
    return item
