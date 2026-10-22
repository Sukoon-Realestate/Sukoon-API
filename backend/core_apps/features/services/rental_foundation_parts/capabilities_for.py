"""Rental foundation: capabilities for."""

from core_apps.properties.models import Property
from core_apps.users.models import User
from ...models import (
    Lease,
    OwnerPaymentProfile,
    RentalInterest,
    RentInvoice,
    PaymentAttempt,
    RentalHandover,
    MaintenanceRequest,
    RentalChange,
    FinalSettlement,
    RentalDispute,
    TenancyInvitation,
    TermsProposal,
)
from ...providers import checkout_available, fake_provider_available
from ..cycle_permissions import cycle_actions
from ..lease_permissions import (
    agreement_actions,
    can_revoke_invitation,
    handover_actions,
    interest_actions,
    interest_creation_blocker,
    proposal_actions,
)
from ..rental_phase3 import invoice_payment_allowed
from .get_authorized_rental_subject import POLICY_VERSION


def capabilities_for(user, subject, requested_action=""):
    """Return only capabilities backed by the current operational implementation."""
    enabled = []
    allowed = []
    blocking = []

    from ..evidence_storage import available as evidence_available

    phase2_ready = fake_provider_available()
    if isinstance(subject, Lease):
        if subject.renter_company_id:
            from ..company.tenancy_access import roles, commercial_read

            corporate_roles = roles(subject.company_tenancy, user)
            corporate_actions = []
            if (
                phase2_ready
                and subject.status == "pending_signatures"
                and corporate_roles & {"owner", "signer"}
            ):
                corporate_actions.append("sign")
            if evidence_available() and corporate_roles & {"owner", "coordinator", "payer"}:
                corporate_actions.append("upload_evidence")
            if commercial_read(subject, user):
                corporate_actions.append("request_statement")
            if not user.is_verified or not user.is_active:
                corporate_actions = []
            return {
                "account_id": str(user.id),
                "account_verified": bool(user.is_active and user.is_verified),
                "enabled_capabilities": (
                    ["rental_agreements", "rental_handovers", "rental_settlement"]
                    if phase2_ready
                    else []
                )
                + (["rental_maintenance"] if evidence_available() else [])
                + (
                    ["signed_documents"]
                    if "request_statement" in corporate_actions
                    else []
                ),
                "allowed_actions": corporate_actions,
                "policy_version": POLICY_VERSION,
                "blocking_reasons": (
                    []
                    if not requested_action or requested_action in corporate_actions
                    else ["Use the current company tenancy responsibility."]
                ),
            }
        allowed.extend(agreement_actions(user, subject))
        enabled.append("rental_center")
        if not subject.legacy_read_only:
            enabled.append("rental_maintenance")
        if phase2_ready and not subject.legacy_read_only:
            enabled.append("rental_agreements")
        if checkout_available():
            enabled.append("rent_checkout")
        if phase2_ready and not subject.legacy_read_only:
            enabled.extend(
                [
                    "rental_handovers",
                    "rental_deposits",
                    "rental_maintenance",
                    "rental_changes",
                    "rental_settlement",
                    "rental_disputes",
                    "signed_documents",
                    "rental_reviews",
                ]
            )
            if subject.owner_id == user.pk:
                enabled.append("owner_payouts")
            allowed.extend(cycle_actions(user, subject))
    elif isinstance(subject, MaintenanceRequest):
        if not subject.lease.legacy_read_only:
            enabled.append("rental_maintenance")
            allowed.extend(cycle_actions(user, subject))
    elif phase2_ready and isinstance(subject, RentalHandover):
        enabled.append("rental_handovers")
        allowed.extend(handover_actions(user, subject))
    elif phase2_ready and isinstance(
        subject, (MaintenanceRequest, RentalChange, FinalSettlement, RentalDispute)
    ):
        capability = {
            MaintenanceRequest: "rental_maintenance",
            RentalChange: "rental_changes",
            FinalSettlement: "rental_settlement",
            RentalDispute: "rental_disputes",
        }[type(subject)]
        enabled.extend([capability, "rental_disputes"])
        allowed.extend(cycle_actions(user, subject))
        if not subject.lease.legacy_read_only:
            allowed.append("create_rental_dispute")
    elif isinstance(subject, RentInvoice):
        enabled.extend(["rental_center"])
        if subject.lease_id:
            from ..company.tenancy_access import can_pay

            if can_pay(subject.lease, user):
                allowed.append("resolve_checkout")
        if checkout_available():
            enabled.append("rent_checkout")
            if invoice_payment_allowed(user, subject):
                allowed.extend(["quote", "checkout"])
    elif isinstance(subject, PaymentAttempt):
        enabled.extend(["rental_center", "rent_checkout"])
        if subject.payer_id == user.pk:
            allowed.append("reconcile")
        if phase2_ready:
            enabled.append("rental_settlement")
            allowed.extend(cycle_actions(user, subject))
    elif isinstance(subject, (User, Property, RentalInterest)):
        # Interest requests only persist local state and notify participants.
        # Signing and payments must not control access to this workflow.
        enabled.append("rental_interests")
        if phase2_ready:
            enabled.append("rental_agreements")
        if isinstance(subject, RentalInterest):
            allowed.extend(interest_actions(user, subject))
        elif isinstance(subject, Property) and not interest_creation_blocker(
            user, subject
        ):
            allowed.append("create_rental_interest")
    elif phase2_ready and isinstance(subject, (TermsProposal, OwnerPaymentProfile)):
        enabled.extend(["rental_interests", "rental_agreements"])
        if isinstance(subject, OwnerPaymentProfile):
            enabled.append("owner_payouts")
    elif isinstance(subject, TenancyInvitation):
        can_revoke = can_revoke_invitation(user, subject)
        # Revocation only changes local invitation state; signing/payment
        # provider availability must not prevent an owner from withdrawing it.
        if phase2_ready or can_revoke:
            enabled.append("rental_agreements")
        if can_revoke:
            allowed.append("revoke_invitation")
        if (
            phase2_ready
            and can_revoke
            and subject.status == TenancyInvitation.Status.ACCEPTED
        ):
            allowed.append("create_lease")

    if phase2_ready:
        if isinstance(subject, OwnerPaymentProfile):
            if subject.status != OwnerPaymentProfile.Status.READY:
                allowed.append("onboard_beneficiary")
        elif isinstance(subject, User):
            allowed.append("onboard")
        elif isinstance(subject, TermsProposal):
            allowed.extend(proposal_actions(user, subject))

    if isinstance(subject, Lease):
        from ..reputation.eligibility import can_review_lease

        if can_review_lease(subject, user):
            enabled.append("rental_reviews")
            allowed.append("review_rental")

    from ..rental_lifecycle.capabilities import lifecycle_capabilities

    extension_enabled, extension_actions = lifecycle_capabilities(user, subject)
    enabled.extend(extension_enabled)
    allowed.extend(extension_actions)
    if not user.is_active or not user.is_verified:
        blocking.append("A verified active account is required.")
        enabled = []
        allowed = []
    elif requested_action and requested_action not in allowed:
        reason = (
            interest_creation_blocker(user, subject)
            if isinstance(subject, Property)
            and requested_action == "create_rental_interest"
            else None
        )
        blocking.append(reason or "The requested rental action is not available yet.")

    return {
        "account_id": str(user.id),
        "account_verified": bool(user.is_active and user.is_verified),
        "enabled_capabilities": list(dict.fromkeys(enabled)),
        "policy_version": POLICY_VERSION,
        "allowed_actions": list(dict.fromkeys(allowed)),
        "blocking_reasons": blocking,
    }


def private_no_store(response):
    response["Cache-Control"] = "private, no-store"
    response["Pragma"] = "no-cache"
    return response
