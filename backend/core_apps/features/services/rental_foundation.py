import uuid

from django.conf import settings
from rest_framework.exceptions import NotFound

from core_apps.properties.models import Property, PropertyVisit
from core_apps.users.models import User
from ..models import (
    Lease,
    OwnerPaymentProfile,
    RentalInterest,
    RentInvoice,
    PaymentAttempt,
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
)
from ..providers import fake_provider_available


POLICY_VERSION = "rental-policy-v1"


def get_authorized_rental_subject(user, subject_id):
    """Resolve a rental subject without revealing unrelated private resources."""
    try:
        subject_id = uuid.UUID(str(subject_id))
    except (TypeError, ValueError, AttributeError):
        raise NotFound()
    if str(user.id) == str(subject_id):
        return user

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
            property_obj.owner_id == user.pk
            or PropertyVisit.objects.filter(property=property_obj, tenant=user).exists()
            or TenancyInvitation.objects.filter(
                property=property_obj, tenant=user
            ).exists()
            or Lease.objects.filter(property=property_obj, tenant=user).exists()
        )
        if is_participant:
            return property_obj
        raise NotFound()

    # Keep an unknown ID indistinguishable from an unauthorized one.
    raise NotFound()


def capabilities_for(user, subject, requested_action=""):
    """Return only capabilities backed by the current operational implementation."""
    enabled = []
    allowed = []
    blocking = []

    phase2_ready = fake_provider_available()
    if isinstance(subject, Lease):
        enabled.append("rental_center")
        if phase2_ready and not subject.legacy_read_only:
            enabled.append("rental_agreements")
        if phase2_ready and getattr(settings, "RENTAL_CHECKOUT_ENABLED", False):
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
            if subject.status == Lease.Status.ACTIVE:
                allowed.append("create_handover")
    elif isinstance(subject, RentInvoice):
        enabled.extend(["rental_center"])
        if phase2_ready and getattr(settings, "RENTAL_CHECKOUT_ENABLED", False):
            enabled.append("rent_checkout")
            if subject.lease.tenant_id == user.pk and subject.status in {
                RentInvoice.Status.DUE,
                RentInvoice.Status.OVERDUE,
            }:
                allowed.extend(["quote", "checkout"])
    elif isinstance(subject, PaymentAttempt):
        enabled.extend(["rental_center", "rent_checkout"])
        if subject.payer_id == user.pk:
            allowed.append("reconcile")
    elif phase2_ready and isinstance(subject, (RentalInterest, TermsProposal)):
        enabled.extend(["rental_interests", "rental_agreements"])
    elif phase2_ready and isinstance(subject, (User, Property, OwnerPaymentProfile)):
        enabled.extend(["rental_interests", "rental_agreements"])

    if phase2_ready:
        if isinstance(subject, (User, OwnerPaymentProfile)):
            allowed.append("onboard")
        elif isinstance(subject, Property):
            allowed.append(
                "create_terms" if subject.owner_id == user.pk else "create_interest"
            )
        elif isinstance(subject, RentalInterest):
            allowed.append("respond")
            if subject.property.owner_id == user.pk:
                allowed.append("create_terms")
        elif isinstance(subject, TermsProposal):
            allowed.append("respond")
        elif isinstance(subject, Lease) and not subject.legacy_read_only:
            if subject.status == Lease.Status.DRAFT:
                allowed.append("review")
                if subject.owner_id == user.pk:
                    allowed.append("submit_for_signature")
            elif subject.status == Lease.Status.PENDING_SIGNATURES:
                allowed.append("sign")

    if not user.is_active or not user.is_verified:
        blocking.append("A verified active account is required.")
        enabled = []
    elif requested_action and requested_action not in allowed:
        blocking.append("The requested rental action is not available yet.")

    return {
        "account_id": str(user.id),
        "account_verified": bool(user.is_active and user.is_verified),
        "enabled_capabilities": enabled,
        "policy_version": POLICY_VERSION,
        "allowed_actions": allowed,
        "blocking_reasons": blocking,
    }


def private_no_store(response):
    response["Cache-Control"] = "private, no-store"
    response["Pragma"] = "no-cache"
    return response
