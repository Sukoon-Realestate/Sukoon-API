"""Explicit, audited reviews and company controls; no force-payment controls."""

from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from core_apps.properties.models import ResidentialBuilding, ResidentialComplex
from ...company_models import Company, CompanyHousingRequest
from ..rental_lifecycle.common import require_staff, require_revision, audit
from ..rental_phase2 import RentalConflict
from .access import company_for, member_for
from .bookings import _live_reservations


@transaction.atomic
def review(actor, kind, identity, data):
    require_staff(
        actor, {"kyc_reviewer"} if kind == "company" else {"property_reviewer"}
    )
    model = {
        "company": Company,
        "building": ResidentialBuilding,
        "complex": ResidentialComplex,
    }[kind]
    item = get_object_or_404(model.objects.select_for_update(), id=identity)
    require_revision(item, data["expected_revision"])
    if (kind == "company" and item.memberships.filter(user=actor).exists()) or (
        kind != "company" and item.manager_id == actor.pk
    ):
        raise PermissionDenied("An independent reviewer must assess this authority.")
    if kind == "company":
        (
            item.review_status,
            item.review_reference,
            item.reviewed_by,
            item.reviewed_at,
        ) = (data["status"], data["evidence_reference"], actor, timezone.now())
    else:
        item.authority_status, item.authority_reference, item.authority_reviewed_by = (
            data["status"],
            data["evidence_reference"],
            actor,
        )
    item.revision += 1
    item.save()
    audit(
        item,
        actor,
        "company_reviewed" if kind == "company" else "portfolio_authority_reviewed",
        data["reason"],
        metadata={
            "status": data["status"],
            "evidence_reference": data["evidence_reference"],
        },
    )
    return item


@transaction.atomic
def set_budget(user, company_id, data):
    company = company_for(user, company_id, "admin", lock=True)
    require_revision(company, data["expected_revision"])
    totals = _live_reservations(company).aggregate(
        rent=Sum("rent_minor"), deposit=Sum("deposit_minor")
    )
    for name, key in (
        ("budget_limit_minor", "rent"),
        ("deposit_limit_minor", "deposit"),
    ):
        value = data[name]
        if value is not None and value < (totals[key] or 0):
            raise RentalConflict(
                "The new limit cannot exclude existing reservations or commitments.",
                code="budget_exceeded",
            )
        setattr(company, name, value)
    company.revision += 1
    company.save()
    audit(company, user, "company_budget_limits_changed", data["reason"])
    return company


@transaction.atomic
def reassign_coordinator(user, request_id, data):
    item = get_object_or_404(CompanyHousingRequest, id=request_id)
    company_for(user, item.company.id, "admin", lock=True)
    item = CompanyHousingRequest.objects.select_for_update().get(pk=item.pk)
    require_revision(item, data["expected_revision"])
    target = get_object_or_404(
        item.company.memberships.select_related("user"),
        user__id=data["coordinator_id"],
        is_active=True,
        is_coordinator=True,
    )
    member_for(target.user, item.company, "coordinate")
    item.coordinator = target.user
    item.revision += 1
    item.save()
    audit(item, user, "company_coordinator_reassigned", data["reason"])
    return item
