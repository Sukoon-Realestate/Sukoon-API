"""Action names shared by capability discovery and participant projections."""

from ..models import (
    FinalSettlement,
    Lease,
    MaintenanceRequest,
    PaymentAttempt,
    RentalChange,
    RentalDispute,
    RentalHandover,
    RentInvoice,
)
from ..providers import signing_available
from .maintenance_access import access_window_current, appointment_reviewable
from django.utils import timezone
from .settlements_parts.prepare_settlement import settlement_precondition_error


MAINTENANCE_TRANSITIONS = {
    "acknowledge": ({"open"}, "acknowledged"),
    "propose_appointment": (
        {"open", "acknowledged", "appointment_proposed", "scheduled"},
        "appointment_proposed",
    ),
    "accept_appointment": ({"appointment_proposed"}, "scheduled"),
    "start_work": ({"acknowledged", "scheduled"}, "in_progress"),
    "report_missed": ({"scheduled"}, "acknowledged"),
    "report_resolved": ({"in_progress"}, "resolution_reported"),
    "confirm_resolved": ({"resolution_reported"}, "resolved"),
    "reopen": ({"resolution_reported", "resolved"}, "open"),
    "cancel": (
        {"open", "acknowledged", "appointment_proposed", "scheduled"},
        "cancelled",
    ),
}


def cycle_actions(user, subject):
    if not user or not user.is_active or not user.is_verified:
        return []
    lease = (
        subject
        if isinstance(subject, Lease)
        else (
            subject.invoice.lease
            if isinstance(subject, PaymentAttempt)
            else subject.lease
        )
    )
    if (
        lease is None
        or lease.renter_company_id
        or lease.legacy_read_only
        or user.pk not in {lease.owner_id, lease.tenant_id}
    ):
        return []
    from .change_versions import EDITABLE, can_edit

    if isinstance(subject, Lease):
        actions = ["request_statement", "create_rental_dispute"]
        if lease.status in {
            Lease.Status.ACTIVE,
            Lease.Status.TERMINATION_PENDING,
            Lease.Status.ENDED,
        }:
            actions += [
                "create_rental_handover",
                "create_maintenance_request",
                "create_payment_extension",
                "create_amendment",
                "create_renewal",
            ]
        if lease.status == Lease.Status.ACTIVE:
            actions.append("create_termination")
        from .evidence_storage import available as evidence_available

        if evidence_available() and lease.status in {
            Lease.Status.ACTIVE,
            Lease.Status.TERMINATION_PENDING,
            Lease.Status.ENDED,
        }:
            actions.append("upload_evidence")
        if not settlement_precondition_error(lease):
            actions.append("propose_settlement")
        from .reputation.eligibility import can_review_lease

        if can_review_lease(lease, user):
            actions.append("review_rental")
        if lease.invoices.filter(
            payment_attempts__payer=user, payment_attempts__payment_status="captured"
        ).exists():
            actions.append("create_rental_refund")
        return actions
    if isinstance(subject, RentInvoice):
        from .rental_phase3 import invoice_balance_minor

        if (
            subject.purpose == "rent"
            and subject.due_at is not None
            and subject.status not in {
                RentInvoice.Status.PAID,
                RentInvoice.Status.SETTLED,
                RentInvoice.Status.CANCELLED,
                RentInvoice.Status.WRITTEN_OFF,
            }
            and invoice_balance_minor(subject) > 0
            and "create_payment_extension" in cycle_actions(user, lease)
        ):
            return ["create_payment_extension"]
        return []
    if isinstance(subject, MaintenanceRequest):
        if subject.status == "cancelled":
            return []
        actions = [
            action
            for action, (states, _) in MAINTENANCE_TRANSITIONS.items()
            if subject.status in states
        ]
        actions += ["reply", "propose_cost"]
        owner_only = {
            "acknowledge",
            "propose_appointment",
            "start_work",
            "report_resolved",
        }
        tenant_only = {"accept_appointment", "confirm_resolved"}
        if user.pk != lease.owner_id:
            actions = [action for action in actions if action not in owner_only]
        if user.pk != lease.tenant_id:
            actions = [action for action in actions if action not in tenant_only]
        if not access_window_current(subject) or (
            subject.proposed_cost_minor
            and subject.cost_version != subject.approved_cost_version
        ):
            actions = [action for action in actions if action != "start_work"]
        if not appointment_reviewable(subject):
            actions = [action for action in actions if action != "accept_appointment"]
        if (
            not subject.appointment_ends_at
            or timezone.now() < subject.appointment_ends_at
        ):
            actions = [action for action in actions if action != "report_missed"]
        payer_id = lease.owner_id if subject.cost_payer == "owner" else lease.tenant_id
        if (
            subject.proposed_cost_minor
            and user.pk == payer_id
            and subject.approved_cost_version != subject.cost_version
        ):
            actions += ["approve_cost", "reject_cost"]
        return actions
    if isinstance(subject, RentalChange):
        if subject.kind == RentalChange.Kind.EXTERNAL_PAYMENT:
            return []  # Financial operations approval is not a participant action.
        if subject.kind == RentalChange.Kind.TERMINATION:
            from .termination_notice import blocker

            if subject.status not in {"proposed", "changes_requested", "review_required"}:
                return []
            return ["reject"] + (["accept"] if not blocker(subject) and str(user.id) not in subject.approvals else [])
        from .change_terms import changed_terms_blocker

        if (
            subject.kind in EDITABLE
            and subject.requester_id == user.pk
            and subject.status in {"proposed", "changes_requested"}
        ):
            return ["edit_change"] if can_edit(subject, user) else []

        if changed_terms_blocker(subject):
            return (
                ["reject", "request_changes"]
                if subject.status
                in {
                    RentalChange.Status.PROPOSED,
                    RentalChange.Status.CHANGES_REQUESTED,
                }
                else []
            )
        if subject.status in {
            RentalChange.Status.PROPOSED,
            RentalChange.Status.CHANGES_REQUESTED,
        }:
            return ["reject", "request_changes"] + (
                ["accept"]
                if (subject.status == "proposed" or subject.kind not in EDITABLE)
                and str(user.id) not in subject.approvals
                else []
            )
        if not signing_available():
            return []
        if subject.kind in {RentalChange.Kind.AMENDMENT, RentalChange.Kind.RENEWAL}:
            if (
                subject.status == RentalChange.Status.ACCEPTED
                and user.pk == lease.owner_id
            ):
                return ["submit_for_signature"]
            if (
                subject.status == RentalChange.Status.PENDING_SIGNATURES
                and str(user.id) not in subject.signed_by
            ):
                return ["sign"]
        return []
    if isinstance(subject, FinalSettlement):
        if subject.status == FinalSettlement.Status.ACCEPTED:
            return []
        actions = [] if settlement_precondition_error(lease) else ["propose_settlement"]
        if subject.status == FinalSettlement.Status.PROPOSED:
            actions.append("dispute")
            if str(user.id) not in subject.accepted_by:
                actions.append("accept")
        return actions
    if isinstance(subject, RentalDispute):
        return ["reply"] if subject.status == RentalDispute.Status.OPEN else []
    if isinstance(subject, PaymentAttempt):
        from .rental_phase6 import refundable_balance_minor

        return (
            ["create_rental_refund"]
            if user.pk == subject.payer_id and refundable_balance_minor(subject)
            else []
        )
    return []
