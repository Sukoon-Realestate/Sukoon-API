import uuid

from rest_framework.exceptions import NotFound

from core_apps.properties.models import Property, PropertyVisit
from core_apps.users.models import User
from ..models import (
    ChangeSigningSession,
    CheckoutSession,
    Lease,
    OwnerOnboardingSession,
    OwnerPaymentProfile,
    RentalInterest,
    RentInvoice,
    PaymentAttempt,
    PaymentQuote,
    RentalEvidence,
    RentalHandover,
    DepositAgreement,
    RentalPayout,
    MaintenanceRequest,
    RentalChange,
    FinalSettlement,
    RefundRequest,
    RentalDispute,
    RentalDocument,
    RentalReview,
    TenancyInvitation,
    TermsProposal,
    SigningSession,
)
from ..providers import checkout_available, fake_provider_available
from .cycle_permissions import cycle_actions
from .lease_permissions import (
    agreement_actions,
    can_revoke_invitation,
    handover_actions,
    interest_actions,
    proposal_actions,
)
from .rental_phase3 import invoice_payment_allowed


POLICY_VERSION = "rental-policy-v1"


def get_authorized_rental_subject(user, subject_id):
    """Resolve a rental subject without revealing unrelated private resources."""
    try:
        subject_id = uuid.UUID(str(subject_id))
    except (TypeError, ValueError, AttributeError):
        raise NotFound()
    if str(user.id) == str(subject_id):
        return user

    # Session/quote receipts identify the created resource, not its parent.
    # Resolve these private results when reconciling an uncertain creation.
    for model, actor_filter in (
        (OwnerOnboardingSession, {"owner_profile__owner": user}),
        (SigningSession, {"signer": user}),
        (ChangeSigningSession, {"signer": user}),
        (CheckoutSession, {"payer": user}),
        (PaymentQuote, {"invoice__lease__tenant": user}),
    ):
        item = model.objects.filter(id=subject_id, **actor_filter).first()
        if item:
            return item

    owner_profile = OwnerPaymentProfile.objects.filter(id=subject_id).first()
    if owner_profile:
        if owner_profile.owner_id == user.pk:
            return owner_profile
        raise NotFound()

    interest = (
        RentalInterest.objects.filter(id=subject_id)
        .select_related("tenant", "property__owner")
        .first()
    )
    if interest:
        if user in (interest.tenant, interest.property.owner):
            return interest
        raise NotFound()

    proposal = (
        TermsProposal.objects.filter(id=subject_id)
        .select_related("owner", "interest__tenant")
        .first()
    )
    if proposal:
        if user in (proposal.owner, proposal.interest.tenant):
            return proposal
        raise NotFound()

    lease = (
        Lease.objects.filter(id=subject_id).select_related("owner", "tenant").first()
    )
    if lease:
        if user in (lease.owner, lease.tenant):
            return lease
        raise NotFound()

    invoice = (
        RentInvoice.objects.filter(id=subject_id)
        .select_related("lease__owner", "lease__tenant")
        .first()
    )
    if invoice:
        if user in (invoice.lease.owner, invoice.lease.tenant):
            return invoice
        raise NotFound()

    attempt = (
        PaymentAttempt.objects.filter(id=subject_id)
        .select_related("invoice__lease__owner", "invoice__lease__tenant")
        .first()
    )
    if attempt:
        if user in (attempt.invoice.lease.owner, attempt.invoice.lease.tenant):
            return attempt
        raise NotFound()

    for model in (
        RentalEvidence,
        RentalHandover,
        DepositAgreement,
        RentalPayout,
        MaintenanceRequest,
        RentalChange,
        FinalSettlement,
        RefundRequest,
        RentalDispute,
        RentalDocument,
        RentalReview,
    ):
        item = (
            model.objects.filter(id=subject_id)
            .select_related("lease__owner", "lease__tenant")
            .first()
        )
        if item:
            if user in (item.lease.owner, item.lease.tenant):
                return item
            raise NotFound()

    invitation = (
        TenancyInvitation.objects.filter(id=subject_id)
        .select_related("owner", "tenant")
        .first()
    )
    if invitation:
        if user in (invitation.owner, invitation.tenant):
            return invitation
        raise NotFound()

    property_obj = (
        Property.objects.filter(id=subject_id).select_related("owner").first()
    )
    if property_obj:
        is_participant = (
            (
                property_obj.status == Property.Status.VERIFIED
                and property_obj.is_verified
            )
            or property_obj.owner_id == user.pk
            or PropertyVisit.objects.filter(property=property_obj, tenant=user).exists()
            or TenancyInvitation.objects.filter(
                property=property_obj, tenant=user
            ).exists()
            or Lease.objects.filter(property=property_obj, tenant=user).exists()
        )
        if is_participant:
            return property_obj
        raise NotFound()

    from .planning_access import planning_subject

    return planning_subject(user, subject_id)


def capabilities_for(user, subject, requested_action=""):
    """Return only capabilities backed by the current operational implementation."""
    enabled = []
    allowed = []
    blocking = []

    phase2_ready = fake_provider_available()
    if isinstance(subject, Lease):
        allowed.extend(agreement_actions(user, subject))
        enabled.append("rental_center")
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
    elif phase2_ready and isinstance(subject, (RentalInterest, TermsProposal)):
        enabled.extend(["rental_interests", "rental_agreements"])
    elif phase2_ready and isinstance(subject, (User, Property, OwnerPaymentProfile)):
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
        elif isinstance(subject, Property):
            if (
                subject.owner_id != user.pk
                and subject.is_verified
                and subject.status == Property.Status.VERIFIED
            ):
                allowed.append("create_rental_interest")
        elif isinstance(subject, RentalInterest):
            allowed.extend(interest_actions(user, subject))
        elif isinstance(subject, TermsProposal):
            allowed.extend(proposal_actions(user, subject))

    if not user.is_active or not user.is_verified:
        blocking.append("A verified active account is required.")
        enabled = []
        allowed = []
    elif requested_action and requested_action not in allowed:
        blocking.append("The requested rental action is not available yet.")

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
