"""Read-only participant guidance. Never creates/settles records or grants rights."""

from django.utils import timezone
from ...models import FinalSettlement
from ...providers import fake_provider_available
from ..lease_permissions import agreement_actions
from ..rental_phase6 import closure_blocking_reasons

# These are the canonical closure service's reasons, not a second closure policy.
CLOSURE_ITEMS = (
    ("agreement", "The legal agreement has not ended.", "lease_review", "both"),
    ("payment", "A payment is still awaiting reconciliation.", "payments", "provider"),
    ("possession", "Occupancy has not been returned.", "handovers", "both"),
    ("invoices", "An invoice balance remains.", "payments", "tenant"),
    ("deposit", "The deposit is unresolved.", "deposit", "both"),
    ("refund", "A refund is pending.", "refunds", "operator"),
    ("dispute", "A dispute is unresolved.", "disputes", "operator"),
    ("inventory", "Rental inventory has not been returned.", "handovers", "both"),
    ("execution", "Settlement execution is incomplete.", "closure", "operator"),
    ("settlement", "The final settlement is not accepted.", "closure", "both"),
)
PRIVATE_FINANCIAL_REASONS = {
    "An owner payable or payout is unresolved.",
    "Owner funds must be recovered after a refunded payout.",
}


def participant_reasons(lease, user, reasons=None):
    reasons = closure_blocking_reasons(lease) if reasons is None else reasons
    return list(
        dict.fromkeys(
            (
                "Financial processing remains open."
                if user.pk != lease.owner_id and reason in PRIVATE_FINANCIAL_REASONS
                else reason
            )
            for reason in reasons
        )
    )


def action(kind, identifier, description, *, actor, code=None):
    return {
        "action": code or f"review_{kind}",
        "kind": kind,
        "resource_id": str(identifier),
        "description": description,
        "next_actor": actor,
    }


def lease_journey(lease, user):
    reasons = closure_blocking_reasons(lease)
    is_owner = user.pk == lease.owner_id
    role = "owner" if is_owner else "tenant"
    ended = lease.status in {"ended", "cancelled"}
    completed = ended and lease.financial_closure_status == "closed" and not reasons
    items = [
        dict(
            code=code,
            blocked=reason in reasons,
            kind=kind,
            resource_id=str(lease.id),
            next_actor=actor,
        )
        for code, reason, kind, actor in CLOSURE_ITEMS
    ]
    known = {item[1] for item in CLOSURE_ITEMS}
    # Private payout references, amounts and beneficiaries never enter this projection.
    if any(reason not in known for reason in reasons):
        items.append(
            dict(
                code="financial_processing",
                blocked=True,
                kind="payables" if is_owner else "closure",
                resource_id=str(lease.id),
                next_actor="operator",
            )
        )
    next_action, next_actor, deadline = None, "", None
    stage = "closed" if completed else "closure" if ended else "tenancy"
    permissions = agreement_actions(user, lease)
    pending = (
        lease.invoices.filter(
            payment_attempts__payment_status__in=["created", "pending", "authorized"]
        )
        .order_by("due_date", "pk")
        .first()
    )
    invoice = (
        lease.invoices.filter(status__in=["due", "overdue", "partially_paid"])
        .order_by("due_date", "pk")
        .first()
    )
    if lease.legacy_read_only:
        stage = "historical"
    elif pending:
        stage, next_actor = "payment_reconciliation", "provider"
        next_action = action(
            "invoice",
            pending.id,
            "Check the original payment result before starting another payment.",
            actor=next_actor,
            code="reconcile_payment",
        )
    elif lease.status in {"draft", "pending_signatures", "pending"}:
        stage = "agreement"
        actionable = bool(
            set(permissions) & {"accept_review", "submit_for_signature", "sign"}
        )
        if actionable:
            next_actor = role
        elif not fake_provider_available():
            next_actor = "provider"
        elif lease.status == "draft" and str(user.id) in lease.reviewed_by:
            next_actor = "tenant" if is_owner else "owner"
        else:
            next_actor = "provider"
        next_action = action(
            "lease_review",
            lease.id,
            "Review the agreement, current permissions and signature requirements.",
            actor=next_actor,
        )
    elif lease.status == "expired":
        stage, next_actor = "expired", "operator"
        next_action = action(
            "lease_review",
            lease.id,
            "Review the expired agreement and any remaining obligations.",
            actor=next_actor,
        )
    elif invoice:
        stage, next_actor = "payment", "tenant"
        deadline = str(invoice.due_date) if invoice.due_date else None
        next_action = action(
            "invoice",
            invoice.id,
            (
                "Review the invoice and payment status."
                if is_owner
                else "Review the amount due and the original payment status."
            ),
            actor=next_actor,
        )
    elif lease.status == "signed":
        stage, next_actor = "activation", "provider"
        next_action = action(
            "lease_review",
            lease.id,
            "Review activation requirements. Signing alone does not establish payment or possession.",
            actor=next_actor,
        )
    elif ended and not completed:
        next_actor = next(
            (item["next_actor"] for item in items if item["blocked"]), "operator"
        )
        settlement = FinalSettlement.objects.filter(lease=lease).first()
        if settlement and settlement.status == "proposed":
            next_actor = (
                role
                if str(user.id) not in settlement.accepted_by
                else ("tenant" if is_owner else "owner")
            )
        next_action = action(
            "closure",
            lease.id,
            "Review the remaining return and financial closure requirements.",
            actor=next_actor,
        )
    else:
        handover = (
            lease.handovers.exclude(status="accepted").order_by("-created_at").first()
        )
        if handover:
            stage = "handover"
            next_actor = (
                role
                if str(user.id) not in handover.approvals
                else ("tenant" if is_owner else "owner")
            )
            next_action = action(
                "handover",
                handover.id,
                "Review the handover and the remaining participant approvals.",
                actor=next_actor,
            )
        elif (
            lease.status in {"active", "termination_pending"}
            and lease.occupancy_status == "not_started"
        ):
            stage = "handover"
            next_actor = (
                "both" if "create_rental_handover" in permissions else "provider"
            )
            next_action = action(
                "handovers",
                lease.id,
                "Review move-in requirements and arrange the handover.",
                actor=next_actor,
            )
    return {
        "version": 1,
        "stage": stage,
        "next_actor": next_actor,
        "next_action": next_action,
        "deadline": deadline,
        "deadline_kind": "invoice_due_date" if deadline else None,
        "complete": completed,
        "closure_items": items if ended else [],
        "blocking_reasons": participant_reasons(lease, user, reasons) if ended else [],
        "allowed_actions": permissions,
        "generated_at": timezone.now().isoformat(),
    }


def application_journey(interest, proposal, invitation, user):
    terminal = interest.status in {"withdrawn", "rejected"}
    item = invitation or proposal or interest
    kind = "invitation" if invitation else "terms" if proposal else "application"
    actor = interest.waiting_for or "owner"
    if proposal and not invitation:
        if proposal.status in {"rejected", "superseded"}:
            # A stopped proposal does not withdraw the underlying application.
            item, kind, actor = interest, "application", "owner"
        elif proposal.status == "accepted":
            actor = "owner" if fake_provider_available() else "provider"
        else:
            actor = (
                ("owner" if user.pk == proposal.owner_id else "tenant")
                if str(user.id) not in proposal.accepted_by
                else ("tenant" if user.pk == proposal.owner_id else "owner")
            )
    if invitation:
        actor = "tenant" if invitation.status == "pending" else "owner"
        terminal = (
            terminal
            or invitation.status in {"rejected", "revoked", "expired"}
            or (not invitation.lease_id and invitation.expires_at <= timezone.now())
        )
    deadline = getattr(item, "expires_at", None) or interest.response_due_at
    return {
        "version": 1,
        "stage": "stopped" if terminal else kind,
        "next_actor": "" if terminal else actor,
        "complete": False,
        "next_action": (
            None
            if terminal
            else action(
                kind,
                item.id,
                "Review the current request and available actions.",
                actor=actor,
            )
        ),
        "deadline": deadline.isoformat() if deadline else None,
        "deadline_kind": "response_or_expiry" if deadline else None,
        "closure_items": [],
        "blocking_reasons": [],
        "generated_at": timezone.now().isoformat(),
    }
