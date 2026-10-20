"""Canonical company agreements; signatures and captures are independent facts."""

from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from ...models import (
    CompanyTenancy,
    CompanyMandate,
    CompanyMembership,
    CompanyLeaseBinding,
    EmployeeAssignment,
    Lease,
    SigningSession,
    ReservationHold,
    CompanyBudgetReservation,
    RentalInventoryDayLock,
)
from ...providers import get_rental_provider, require_rental_provider
from ..rental_phase2 import RentalConflict, fingerprint, ensure_policy
from ..rental_lifecycle.common import require_revision, require_staff, audit
from . import tenancy_access as access, contract_access, contract_snapshot


@transaction.atomic
def verify_mandate(user, identity, data):
    from core_apps.users.models import User
    from core_apps.admin_api.models import StaffProfile

    user = User.objects.select_for_update(no_key=True).get(pk=user.pk)
    StaffProfile.objects.select_for_update().filter(user=user).first()
    if user.sensitive_actions_frozen:
        raise PermissionDenied(
            "Recover operator authority before granting execution rights."
        )
    initial = get_object_or_404(CompanyMandate, id=identity)
    from ...models import Company

    Company.objects.select_for_update().get(pk=initial.company_id)
    item = CompanyMandate.objects.select_for_update().get(pk=initial.pk)
    require_staff(
        user, {"kyc_reviewer"} if item.kind == "sign" else {"financial_approver"}
    )
    require_revision(item, data["expected_revision"])
    if (
        user.pk in {item.proposed_by_id, item.reviewed_by_id, item.membership.user_id}
        or CompanyMembership.objects.filter(company=item.company, user=user).exists()
    ):
        raise PermissionDenied(
            "An independent operator must verify company execution authority."
        )
    if (
        data["verified_until"] <= timezone.now()
        or data["verified_until"] > item.valid_until
    ):
        raise RentalConflict(
            "Verification must expire within the original mandate period."
        )
    from .mandates import current

    if not current(item):
        raise RentalConflict("Only a current approved mandate can be verified.")
    item.execution_reviewed_by = user
    item.execution_reference = data["evidence_reference"]
    item.execution_verified_until = data["verified_until"]
    item.revision += 1
    item.save()
    audit(
        item,
        user,
        "company_execution_authority_verified",
        data["reason"],
        {
            "reference": item.execution_reference,
            "until": item.execution_verified_until.isoformat(),
        },
    )
    from .mandates import notify

    notify(item)
    return item


@transaction.atomic
def create(user, identity, data):
    from .access import require_new_business

    require_new_business()
    preparation = contract_access.get(user, identity, lock=True)
    if not contract_access.manages(preparation, user):
        raise PermissionDenied(
            "The assigned coordinator must create the company agreement."
        )
    require_revision(preparation, data["expected_revision"])
    if preparation.state != "reviews_complete" or hasattr(preparation, "tenancy"):
        raise RentalConflict(
            "Complete the current participant reviews before creating an agreement."
        )
    contract_snapshot.revalidate(preparation, lock=True)
    exposure = (
        preparation.snapshot["full_term_rent_minor"]
        + preparation.snapshot["deposit_minor"]
    )
    if not all(
        access.execution_mandate(m, exposure=exposure)
        for m in [preparation.signer_mandate, preparation.payer_mandate]
    ):
        raise RentalConflict(
            "Verify both execution mandates, then refresh participant reviews before creating the agreement.",
            code="execution_authority_required",
        )
    booking = preparation.booking
    if booking.request.coordinator_id == booking.offer.owner_id:
        raise PermissionDenied(
            "Assign a company coordinator distinct from the property owner before contracting."
        )
    from .assignment_locks import lock_people, require_available

    lock_people(p["employee_id"] for p in preparation.snapshot["placements"])
    for place in preparation.snapshot["placements"]:
        member = CompanyMembership.objects.get(
            company=booking.request.company, user__id=place["employee_id"]
        )
        require_available(
            member.user, booking.request.starts_on, booking.request.ends_on_exclusive
        )
    if (
        not booking.hold_id
        or booking.hold.status != "active"
        or booking.hold.expires_at <= timezone.now()
    ):
        raise RentalConflict(
            "Reserve the exact reviewed units before creating the agreement.",
            code="hold_expired",
        )
    hold = ReservationHold.objects.select_for_update().get(pk=booking.hold_id)
    snapshot = preparation.snapshot
    props = [u["id"] for u in snapshot["inventory"]["units"]]
    from core_apps.properties.models import Property

    properties = list(Property.objects.filter(id__in=props).order_by("pkid"))
    policy = ensure_policy()
    terms = {
        "business_policies": booking.snapshot.get("business_policies", {}),
        "renter_kind": "company",
        "renter_company_id": snapshot["company_id"],
        "renter_company_name": snapshot["company_name"],
        "renter_registration": snapshot["company_registration"],
        "payer_kind": "company",
        "employees_are_debtors": False,
        "owner_id": snapshot["owner_id"],
        "signer_id": snapshot["signer_id"],
        "starts_on": snapshot["starts_on"],
        "ends_on_exclusive": snapshot["ends_on_exclusive"],
        "rent": booking.snapshot["monthly_rent"],
        "deposit": {
            "amount_minor": booking.deposit_minor,
            "currency": "EGP",
            "exponent": 2,
        },
        "deposit_holder": "platform",
        "billing_anchor_day": booking.request.starts_on.day,
        "handover_on": snapshot["starts_on"],
        "portfolio": snapshot["inventory"],
        "placements": snapshot["placements"],
        "policy_version": policy.version,
    }
    from ..platform_rent_payments import reviewed_terms

    terms = reviewed_terms(terms)
    lease = Lease.objects.create(
        property=properties[0],
        owner=booking.offer.owner,
        tenant=None,
        renter_company=booking.request.company,
        template_id="company-rental",
        template_version="1",
        start_date=booking.request.starts_on,
        end_date=booking.request.ends_on_exclusive,
        rent_amount_minor=booking.snapshot["monthly_rent"]["amount_minor"],
        legacy_read_only=False,
        offer_id=str(booking.offer.id),
        offer_snapshot={"rental_scope": "entire_property", "company_unit_ids": props},
        terms=terms,
        policy_version=policy.version,
        hold_expires_at=hold.expires_at,
    )
    item = CompanyTenancy.objects.create(
        lease=lease,
        preparation=preparation,
        coordinator=booking.request.coordinator,
        signer_mandate=preparation.signer_mandate,
        payer_mandate=preparation.payer_mandate,
        source_snapshot=snapshot,
        terms_digest=fingerprint(terms),
    )
    hold.lease = lease
    hold.revision += 1
    hold.save()
    hold.day_locks.update(lease=lease)
    booking.lease, booking.status = lease, "contracting"
    booking.revision += 1
    booking.save()
    for place in snapshot["placements"]:
        EmployeeAssignment.objects.create(
            item=booking,
            employee_id=get_object_or_404(
                CompanyMembership,
                company=booking.request.company,
                user__id=place["employee_id"],
            ).user_id,
            property=Property.objects.get(id=place["property_id"]),
            starts_on=lease.start_date,
            ends_on_exclusive=lease.end_date,
            acknowledgment="accepted",
            acknowledged_revision=1,
        )
    preparation.state = "agreement_created"
    preparation.revision += 1
    preparation.save()
    audit(
        lease,
        user,
        "company_agreement_created",
        metadata={"terms_digest": item.terms_digest},
    )
    access.notify(item)
    return item


def validate_unsigned(item):
    """No silent re-use of a review after corporate/actor/source authority changes."""
    lease, source = item.lease, item.source_snapshot
    company = lease.renter_company
    if (
        company.review_status != "verified"
        or company.revision != source["company_revision"]
    ):
        raise RentalConflict(
            "Company authority changed. Cancel this unsigned draft and review a new package."
        )
    for mandate, kind in [(item.signer_mandate, "sign"), (item.payer_mandate, "pay")]:
        if (
            not access.execution_mandate(
                mandate,
                exposure=source["full_term_rent_minor"] + source["deposit_minor"],
            )
            or mandate.revision
            != source[("signer" if kind == "sign" else "payer") + "_mandate_revision"]
        ):
            raise RentalConflict(
                "Current verified authority and a fresh participant review are required.",
                code="execution_authority_required",
            )
    from core_apps.users.models import User

    for identity, epoch in source["actor_security_epochs"].items():
        if not User.objects.filter(
            id=identity,
            is_active=True,
            is_verified=True,
            sensitive_actions_frozen=False,
            security_epoch=epoch,
        ).exists():
            raise RentalConflict(
                "Participant account authority changed. Review a new agreement."
            )
    for employee in source["people"]:
        if not CompanyMembership.objects.filter(
            id=employee["membership_id"],
            company=company,
            is_active=True,
            is_employee=True,
            revision=employee["membership_revision"],
            user__is_active=True,
            user__is_verified=True,
            user__security_epoch=employee["security_epoch"],
            user__sensitive_actions_frozen=False,
        ).exists():
            raise RentalConflict(
                "Employee consent or membership changed. Review a new agreement."
            )
    if any(prop.owner_id != lease.owner_id for prop in access.properties(item)):
        raise RentalConflict("Property ownership changed. Review a new agreement.")
    from ..rental_lifecycle.inventory import hold_coverage

    if (
        not lease.hold_expires_at
        or lease.hold_expires_at <= timezone.now()
        or not hold_coverage(lease)
    ):
        raise RentalConflict("The exact inventory hold expired.", code="hold_expired")


def review(item, user, data):
    role = data["role"]
    if role not in {"owner", "signer"}:
        raise PermissionDenied("Only the two contract parties review the agreement.")
    access.require_role(item, user, {role}, sensitive=True)
    if role == "signer":
        access.require_delegate(item, user, "sign")
    if item.lease.status != "draft" or data["digest"] != item.terms_digest:
        raise RentalConflict("Review the current unsigned company agreement.")
    validate_unsigned(item)
    item.contract_reviews[role] = {
        "actor_id": str(user.id),
        "digest": item.terms_digest,
        "security_epoch": user.security_epoch,
    }
    item.save(update_fields=["contract_reviews", "updated_at"])
    return access.changed(item, user, "company_agreement_reviewed")


def submit(item, user, data):
    access.require_role(item, user, {"owner"}, sensitive=True)
    require_rental_provider(user)
    if item.lease.status != "draft" or set(item.contract_reviews) != {
        "owner",
        "signer",
    }:
        raise RentalConflict(
            "Both contract parties must review the exact company agreement."
        )
    validate_unsigned(item)
    document = get_rental_provider().generate_agreement(
        item.lease.id, item.lease.revision, item.lease.terms
    )
    item.lease.document_id, item.lease.document_hash = (
        document.document_id,
        document.digest,
    )
    item.lease.status = "pending_signatures"
    return access.changed(item, user, "company_signature_requested")


def signing_session(item, user, data):
    access.require_role(item, user, {"owner", "signer"}, sensitive=True)
    require_rental_provider(user)
    if user.pk != item.lease.owner_id:
        access.require_delegate(item, user, "sign")
    lease = item.lease
    if lease.status != "pending_signatures" or data["digest"] != lease.document_hash:
        raise RentalConflict("Review the current signing document.")
    from .tenancy_initial_recovery import pending

    if pending(item):
        raise RentalConflict(
            "Resolve or withdraw the separate agreement release before starting another original signing session."
        )
    validate_unsigned(item)
    if lease.signing_sessions.filter(
        signer=user,
        document_hash=lease.document_hash,
    ).exists():
        raise RentalConflict("Resume or reconcile the original signing session.")

    hosted = get_rental_provider().create_signing_session(
        lease.id, user.id, data["request_key"]
    )
    session = SigningSession.objects.create(
        lease=lease,
        signer=user,
        request_key=data["request_key"],
        lease_revision=lease.revision + 1,
        document_id=lease.document_id,
        document_hash=lease.document_hash,
        provider_session_id=hosted.provider_session_id,
        hosted_url=hosted.hosted_url,
        expires_at=min(
            lease.hold_expires_at,
            timezone.now() + timedelta(minutes=settings.RENTAL_SIGNING_TTL_MINUTES),
        ),
    )
    audit(
        lease,
        user,
        "company_signing_session_created",
        metadata={"session_id": str(session.id)},
    )
    return access.changed(item, user, "company_signing_session_opened")


def complete_signature(session, *, reconcile=False):
    """Retain authenticated facts; manual resume only rechecks a retained fact."""
    initial = session.lease.company_tenancy
    lease = access.lock_lease(initial.lease)
    item = CompanyTenancy.objects.select_for_update().get(pk=initial.pk)
    item.lease = lease
    session = SigningSession.objects.select_for_update().get(pk=session.pk)
    if session.status == "completed":
        return
    if reconcile:
        if session.status != "review_required" or not session.completed_at:
            raise RentalConflict(
                "Only a previously authenticated signature fact can be reconciled."
            )
    elif session.status == "review_required":
        return
    from .tenancy_initial_recovery import pending, applied

    if pending(item) or applied(item):
        # A separate signed release covers the exact original document. Late
        # original events remain facts, never permission to restart the lease.
        session.status = "review_required"
        session.completed_at = session.completed_at or timezone.now()
        session.save()
        access.changed(
            item,
            None,
            "company_original_signature_retained_during_release",
            metadata={
                "session_id": str(session.id),
                "provider_session_id": session.provider_session_id,
                "document_hash": session.document_hash,
            },
        )
        return
    from rest_framework.exceptions import APIException

    failure = ""
    try:
        validate_unsigned(item)
    except APIException as error:
        failure = str(error.detail)
    if (
        lease.status != "pending_signatures"
        or session.expires_at <= timezone.now()
        or session.document_id != lease.document_id
        or session.document_hash != lease.document_hash
    ):
        failure = (
            "The signing result arrived after the reviewed session changed or expired."
        )
    if failure:
        if reconcile:
            # Keep the original provider receipt timestamp and case unchanged.
            # A refresh cannot turn an expired or changed source into approval.
            return
        session.status = "review_required"
        session.completed_at = session.completed_at or timezone.now()
        session.save()
        from ..rental_lifecycle.cases import open_system_case

        open_system_case(
            kind="company_tenancy_review",
            source_key=f"company-signature:{session.id}",
            lease=lease,
            reason=failure,
            next_action="Reconcile the recorded provider signature against the original document and current company authority.",
        )
        access.changed(
            item,
            None,
            "company_signature_needs_reconciliation",
            failure,
            {"session_id": str(session.id), "document_hash": session.document_hash},
        )
        return
    required = {lease.owner_id, item.signer_mandate.membership.user_id}
    if session.signer_id not in required:
        raise PermissionDenied(
            "The signing session is not for a current contract party."
        )
    session.status = "completed"
    session.completed_at = session.completed_at or timezone.now()
    session.save()
    done = set(
        lease.signing_sessions.filter(
            status="completed",
            document_id=lease.document_id,
            document_hash=lease.document_hash,
        ).values_list("signer_id", flat=True)
    )
    if not required.issubset(done):
        access.changed(item, None, "company_party_signature_recorded")
        return
    # Preserve the existing signed-rental initial-payment window; no new fee rule.
    lease.status, lease.hold_expires_at = "signed", timezone.now() + timedelta(hours=48)
    lease.inventory_day_locks.filter(kind="hold").update(
        expires_at=lease.hold_expires_at
    )
    ReservationHold.objects.filter(lease=lease).update(expires_at=lease.hold_expires_at)
    access.changed(item, None, "company_agreement_signed")
    CompanyLeaseBinding.objects.get_or_create(
        lease=lease,
        defaults={
            "booking": item.preparation.booking,
            "renter_company": lease.renter_company,
            "proposed_by": item.preparation.created_by,
            "state": "accepted",
            "source_snapshot": {
                **item.source_snapshot,
                "inventory_snapshot": item.source_snapshot["inventory"],
                "tenant_id": None,
                "document_id": str(lease.document_id),
                "document_hash": lease.document_hash,
            },
            "approvals": item.contract_reviews,
            "accepted_at": timezone.now(),
        },
    )
    from ..rental_phase3 import generate_billing_schedule

    generate_billing_schedule(lease)


def cancel(item, user, data):
    access.require_role(item, user, {"owner", "coordinator"})
    lease = item.lease
    if (
        lease.status not in {"draft", "expired", "pending_signatures"}
        or lease.status == "pending_signatures"
        and lease.signing_sessions.exists()
        or lease.signing_sessions.filter(
            status__in=["pending", "completed", "review_required"]
        ).exists()
        or lease.invoices.exists()
    ):
        raise RentalConflict(
            "A signature, pending signing or money obligation requires reconciliation; it cannot be discarded."
        )
    lease.inventory_day_locks.filter(kind="hold").delete()
    ReservationHold.objects.filter(lease=lease).update(
        status="released", released_at=timezone.now()
    )
    CompanyBudgetReservation.objects.filter(
        item=item.preparation.booking, status="reserved"
    ).update(status="released")
    item.preparation.booking.assignments.update(occupancy_status="cancelled")
    booking = item.preparation.booking
    booking.status = "cancelled"
    booking.revision += 1
    booking.save()
    lease.status = "cancelled"
    from ..rental_phase6 import evaluate_financial_closure

    evaluate_financial_closure(lease, increment_revision=False)
    return access.changed(
        item, user, "company_unsigned_agreement_cancelled", data["reason"]
    )
