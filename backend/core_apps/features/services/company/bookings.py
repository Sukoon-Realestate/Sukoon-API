from datetime import timedelta
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from ...company_models import (
    Company,
    CompanyMembership,
    CompanyHousingRequest,
    CompanyBookingItem,
    CompanyApproval,
    CompanyBudgetReservation,
    PortfolioOffer,
)
from ...models import ReservationHold
from ..rental_lifecycle.common import audit, require_revision, lifecycle_policy
from ..rental_lifecycle.inventory import (
    allocate_days,
    expire_property_holds,
    assert_available,
)
from ..rental_phase2 import (
    RentalConflict,
    fingerprint,
    ensure_policy,
    assert_owner_ready,
)
from ..rental_lifecycle.reservations import confirmation_current
from ..rental_phase2_parts.remember_mutation import add_months
from .access import company_for, request_for, member_for, require_new_business
from .offers import resolve_scope, scope_snapshot


@transaction.atomic
def save_request(user, company, data):
    require_new_business()
    member_for(user, company, "coordinate")
    fields = (
        "title",
        "purpose",
        "cost_center",
        "location",
        "starts_on",
        "ends_on_exclusive",
        "headcount",
        "commitment_ceiling_minor",
        "deposit_limit_minor",
    )
    item = CompanyHousingRequest.objects.create(
        company=company,
        requester=user,
        coordinator=user,
        **{k: data[k] for k in fields if k in data}
    )
    audit(item, user, "company_housing_request_created")
    from core_apps.chat.services.company_access import provision

    provision(item, user)
    return item


@transaction.atomic
def select_offer(user, request_id, data):
    require_new_business()
    request = request_for(user, request_id, lock=True)
    require_revision(request, data["expected_revision"])
    policy, rules = lifecycle_policy("reservations")
    if (
        request.starts_on < timezone.localdate()
        or not 0
        < (request.ends_on_exclusive - request.starts_on).days
        <= rules["max_booking_days"]
    ):
        raise ValidationError(
            {"ends_on_exclusive": "Choose a supported future rental interval."}
        )
    offer = get_object_or_404(
        PortfolioOffer.objects.select_for_update(),
        id=data["offer_id"],
        status="published",
    )
    require_revision(offer, data["offer_revision"])
    props = resolve_scope(offer, lock=True)
    for prop in props:
        expire_property_holds(prop)
        assert_available(
            prop,
            {"rental_scope": "entire_property"},
            request.starts_on,
            request.ends_on_exclusive + timedelta(days=rules["turnover_days"]),
        )
    months = next(
        (
            n
            for n in range(1, 121)
            if add_months(request.starts_on, n) == request.ends_on_exclusive
        ),
        None,
    )
    if months is None:
        raise ValidationError(
            {
                "ends_on_exclusive": "This offer supports whole monthly billing periods, up to ten years."
            }
        )
    occupants = list(
        CompanyMembership.objects.filter(
            company=request.company,
            is_active=True,
            is_employee=True,
            user__id__in=data["occupant_ids"],
        ).select_related("user")
    )
    if len(occupants) != len(set(data["occupant_ids"])):
        raise ValidationError(
            {
                "occupant_ids": "Every initial occupant must be an active employee member."
            }
        )
    snapshot = scope_snapshot(offer, props)
    from ...company_staff_models import CompanyStaffRecord

    planned_staff = list(
        CompanyStaffRecord.objects.filter(
            company=request.company,
            id__in=data.get("staff_ids", []),
            employment_status="active",
        ).select_related("membership__user")
    )
    if len(planned_staff) != len(set(data.get("staff_ids", []))) or any(
        "employee" not in row.proposed_roles for row in planned_staff
    ):
        raise ValidationError(
            {"staff_ids": "Choose active company staff with employee eligibility."}
        )
    if any(
        row.membership_id
        and (
            not row.membership.is_active
            or not row.membership.is_employee
            or row.membership.user_id in {m.user_id for m in occupants}
        )
        for row in planned_staff
    ):
        raise ValidationError(
            {"staff_ids": "Do not duplicate or include inactive employee memberships."}
        )
    initial_places = len(occupants) + len(planned_staff)
    if snapshot["capacity"] is None:
        raise RentalConflict(
            "Confirm the registered accommodation capacity before requesting approval.",
            code="capacity_unknown",
        )
    if initial_places > snapshot["capacity"]:
        raise ValidationError(
            {"occupant_ids": "The selected accommodation has insufficient capacity."}
        )
    if (
        offer.occupancy_policy != "reserve_capacity_with_notice"
        and initial_places < snapshot["capacity"]
    ):
        raise RentalConflict(
            "This offer requires named occupants. Choose an offer permitting reserve capacity or identify its occupants.",
            code="occupants_required",
        )
    commercial = ensure_policy()
    if not commercial.is_active or (
        commercial.commission_rate_bps,
        commercial.commission_payer,
        commercial.commission_basis,
        commercial.processing_fee_payer,
        commercial.renewal_commission_rate_bps,
        commercial.currency,
        commercial.exponent,
        commercial.billing_cycle,
        commercial.timezone,
    ) != (
        1000,
        "owner",
        "first_period_base_rent",
        "platform",
        0,
        "EGP",
        2,
        "monthly",
        "Africa/Cairo",
    ):
        raise RentalConflict(
            "The supported commercial policy must be configured before quoting.",
            code="policy_not_configured",
        )
    snapshot.update(
        company_id=str(request.company.id),
        company_name=request.company.name,
        requester_id=str(request.requester.id),
        requester_name=request.requester.get_full_name,
        purpose=request.purpose,
        starts_on=str(request.starts_on),
        ends_on_exclusive=str(request.ends_on_exclusive),
        occupant_ids=sorted(str(m.user.id) for m in occupants),
        occupants=[
            {"user_id": str(m.user.id), "name": m.user.get_full_name}
            for m in sorted(occupants, key=lambda m: str(m.user.id))
        ],
        planned_staff=[
            {
                "staff_id": str(row.id),
                "name": row.display_name,
                "activation_required": not bool(row.membership_id),
                "proposal_revision": row.proposal_revision,
            }
            for row in sorted(planned_staff, key=lambda row: str(row.id))
        ],
        reserve_places=snapshot["capacity"] - initial_places,
        full_term_rent_minor=months * offer.monthly_rent_minor,
        policy_version=commercial.version,
        lifecycle_policy_version=policy.version,
        lifecycle_rules=rules,
        tenant_funding="company_100_percent",
        owner_commission_basis_points=1000,
        commission_period="first_base_rent_period",
        processing_fee_payer="platform",
        renewal_commission_basis_points=0,
    )
    item = CompanyBookingItem.objects.create(
        request=request,
        offer=offer,
        snapshot=snapshot,
        snapshot_digest=fingerprint(snapshot),
        quote_expires_at=timezone.now() + timedelta(hours=24),
        full_term_rent_minor=snapshot["full_term_rent_minor"],
        deposit_minor=offer.deposit_minor,
    )
    item.occupants.set(m.user for m in occupants)
    item.planned_staff.set(planned_staff)
    request.revision += 1
    request.save()
    audit(item, user, "company_package_proposed")
    return item


def _live_reservations(company):
    # An expired approval can only release uncommitted obligations.
    company.budget_reservations.filter(
        status="reserved",
        approval__expires_at__lte=timezone.now(),
        item__lease__isnull=True,
    ).update(status="released")
    return company.budget_reservations.filter(status__in=["reserved", "committed"])


@transaction.atomic
def decide(user, item_id, data):
    require_new_business()
    item = get_object_or_404(CompanyBookingItem, id=item_id)
    company = company_for(user, item.request.company.id, "approve", lock=True)
    item = (
        CompanyBookingItem.objects.select_for_update()
        .select_related("request")
        .get(pk=item.pk)
    )
    require_revision(item, data["expected_revision"])
    if item.status != "approval_pending":
        raise RentalConflict(
            "Only a current proposed package can receive a decision.",
            code="package_closed",
        )
    from .approval_routing import require_independent, validate_staff_plan

    if not item.assigned_approver_id or item.assigned_approver.user_id != user.pk:
        raise PermissionDenied(
            "Only the currently assigned approver can decide this package."
        )
    if (
        item.request.requester_id == user.pk
        or item.request.items.filter(occupants=user).exists()
    ):
        raise PermissionDenied(
            "An independent approver must decide this accommodation package."
        )
    require_independent(item.assigned_approver, item)
    validate_staff_plan(item)
    if data["decision"] not in {"approved", "rejected", "changes_requested"} or (
        data["decision"] != "approved" and not data.get("reason", "").strip()
    ):
        raise ValidationError({"reason": "Explain the rejection or requested changes."})
    if item.approvals.filter(commercial_revision=item.commercial_revision).exists():
        raise RentalConflict(
            "This commercial revision already has a decision.", code="decision_exists"
        )
    if item.quote_expires_at <= timezone.now():
        raise RentalConflict(
            "Obtain a fresh quote before approval.", code="quote_expired"
        )
    if data["snapshot_digest"] != item.snapshot_digest:
        raise RentalConflict(
            "Review the exact current commercial package.", code="stale_revision"
        )
    reservations = _live_reservations(company)
    if data["decision"] == "approved":
        for rows, rent_limit, deposit_limit in [
            (reservations, company.budget_limit_minor, company.deposit_limit_minor),
            (
                reservations.filter(item__request=item.request),
                item.request.commitment_ceiling_minor,
                item.request.deposit_limit_minor,
            ),
        ]:
            totals = rows.aggregate(
                rent=Sum("rent_minor"), deposit=Sum("deposit_minor")
            )
            if (
                rent_limit is not None
                and (totals["rent"] or 0) + item.full_term_rent_minor > rent_limit
            ) or (
                deposit_limit is not None
                and (totals["deposit"] or 0) + item.deposit_minor > deposit_limit
            ):
                raise RentalConflict(
                    "The package exceeds the remaining commitment or deposit limit.",
                    code="budget_exceeded",
                )
    approval = CompanyApproval.objects.create(
        item=item,
        approver=user,
        commercial_revision=item.commercial_revision,
        snapshot=item.snapshot,
        snapshot_digest=item.snapshot_digest,
        decision=data["decision"],
        expires_at=item.quote_expires_at,
        reason=data.get("reason", ""),
    )
    if approval.decision == "approved":
        CompanyBudgetReservation.objects.create(
            company=company,
            item=item,
            approval=approval,
            rent_minor=item.full_term_rent_minor,
            deposit_minor=item.deposit_minor,
        )
    item.status = approval.decision
    item.revision += 1  # Approval does not mutate the commercial revision/digest.
    item.save()
    audit(item, user, "company_package_" + approval.decision, approval.reason)
    from .approval_routing import notify

    notify(item, item.request.coordinator)
    from core_apps.chat.services.company_access import approval_card

    approval_card(item, user, "company_approval_decided")
    return item


@transaction.atomic
def hold_item(user, item_id, data):
    require_new_business()
    item = get_object_or_404(CompanyBookingItem, id=item_id)
    company = company_for(user, item.request.company.id, "coordinate", lock=True)
    item = (
        CompanyBookingItem.objects.select_for_update()
        .select_related("request", "offer")
        .get(pk=item.pk)
    )
    require_revision(item, data["expected_revision"])
    if (
        company.review_status != "verified"
        or not company.reviewed_by_id
        or not company.review_reference
    ):
        raise RentalConflict(
            "Company review must complete before a reservation.",
            code="company_review_required",
        )
    approval = item.approvals.filter(
        commercial_revision=item.commercial_revision,
        decision="approved",
        expires_at__gt=timezone.now(),
    ).first()
    if (
        not approval
        or approval.snapshot_digest != item.snapshot_digest
        or item.quote_expires_at <= timezone.now()
    ):
        raise RentalConflict(
            "A current independent approval and quote are required.",
            code="approval_required",
        )
    member_for(approval.approver, company, "approve")
    from .approval_routing import require_independent, validate_staff_plan

    require_independent(item.assigned_approver, item)
    validate_staff_plan(item)
    if (
        item.request.requester_id == approval.approver_id
        or item.request.items.filter(occupants=approval.approver).exists()
    ):
        raise RentalConflict(
            "The approval is no longer independent.", code="approval_required"
        )
    if item.status != "approved" or item.offer.status != "published":
        raise RentalConflict(
            "This package is no longer eligible for reservation.", code="offer_changed"
        )
    if item.hold_id:
        raise RentalConflict(
            "Review the existing hold before creating another.", code="hold_exists"
        )
    if not CompanyBudgetReservation.objects.filter(
        item=item, status="reserved"
    ).exists():
        raise RentalConflict(
            "The budget reservation is no longer valid.", code="budget_exceeded"
        )
    props = resolve_scope(item.offer, lock=True)
    current = scope_snapshot(item.offer, props)
    if any(item.snapshot.get(k) != value for k, value in current.items()):
        raise RentalConflict(
            "Inventory or terms changed. Obtain a fresh package and approval.",
            code="offer_changed",
        )
    policy, rules = lifecycle_policy("reservations")
    if (
        item.snapshot.get("lifecycle_policy_version") != policy.version
        or item.snapshot.get("lifecycle_rules") != rules
    ):
        raise RentalConflict(
            "The reservation policy changed. Review a new package.",
            code="policy_changed",
        )
    starts = item.request.starts_on
    ends = item.request.ends_on_exclusive
    blocked_until = ends + timedelta(days=rules["turnover_days"])
    if (
        starts < timezone.localdate()
        or not 0 < (ends - starts).days <= rules["max_booking_days"]
    ):
        raise ValidationError(
            {"ends_on_exclusive": "Choose a supported future rental interval."}
        )
    for prop in props:
        assert_owner_ready(prop.owner, prop)
        if not confirmation_current(prop, rules):
            raise RentalConflict(
                "The owner must confirm current availability for every included unit.",
                code="availability_confirmation_required",
            )
        expire_property_holds(prop)
        assert_available(
            prop, {"rental_scope": "entire_property"}, starts, blocked_until
        )
    if (
        ReservationHold.objects.filter(
            actor=user, status__in=["active", "reconciliation_pending"]
        ).count()
        >= rules["max_active_holds"]
    ):
        raise RentalConflict(
            "Resolve an existing reservation before starting another.",
            code="hold_limit_reached",
        )
    expires = min(
        approval.expires_at, timezone.now() + timedelta(minutes=rules["hold_minutes"])
    )
    hold = ReservationHold.objects.create(
        property=props[0],
        actor=user,
        offer_id=str(item.offer.id),
        offer_revision=item.offer.revision,
        inventory_revision=1,
        selection_snapshot=item.snapshot,
        terms_digest=item.snapshot_digest,
        starts_on=starts,
        ends_on_exclusive=ends,
        blocked_until_exclusive=blocked_until,
        expires_at=expires,
        policy_version=policy.version,
        policy_snapshot=rules,
    )
    for prop in props:
        allocate_days(
            prop=prop,
            snapshot={"rental_scope": "entire_property"},
            offer_id=str(item.offer.id),
            starts_on=starts,
            ends_on=blocked_until,
            expires_at=expires,
            hold=hold,
        )
    item.hold = hold
    item.status = "held"
    item.revision += 1
    item.save()
    audit(
        item,
        user,
        "company_inventory_held",
        metadata={"hold_id": str(hold.id), "unit_ids": [str(p.id) for p in props]},
    )
    return item


@transaction.atomic
def withdraw_item(user, item_id, data):
    """Release only an uncommitted package; available with new bookings disabled."""
    item = get_object_or_404(CompanyBookingItem, id=item_id)
    company_for(user, item.request.company.id, "coordinate", lock=True)
    item = CompanyBookingItem.objects.select_for_update().get(pk=item.pk)
    require_revision(item, data["expected_revision"])
    if item.lease_id or item.invitation_id:
        raise RentalConflict(
            "Use the agreement or invitation lifecycle for this commitment.",
            code="commitment_exists",
        )
    if item.hold_id:
        hold = ReservationHold.objects.select_for_update().get(pk=item.hold_id)
        if hold.lease_id or hold.status in {"committed", "reconciliation_pending"}:
            raise RentalConflict(
                "Reconcile the existing commitment before releasing it.",
                code="commitment_exists",
            )
        hold.day_locks.all().delete()
        hold.status = "released"
        hold.released_at = timezone.now()
        hold.revision += 1
        hold.save()
    CompanyBudgetReservation.objects.filter(item=item, status="reserved").update(
        status="released"
    )
    item.status = "withdrawn"
    item.revision += 1
    item.save()
    audit(item, user, "company_package_withdrawn", data.get("reason", ""))
    return item


def item_payload(item):
    hold = item.hold
    status = item.status
    if (
        hold
        and (
            hold.status in {"expired", "released", "cancelled"}
            or (hold.expires_at and hold.expires_at <= timezone.now())
        )
        and not item.lease_id
        and status != "withdrawn"
    ):
        status = "hold_expired"
    return {
        "id": str(item.id),
        "request_id": str(item.request.id),
        "revision": item.revision,
        "commercial_revision": item.commercial_revision,
        "status": status,
        "assigned_approver_id": (
            str(item.assigned_approver.id) if item.assigned_approver_id else None
        ),
        "assigned_approver_name": (
            item.assigned_approver.user.get_full_name
            if item.assigned_approver_id
            else None
        ),
        "submitted_at": item.submitted_at.isoformat() if item.submitted_at else None,
        "decision_reason": item.approvals.order_by("-created_at")
        .values_list("reason", flat=True)
        .first(),
        "snapshot": item.snapshot,
        "snapshot_digest": item.snapshot_digest,
        "quote_expires_at": item.quote_expires_at.isoformat(),
        "hold_expires_at": (
            hold.expires_at.isoformat() if hold and hold.expires_at else None
        ),
        "full_term_rent_minor": item.full_term_rent_minor,
        "deposit_minor": item.deposit_minor,
        "lease_id": str(item.lease.id) if item.lease_id else None,
        "contract_progression_available": False,
    }


def request_payload(request, viewer=None):
    items = list(request.items.select_related("hold", "lease", "request"))
    confirmed = [i for i in items if i.lease_id and i.lease.status == "active"]
    covered = sum(i.snapshot.get("capacity") or 0 for i in confirmed)
    return {
        "id": str(request.id),
        "company_id": str(request.company.id),
        "revision": request.revision,
        "title": request.title,
        "purpose": request.purpose,
        "cost_center": request.cost_center,
        "location": request.location,
        "starts_on": str(request.starts_on),
        "ends_on_exclusive": str(request.ends_on_exclusive),
        "headcount": request.headcount,
        "commitment_ceiling_minor": request.commitment_ceiling_minor,
        "deposit_limit_minor": request.deposit_limit_minor,
        "confirmed_items": len(confirmed),
        "total_items": len(items),
        "uncovered_headcount": max(0, request.headcount - covered),
        "items": [
            item_payload(i)
            for i in items
            if viewer is None
            or request.coordinator_id == viewer.pk
            or (i.assigned_approver_id and i.assigned_approver.user_id == viewer.pk)
        ],
    }
