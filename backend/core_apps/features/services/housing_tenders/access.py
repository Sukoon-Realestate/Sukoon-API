"""Current group authority and sealed owner projections."""

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound
from ...advanced_tender_models import (
    HousingTender,
    OwnerBid,
    PackageCandidate,
    TenderPackageRun,
    TenderBidClarification,
)
from ...planning_models import HousingGroup, HousingRequest
from ..planning import eligible_owner, enabled_services

CAPABILITY = "collective_tender_planning"


def member(user, tender):
    membership = tender.group.memberships.filter(user=user, status="active").first()
    return bool(
        membership
        and tender.member_access.get(str(user.id))
        == [str(membership.id), membership.joined_revision]
    )


def admin(user, tender):
    return (
        member(user, tender)
        and tender.group.status == "active"
        and tender.group.memberships.filter(
            user=user, status="active", role="admin"
        ).exists()
    )


def current(tender):
    from ..student_housing.publication import request_current

    return (
        tender.group.status == "active"
        and tender.group.roster_revision == tender.roster_revision
        and tender.request.revision == tender.request_revision
        and tender.request.status == "published"
        and tender.request.expires_at > timezone.now()
        and request_current(tender.request)
    )


def get_tender(user, identifier, *, lock=False):
    obj = get_object_or_404(
        HousingTender.objects.select_related("group", "request", "active_snapshot"),
        id=identifier,
    )
    if lock:
        obj.group = HousingGroup.objects.select_for_update().get(pk=obj.group_id)
        obj.request = HousingRequest.objects.select_for_update().get(pk=obj.request_id)
        obj = (
            HousingTender.objects.select_for_update(of=("self",))
            .select_related("group", "request", "active_snapshot")
            .get(pk=obj.pk)
        )
    if member(user, obj):
        return obj
    if obj.bids.filter(owner=user).exists():
        return obj
    if eligible_owner(user) and (
        (obj.status == "published" and obj.closes_at > timezone.now() and current(obj))
        or obj.bids.filter(owner=user).exists()
    ):
        return obj
    raise NotFound()


def get_package(user, identifier, *, lock=False):
    obj = get_object_or_404(
        PackageCandidate.objects.select_related("tender", "snapshot"), id=identifier
    )
    obj.tender = get_tender(user, obj.tender.id, lock=lock)
    if not member(user, obj.tender):
        raise NotFound()
    if lock:
        obj = (
            PackageCandidate.objects.select_for_update(of=("self",))
            .select_related("tender__group", "tender__request", "snapshot")
            .get(pk=obj.pk)
        )
    return obj


def subject(user, identifier):
    note = (
        TenderBidClarification.objects.select_related("bid__tender")
        .filter(id=identifier)
        .first()
    )
    if note:
        if note.bid.owner_id == user.pk or admin(user, note.bid.tender):
            return note
        raise NotFound()
    if TenderPackageRun.objects.filter(id=identifier).exists():
        from .construction import get_run

        return get_run(user, identifier)
    if HousingTender.objects.filter(id=identifier).exists():
        return get_tender(user, identifier)
    if PackageCandidate.objects.filter(id=identifier).exists():
        return get_package(user, identifier)
    obj = OwnerBid.objects.filter(id=identifier).select_related("tender").first()
    if obj:
        get_tender(user, obj.tender.id)
        if obj.owner_id == user.pk or admin(user, obj.tender):
            return obj
        raise NotFound()
    return None


def tender_actions(user, tender):
    if CAPABILITY not in enabled_services():
        return []
    if not current(tender):
        return ["amend"] if admin(user, tender) else []
    if tender.closes_at <= timezone.now():
        return (
            ["package-runs", "amend", "withdraw"]
            if admin(user, tender) and tender.status == "published"
            else []
        )
    result = []
    if member(user, tender) and tender.status == "collecting_requirements":
        result.append("requirements")
    if admin(user, tender):
        result += {
            "collecting_requirements": ["publish"],
            "published": ["package-runs", "amend", "withdraw"],
        }.get(tender.status, [])
    elif (
        not member(user, tender)
        and eligible_owner(user)
        and tender.status == "published"
    ):
        result.append("bid")
    return result


def package_quotes_current(package):
    from datetime import date
    from ..rental_lifecycle.inventory import assert_available
    from ..tenancy_invitations import InvitationConflict, resolve_offer_snapshot
    from ..rental_phase2 import RentalConflict
    from rest_framework.exceptions import ValidationError
    from ...advanced_tender_models import TenderBidLine

    for allocation in package.allocations:
        line = (
            TenderBidLine.objects.select_related("bid", "offer__property")
            .filter(id=allocation["line_id"], bid__tender=package.tender)
            .first()
        )
        if (
            not line
            or line.bid.status != "submitted"
            or line.bid.revision != allocation["bid_revision"]
            or line.bid.expires_at <= timezone.now()
        ):
            return False
        try:
            resolve_offer_snapshot(
                line.offer.property,
                line.offer.selection["offer_id"],
                line.offer.selection["offer_revision"],
            )
            assert_available(
                line.offer.property,
                line.offer.selection,
                date.fromisoformat(allocation["start_on"]),
                date.fromisoformat(allocation["end_on"]),
            )
        except (ValidationError, RentalConflict, InvitationConflict):
            return False
    return True


def actions(user, capability, subject_id=""):
    if capability in {"collective_tender_execution", "conditional_group_execution"}:
        from config.advanced_housing import mock_mode_available

        if not subject_id:
            return ["read"]
        try:
            item = get_package(user, subject_id)
        except (NotFound, ValueError):
            return []
        return ["read"] + (
            ["prepare"]
            if mock_mode_available()
            and capability in enabled_services()
            and admin(user, item.tender)
            and current(item.tender)
            and item.tender.status == "published"
            and item.tender.active_snapshot_id == item.snapshot_id
            and package_quotes_current(item)
            and item.consents.filter(decision="accept").count() == len(item.allocations)
            else []
        )
    if capability != CAPABILITY:
        return []
    if not subject_id:
        return ["read", "create"]
    try:
        obj = subject(user, subject_id)
    except (NotFound, ValueError):
        return []
    if isinstance(obj, HousingTender):
        return ["read", *tender_actions(user, obj)]
    if isinstance(obj, OwnerBid):
        result = ["read"]
        if CAPABILITY in enabled_services():
            result.append("clarifications")
            if obj.owner_id == user.pk and obj.status == "submitted":
                result.append("withdraw")
            if (
                obj.owner_id == user.pk
                and "bid" in tender_actions(user, obj.tender)
                and obj.status != "revised"
            ):
                result.append("revise")
        return result
    if isinstance(obj, TenderPackageRun):
        return ["read"] + (
            ["dispatch"]
            if obj.status == "queued" and CAPABILITY in enabled_services()
            else []
        )
    if isinstance(obj, PackageCandidate):
        own = any(x["participant_id"] == str(user.id) for x in obj.allocations)
        valid = (
            current(obj.tender)
            and obj.tender.active_snapshot_id == obj.snapshot_id
            and obj.tender.status == "published"
        )
        return ["read"] + (
            ["consents"]
            if own
            and valid
            and package_quotes_current(obj)
            and CAPABILITY in enabled_services()
            else []
        )
    return []
