"""One explicit independent decision stage, projected as work rather than chat state."""

from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from ...company_models import CompanyMembership, CompanyBookingItem
from ..rental_lifecycle.common import audit, require_revision
from ..rental_phase2 import RentalConflict
from .access import company_for, request_for, require_new_business, member_for


def eligible(member, item):
    if (
        not member
        or not member.is_active
        or not member.is_approver
        or not member.user.is_active
        or not member.user.is_verified
    ):
        return False
    request = item.request
    if member.company_id != request.company_id or member.user_id in {
        request.requester_id,
        request.coordinator_id,
    }:
        return False
    return not request.items.filter(
        Q(occupants=member.user)
        | Q(planned_staff__membership__user=member.user)
        | Q(planned_staff__work_email__iexact=member.user.email)
    ).exists()


def require_independent(member, item):
    if not eligible(member, item):
        raise RentalConflict(
            "Assign an active independent approver before submitting this package.",
            code="independent_approver_required",
        )


def validate_staff_plan(item):
    expected = {
        row["staff_id"]: row["proposal_revision"]
        for row in item.snapshot.get("planned_staff", [])
    }
    people = list(item.planned_staff.select_related("membership"))
    if len(people) != len(expected) or any(
        expected.get(str(person.id)) != person.proposal_revision
        or person.employment_status != "active"
        or "employee" not in person.proposed_roles
        or (
            person.membership_id
            and (not person.membership.is_active or not person.membership.is_employee)
        )
        for person in people
    ):
        raise RentalConflict(
            "The staff plan changed. Review a new package.", code="staff_plan_changed"
        )


@transaction.atomic
def configure(user, company_id, data):
    company = company_for(user, company_id, "admin", lock=True)
    require_revision(company, data["expected_revision"])
    selected = []
    for key in ("default_approver_id", "backup_approver_id"):
        member = (
            get_object_or_404(
                CompanyMembership,
                company=company,
                id=data[key],
                is_active=True,
                is_approver=True,
                user__is_active=True,
                user__is_verified=True,
            )
            if data[key]
            else None
        )
        selected.append(member)
    if selected[1] and (not selected[0] or selected[0].pk == selected[1].pk):
        raise RentalConflict(
            "Choose a distinct backup after selecting the default approver.",
            code="invalid_approval_route",
        )
    company.default_approver, company.backup_approver = selected
    company.revision += 1
    company.save()
    audit(
        company,
        user,
        "company_approval_route_changed",
        data["reason"],
        metadata={
            "default_approver_id": str(selected[0].id) if selected[0] else None,
            "backup_approver_id": str(selected[1].id) if selected[1] else None,
        },
    )
    return company


@transaction.atomic
def submit(user, item_id, data):
    require_new_business()
    from .access import booking_account_parties, lock_account_parties
    from core_apps.users.services.new_business import (
        require_new_business as require_account_business,
    )

    parties = lock_account_parties(user, booking_account_parties(item_id))
    require_account_business(*parties)
    initial = get_object_or_404(CompanyBookingItem, id=item_id)
    request = request_for(user, initial.request.id, lock=True)
    item = CompanyBookingItem.objects.select_for_update().get(pk=initial.pk)
    require_revision(item, data["expected_revision"])
    from .negotiation_binding import require_accepted

    require_accepted(item)
    if item.status != "proposed" or item.quote_expires_at <= timezone.now():
        raise RentalConflict(
            "Obtain a current proposed quote before submitting approval.",
            code="quote_expired",
        )
    member = request.company.default_approver
    # Backup routing is always an explicit administrator decision.
    require_independent(member, item)
    validate_staff_plan(item)
    item.assigned_approver = member
    item.submitted_at = timezone.now()
    item.status = "approval_pending"
    item.revision += 1
    item.save()
    audit(
        item,
        user,
        "company_approval_submitted",
        metadata={
            "company_id": str(request.company.id),
            "approver_membership_id": str(member.id),
            "snapshot_digest": item.snapshot_digest,
        },
    )
    notify(item, member.user)
    from core_apps.chat.services.company_access import approval_card

    approval_card(item, user, "company_approval_submitted")
    return item


def notify(item, recipient):
    from ...planning_models import PlanningEvent

    PlanningEvent.objects.get_or_create(
        recipient=recipient,
        event_key=f"company.work:{item.id}:{item.revision}",
        defaults={
            "destination": {
                "action_type": "open_company_work",
                "target_id": str(item.request.company.id),
                "item_id": str(item.id),
                "revision": item.revision,
                "schema_version": "1",
                "workspace": "company",
            }
        },
    )


@transaction.atomic
def reassign(user, item_id, data):
    initial = get_object_or_404(CompanyBookingItem, id=item_id)
    company = company_for(user, initial.request.company.id, "admin", lock=True)
    item = CompanyBookingItem.objects.select_for_update().get(pk=initial.pk)
    require_revision(item, data["expected_revision"])
    if item.status != "approval_pending":
        raise RentalConflict(
            "Only a pending approval can be reassigned.", code="package_closed"
        )
    member = get_object_or_404(
        CompanyMembership, company=company, id=data["approver_id"]
    )
    require_independent(member, item)
    item.assigned_approver = member
    item.revision += 1
    item.save()
    audit(
        item,
        user,
        "company_approval_reassigned",
        data["reason"],
        metadata={
            "company_id": str(company.id),
            "approver_membership_id": str(member.id),
        },
    )
    notify(item, member.user)
    from core_apps.chat.services.company_access import approval_card

    approval_card(item, user, "company_approval_reassigned")
    return item


def work_items(user, company):
    from .listing_changes import invalidated_ids

    # Derived from current canonical business state. No generic completion API.
    member = member_for(user, company)
    admin = company.memberships.filter(
        user=user, is_active=True, is_admin=True
    ).exists()
    administrative = Q(status="approval_pending") if admin else Q(pk__in=[])
    coordinator = (
        Q(request__coordinator=user) if member.is_coordinator else Q(pk__in=[])
    )
    affected = Q(id__in=invalidated_ids()) & ~Q(status__in=["withdrawn", "replaced"])
    return (
        CompanyBookingItem.objects.filter(request__company=company)
        .filter(
            administrative
            | affected
            & (
                coordinator
                | Q(
                    assigned_approver__user=user,
                    assigned_approver__is_active=True,
                    assigned_approver__is_approver=True,
                )
            )
            | Q(
                status="approval_pending",
                assigned_approver__user=user,
                assigned_approver__is_active=True,
                assigned_approver__is_approver=True,
            )
            | coordinator
            & Q(
                status__in=[
                    "proposed",
                    "approved",
                    "changes_requested",
                    "rejected",
                    "held",
                ],
            )
        )
        .select_related("request", "hold", "assigned_approver__user")
        .order_by("quote_expires_at", "id")
    )


def work_payload(item, user):
    from .listing_changes import needs_review, publication_blocked
    from .access import booking_account_parties
    from core_apps.users.services.new_business import restricted_accounts

    source_review = needs_review(item)
    unpublished = publication_blocked(item)
    closure_blocked = bool(
        restricted_accounts(
            user.pk, *booking_account_parties(item.id, include_preparation=False)
        )
    )
    pending = item.status == "approval_pending"
    reassign = (
        pending
        and (not item.assigned_approver_id or item.assigned_approver.user_id != user.pk)
        and item.request.company.memberships.filter(
            user=user, is_active=True, is_admin=True
        ).exists()
    )
    actionable = (
        not source_review
        and not unpublished
        and not closure_blocked
        and item.quote_expires_at > timezone.now()
        and (not pending or eligible(item.assigned_approver, item))
    )
    return {
        "id": str(item.id),
        "company_id": str(item.request.company.id),
        "request_id": str(item.request.id),
        "title": item.request.title,
        "revision": item.revision,
        "status": item.status,
        "action": (
            "review_request"
            if source_review
            else "reassign" if reassign else "decide" if pending else "review_request"
        ),
        "due_at": item.quote_expires_at.isoformat(),
        "actionable": actionable,
        "blocking_reason": (
            "account_closure_pending"
            if closure_blocked
            else (
                "company_source_changed"
                if source_review
                else (
                    "portfolio_offer_unpublished"
                    if unpublished
                    else "" if actionable else "refresh_quote_or_authority"
                )
            )
        ),
    }
