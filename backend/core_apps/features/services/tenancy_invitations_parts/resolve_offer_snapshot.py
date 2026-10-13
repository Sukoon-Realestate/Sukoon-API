"""Tenancy invitations: resolve offer snapshot."""

import copy
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from core_apps.features.models import Lease, TenancyInvitation
from .validate_accounts import (
    InvitationConflict,
    LIVE_LEASE_STATUSES,
    localized,
    _room_details,
)


def resolve_offer_snapshot(
    property_obj, offer_id, expected_revision=None, request=None
):
    inventory = property_obj.rental_inventory or {}
    # The property API represents empty legacy inventory as {"offers": []}.
    # Accept that exact shape too, without treating unknown versions as legacy.
    if not inventory or inventory == {"offers": []}:
        if offer_id or expected_revision is not None:
            raise ValidationError(
                {
                    "offer_id": localized(
                        request,
                        "Legacy properties do not accept an offer selection.",
                        "العقارات القديمة لا تقبل اختيار عرض.",
                    )
                }
            )
        return "", None
    if inventory.get("schema_version") != 1:
        raise ValidationError(
            localized(
                request,
                "Unsupported rental inventory version.",
                "إصدار مخزون الإيجار غير مدعوم.",
            )
        )
    if not offer_id or expected_revision is None:
        raise ValidationError(
            {
                "offer_id": localized(
                    request,
                    "offer_id and expected_offer_revision are required.",
                    "يلزم معرف العرض ومراجعته المتوقعة.",
                )
            }
        )
    offer = next(
        (
            value
            for value in inventory.get("offers", [])
            if str(value.get("id")) == str(offer_id)
        ),
        None,
    )
    if not offer:
        raise ValidationError({"offer_id": "Offer not found for this property."})
    if int(offer.get("revision", 0)) != int(expected_revision):
        raise InvitationConflict(
            localized(
                request,
                "The offer revision is stale.",
                "مراجعة العرض قديمة.",
            )
        )
    if offer.get("archived") or offer.get("availability") != "available":
        raise InvitationConflict(
            localized(
                request,
                "The selected accommodation is not available.",
                "مكان الإقامة المحدد غير متاح.",
            )
        )
    snapshot = {
        "property_id": str(property_obj.id),
        "offer_id": str(offer_id),
        "offer_revision": int(offer.get("revision", 0)),
        "rental_scope": offer.get("rental_scope"),
        "name": str(offer.get("name") or ""),
        **_room_details(inventory, offer),
        "availability": offer.get("availability"),
        "archived": bool(offer.get("archived")),
        "offer_link": str(offer.get("offer_link") or ""),
        "terms": copy.deepcopy(offer.get("terms") or {}),
    }
    return str(offer_id), snapshot


def current_invitation_problem(invitation):
    if invitation.owner_id != invitation.property.owner_id:
        return "ownership_changed"
    if (
        invitation.property.status != invitation.property.Status.VERIFIED
        or not invitation.property.is_verified
    ):
        return "property_unavailable"
    if not invitation.owner.is_active or not invitation.owner.is_verified:
        return "owner_access_changed"
    if not invitation.tenant.is_active or not invitation.tenant.is_verified:
        return "tenant_access_changed"
    try:
        _, current = resolve_offer_snapshot(
            invitation.property,
            invitation.offer_id,
            (invitation.offer_snapshot or {}).get("offer_revision"),
        )
    except (ValidationError, InvitationConflict):
        return "accommodation_changed"
    if current != invitation.offer_snapshot:
        return "accommodation_changed"
    conflicting = Lease.objects.filter(
        property=invitation.property,
        offer_id=invitation.offer_id,
        status__in=LIVE_LEASE_STATUSES,
    )
    if invitation.lease_id:
        conflicting = conflicting.exclude(pk=invitation.lease_id)
    if conflicting.exists():
        return "allocation_conflict"
    return None


def refresh_effective_status(invitation, save=True):
    if invitation.lease_id or invitation.status not in {
        TenancyInvitation.Status.PENDING,
        TenancyInvitation.Status.ACCEPTED,
    }:
        return invitation
    new_status = None
    now = timezone.now()
    if invitation.expires_at <= now:
        new_status = TenancyInvitation.Status.EXPIRED
    elif current_invitation_problem(invitation):
        new_status = TenancyInvitation.Status.REVOKED
    if new_status:
        invitation.status = new_status
        invitation.revision += 1
        if new_status == TenancyInvitation.Status.REVOKED:
            invitation.revoked_at = now
        if save:
            fields = ["status", "revision", "updated_at"]
            if invitation.revoked_at:
                fields.append("revoked_at")
            invitation.save(update_fields=fields)
    return invitation


def invitation_is_eligible(invitation):
    if (
        invitation.status != TenancyInvitation.Status.ACCEPTED
        or invitation.lease_id
        or invitation.expires_at <= timezone.now()
    ):
        return False
    return current_invitation_problem(invitation) is None
