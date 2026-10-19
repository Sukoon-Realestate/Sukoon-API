"""Additive settlement corrections under the existing funded-settlement rules."""

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from core_apps.users.models import User
from ...models import FinalSettlement, SettlementAdjustment
from ..rental_phase2 import RentalConflict, fingerprint
from ..rental_lifecycle.common import require_staff
from ..settlements import prepare_settlement, financial_snapshot, execute_settlement
from . import (
    tenancy_access as access,
    tenancy_changes as changes,
    tenancy_closure as closure,
)


def reviewer(item, user, required):
    require_staff(user, {"financial_approver"})
    if str(user.id) in {
        v for k, v in required.items() if k != "financial_reviewer"
    } or access.member(item, user):
        raise PermissionDenied(
            "A financial operator independent of all company participants must review the correction."
        )


def require_correction_authority(item, plan):
    from .tenancy_commercial import exposure

    additional = sum(line["amount"]["amount_minor"] for line in plan["charges"])
    for mandate in [item.signer_mandate, item.payer_mandate]:
        if not access.execution_mandate(mandate, exposure=exposure(item) + additional):
            raise RentalConflict(
                "The correction exceeds current verified company execution authority.",
                code="execution_authority_required",
            )


def propose(item, user, data):
    access.require_role(item, user, {"owner", "payer"}, sensitive=True)
    if user.pk != item.lease.owner_id:
        access.require_delegate(item, user, "pay")
    original = get_object_or_404(
        FinalSettlement, lease=item.lease, execution_status="executed"
    )
    from ..business_policies import bound

    correction_policy = bound(item.lease.terms, "D09")
    lines = closure.settlement_lines(item.lease, data["lines"])
    if not lines:
        raise RentalConflict("Describe at least one supported additive correction.")
    roles = changes.current_roles(item)
    required = {k: roles[k] for k in ["owner", "signer", "payer"]}
    operator = get_object_or_404(User, id=data["financial_reviewer_id"], is_active=True)
    reviewer(item, operator, required)
    required["financial_reviewer"] = str(operator.id)
    plan = prepare_settlement(item.lease, lines)
    require_correction_authority(item, plan)
    changes.propose(
        item,
        user,
        "settlement_adjustment",
        {
            "original_settlement_id": str(original.id),
            "original_revision": original.revision,
            "lines": lines,
            "plan": plan,
            "financial_snapshot": financial_snapshot(item.lease),
            "correction_policy": correction_policy,
        },
        required,
        data["reason"],
    )
    if (
        correction_policy
        and original.executed_at
        and (timezone.now() - original.executed_at).total_seconds()
        > correction_policy["rules"]["late_review_days"] * 86400
    ):
        from ..rental_lifecycle.cases import open_system_case

        open_system_case(
            kind="company_tenancy_review",
            source_key=f"late-company-adjustment:{item.id}:{item.changes.filter(kind='settlement_adjustment').latest('pkid').id}",
            lease=item.lease,
            actor=user,
            reason="The additive correction was requested after the accepted additional-review target.",
            next_action="Review the correction with the independent financial reviewer. Elapsed time does not erase the claim or execute a financial adjustment.",
        )
    item.lease.financial_closure_status = "reopened_for_adjustment"
    item.lease.save()
    closure.close_budget(item)
    return item


def apply(item, change):
    body = change.snapshot["content"]
    original = get_object_or_404(
        FinalSettlement,
        id=body["original_settlement_id"],
        lease=item.lease,
        execution_status="executed",
        revision=body["original_revision"],
    )
    if fingerprint(financial_snapshot(item.lease)) != fingerprint(
        body["financial_snapshot"]
    ):
        raise RentalConflict(
            "Financial records changed; propose a fresh correction.",
            code="settlement_financial_state_changed",
        )
    lines = closure.settlement_lines(item.lease, body["lines"])
    plan = prepare_settlement(item.lease, lines)
    require_correction_authority(item, plan)
    if plan != body["plan"]:
        raise RentalConflict("The reviewed correction allocation changed.")
    correction = SettlementAdjustment.objects.create(
        original=original,
        lease=item.lease,
        company_change=change,
        proposed_by=change.proposed_by,
        lines=lines,
        financial_snapshot=body["financial_snapshot"],
        execution_plan=plan,
        accepted_by=list(change.snapshot["required"].values()),
    )
    execute_settlement(correction)
