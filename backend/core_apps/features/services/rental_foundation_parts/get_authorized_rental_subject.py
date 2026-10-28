"""Rental foundation: get authorized rental subject."""

import uuid
from rest_framework.exceptions import NotFound
from core_apps.properties.models import Property, PropertyVisit
from ...models import (
    ChangeSigningSession,
    CheckoutSession,
    Lease,
    OwnerOnboardingSession,
    OwnerBeneficiarySubmission,
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


POLICY_VERSION = "rental-policy-v1"


def get_authorized_rental_subject(user, subject_id):
    """Resolve a rental subject without revealing unrelated private resources."""
    try:
        subject_id = uuid.UUID(str(subject_id))
    except (TypeError, ValueError, AttributeError):
        raise NotFound()
    if str(user.id) == str(subject_id):
        return user
    from ..company.access import company_subject, authority_review_subject

    corporate = company_subject(user, subject_id) or authority_review_subject(
        user, subject_id
    )
    if corporate:
        return corporate
    from ..student_housing.access import student_subject

    academic = student_subject(user, subject_id)
    if academic:
        return academic
    from ..rental_lifecycle.access import lifecycle_subject

    extension = lifecycle_subject(user, subject_id)
    if extension:
        return extension

    # Session/quote receipts identify the created resource, not its parent.
    # Resolve these private results when reconciling an uncertain creation.
    for model, actor_filter in (
        (OwnerBeneficiarySubmission, {"profile__owner": user}),
        (OwnerOnboardingSession, {"owner_profile__owner": user}),
        (SigningSession, {"signer": user}),
        (ChangeSigningSession, {"signer": user}),
        (CheckoutSession, {"payer": user}),
        (PaymentQuote, {"invoice__lease__tenant": user}),
    ):
        item = model.objects.filter(id=subject_id, **actor_filter).first()
        if item:
            lease = (
                item.lease
                if isinstance(item, SigningSession)
                else (
                    item.change.lease
                    if isinstance(item, ChangeSigningSession)
                    else (
                        item.invoice.lease
                        if isinstance(item, (CheckoutSession, PaymentQuote))
                        else None
                    )
                )
            )
            if lease and lease.renter_company_id:
                from ..company.tenancy_access import commercial_read, financial_read

                if not (
                    financial_read(lease, user)
                    if isinstance(item, (CheckoutSession, PaymentQuote))
                    else commercial_read(lease, user)
                ):
                    raise NotFound()
            return item

    quote = PaymentQuote.objects.filter(
        id=subject_id, invoice__lease__renter_company__isnull=False
    ).first()
    if quote:
        from ..company.tenancy_access import commercial_read, financial_read

        if financial_read(quote.invoice.lease, user):
            return quote
        raise NotFound()

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
        from ..company.tenancy_access import commercial_read, financial_read

        from ..company.tenancy_access import roles

        if (
            commercial_read(lease, user)
            or lease.renter_company_id
            and roles(lease.company_tenancy, user) & {"coordinator", "payer"}
        ):
            return lease
        raise NotFound()

    invoice = (
        RentInvoice.objects.filter(id=subject_id, purpose="rent")
        .select_related("lease__owner", "lease__tenant")
        .first()
    )
    if invoice:
        from ..company.tenancy_access import commercial_read, financial_read

        if invoice.beneficiary_id == user.pk or financial_read(invoice.lease, user):
            return invoice
        raise NotFound()

    attempt = (
        PaymentAttempt.objects.filter(id=subject_id, invoice__purpose="rent")
        .select_related("invoice__lease__owner", "invoice__lease__tenant")
        .first()
    )
    if attempt:
        from ..company.tenancy_access import commercial_read, financial_read

        if attempt.invoice.beneficiary_id == user.pk or financial_read(
            attempt.invoice.lease, user
        ):
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
            if isinstance(item, RentalEvidence) and item.purpose == "student":
                if item.uploader_id == user.pk and not item.deleted_at:
                    return item
                raise NotFound()
            from ..company.tenancy_access import commercial_read, financial_read

            if item.lease.renter_company_id and isinstance(item, RentalEvidence):
                from ..company.role_evidence import can_read

                if can_read(item, user):
                    return item
                raise NotFound()
            if item.lease.renter_company_id:
                from ..company.tenancy_access import roles

                current = roles(item.lease.company_tenancy, user)
                if isinstance(item, RentalDocument):
                    finance = item.document_type in {
                        "receipt",
                        "settlement",
                        "statement",
                    }
                    if (
                        financial_read(item.lease, user)
                        if finance
                        else commercial_read(item.lease, user)
                    ):
                        return item
                elif isinstance(
                    item, (FinalSettlement, RefundRequest, DepositAgreement)
                ):
                    if financial_read(item.lease, user):
                        return item
                elif isinstance(item, RentalChange):
                    # Company continuation signatures use the canonical rental
                    # change ID. Recovery reveals identity only to its signer.
                    if current & {"owner", "signer"}:
                        return item
                elif "owner" in current:
                    return item
                raise NotFound()
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

    from ..planning_access import planning_subject

    return planning_subject(user, subject_id)
