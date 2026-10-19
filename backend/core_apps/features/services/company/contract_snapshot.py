"""Rebuild the exact reviewed source; never infer allocation or signatures."""

from collections import Counter
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from ...company_models import CompanyMembership, CompanyBudgetReservation
from ...company_contract_models import CompanyMandate
from ..rental_phase2 import RentalConflict
from . import approval_routing, offers, mandates


def people_for(item):
    approval_routing.validate_staff_plan(item)
    people = {str(p.id): p for p in item.occupants.all()}
    for staff in item.planned_staff.select_related("membership__user"):
        if not staff.membership_id:
            raise RentalConflict(
                "Activate every named employee before preparing the contract.",
                code="employee_activation_required",
            )
        people[str(staff.membership.user.id)] = staff.membership.user
    result = []
    for identity, person in sorted(people.items()):
        member = CompanyMembership.objects.filter(
            company=item.request.company, user=person, is_active=True, is_employee=True
        ).first()
        staff = getattr(member, "staff_record", None) if member else None
        if (
            not member
            or not person.is_active
            or not person.is_verified
            or person.sensitive_actions_frozen
            or (staff and staff.employment_status != "active")
        ):
            raise RentalConflict(
                "Every named occupant needs current employee access and an active verified account.",
                code="employee_activation_required",
            )
        result.append(
            {
                "id": identity,
                "name": person.get_full_name,
                "membership_id": str(member.id),
                "membership_revision": member.revision,
                "security_epoch": person.security_epoch,
                "staff_revision": staff.proposal_revision if staff else None,
            }
        )
    if not result:
        raise RentalConflict(
            "Select named employees before preparing a company contract.",
            code="named_employees_required",
        )
    return result


def source(item, signer_id, payer_id, placements, *, cycle, lock=False):
    company = item.request.company
    now = timezone.now()
    if item.lease_id or item.invitation_id or item.status not in {"approved", "held"}:
        raise RentalConflict(
            "Review an approved uncommitted company package.", code="package_closed"
        )
    if (
        company.review_status != "verified"
        or not company.reviewed_by_id
        or not company.review_reference
    ):
        raise RentalConflict(
            "Complete the company authority review first.",
            code="company_review_required",
        )
    if item.quote_expires_at <= now:
        raise RentalConflict(
            "Obtain a new quote and approval before continuing.", code="quote_expired"
        )
    if item.request.starts_on < timezone.localdate():
        raise RentalConflict(
            "Review current arrival dates before continuing.", code="dates_expired"
        )
    if not item.offer.owner.is_active or not item.offer.owner.is_verified:
        raise RentalConflict(
            "The current owner must have active verified access.",
            code="owner_unavailable",
        )
    approval_routing.require_independent(item.assigned_approver, item)
    if item.assigned_approver.user_id == item.offer.owner_id:
        raise RentalConflict(
            "The property owner cannot approve the renting company's package.",
            code="independent_approver_required",
        )
    approval = item.approvals.filter(
        decision="approved",
        commercial_revision=item.commercial_revision,
        snapshot_digest=item.snapshot_digest,
        expires_at__gt=now,
        approver_id=item.assigned_approver.user_id,
    ).first()
    if (
        not approval
        or not CompanyBudgetReservation.objects.filter(
            item=item, approval=approval, status="reserved"
        ).exists()
    ):
        raise RentalConflict(
            "A current independent budget approval is required.",
            code="approval_required",
        )
    if item.hold_id and (item.hold.status != "active" or item.hold.expires_at <= now):
        raise RentalConflict(
            "The inventory hold expired. Withdraw and obtain a current package.",
            code="hold_expired",
        )
    props = offers.resolve_scope(item.offer, lock=lock)
    current = offers.scope_snapshot(item.offer, props)
    if item.offer.status != "published" or any(
        item.snapshot.get(k) != v for k, v in current.items()
    ):
        raise RentalConflict(
            "Inventory or commercial terms changed. Review a new package.",
            code="offer_changed",
        )
    people = people_for(item)
    normal = sorted(
        [
            {"employee_id": str(p["employee_id"]), "property_id": str(p["property_id"])}
            for p in placements
        ],
        key=lambda p: p["employee_id"],
    )
    if len(normal) != len(people) or {p["employee_id"] for p in normal} != {
        p["id"] for p in people
    }:
        raise ValidationError(
            "Assign each named employee exactly once; do not add unapproved occupants."
        )
    properties = {str(p.id): p for p in props}
    counts = Counter(p["property_id"] for p in normal)
    if any(
        identity not in properties
        or properties[identity].occupancy_capacity is None
        or count > properties[identity].occupancy_capacity
        for identity, count in counts.items()
    ):
        raise ValidationError(
            "Choose selected units with sufficient explicitly recorded capacity."
        )
    exposure = item.full_term_rent_minor + item.deposit_minor
    selected = []
    for identity, kind in [(signer_id, "sign"), (payer_id, "pay")]:
        mandate = get_object_or_404(
            CompanyMandate.objects.select_related("membership__user"),
            id=identity,
            company=company,
        )
        if not mandates.current(mandate, kind=kind, exposure=exposure):
            raise RentalConflict(
                "Choose current independently approved signing and payment mandates covering the full exposure.",
                code="mandate_unavailable",
            )
        if mandate.membership.user_id == item.offer.owner_id:
            raise RentalConflict(
                "The property owner cannot represent the renting company in this package.",
                code="independent_representative_required",
            )
        selected.append(mandate)
    signer, payer = selected
    actors = [
        item.request.coordinator,
        item.offer.owner,
        item.assigned_approver.user,
        signer.membership.user,
        payer.membership.user,
    ]
    if any(
        not actor.is_active or not actor.is_verified or actor.sensitive_actions_frozen
        for actor in actors
    ):
        raise RentalConflict(
            "Restore active account authority before approving this company plan.",
            code="security_review_required",
        )
    return {
        "cycle": cycle,
        "actor_security_epochs": {
            str(actor.id): actor.security_epoch for actor in actors
        },
        "company_id": str(company.id),
        "company_name": company.name,
        "company_revision": company.revision,
        "company_registration": company.registration_number,
        "renter_kind": "company",
        "payer_kind": "company",
        "employees_are_debtors": False,
        "booking_id": str(item.id),
        "booking_digest": item.snapshot_digest,
        "request_commercial_revision": item.request.commercial_revision,
        "coordinator_id": str(item.request.coordinator.id),
        "approval_id": str(approval.id),
        "approver_id": str(approval.approver.id),
        "approver_revision": item.assigned_approver.revision,
        "owner_id": str(item.offer.owner.id),
        "signer_id": str(signer.membership.user.id),
        "payer_id": str(payer.membership.user.id),
        "signer_name": signer.membership.user.get_full_name,
        "payer_name": payer.membership.user.get_full_name,
        "signer_mandate_id": str(signer.id),
        "signer_mandate_revision": signer.revision,
        "payer_mandate_id": str(payer.id),
        "payer_mandate_revision": payer.revision,
        "people": people,
        "placements": normal,
        "inventory": current,
        "starts_on": str(item.request.starts_on),
        "ends_on_exclusive": str(item.request.ends_on_exclusive),
        "full_term_rent_minor": item.full_term_rent_minor,
        "deposit_minor": item.deposit_minor,
        "currency": "EGP",
        "exponent": 2,
        "quote_expires_at": item.quote_expires_at.isoformat(),
    }


def revalidate(item, *, lock=False):
    current = source(
        item.booking,
        item.signer_mandate.id,
        item.payer_mandate.id,
        item.snapshot["placements"],
        cycle=item.snapshot["cycle"],
        lock=lock,
    )
    if current != item.snapshot:
        raise RentalConflict(
            "People, mandates or approved source changed. Prepare a fresh review cycle.",
            code="preparation_changed",
        )


def required(snapshot):
    return [
        (snapshot["owner_id"], "owner"),
        (snapshot["signer_id"], "signer"),
        (snapshot["payer_id"], "payer"),
        *[(p["employee_id"], "employee") for p in snapshot["placements"]],
    ]
