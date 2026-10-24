"""Tenancy invitations: validate accounts."""

import copy
from rest_framework import status
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError
from core_apps.features.models import Lease


class InvitationConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "The invitation conflicts with current server state."


LIVE_LEASE_STATUSES = {
    Lease.Status.DRAFT,
    Lease.Status.PENDING_SIGNATURES,
    Lease.Status.PENDING,
    Lease.Status.SIGNED,
    Lease.Status.ACTIVE,
    Lease.Status.TERMINATION_PENDING,
}


def localized(request, english, arabic):
    from core_apps.common.locale_middleware import resolve_request_language

    return arabic if resolve_request_language(request) == "ar" else english


def validate_accounts(owner, tenant, request=None):
    from core_apps.chat.moderation.policy import require_new_business
    require_new_business(owner)
    require_new_business(tenant)
    if not owner.is_active or not owner.is_verified:
        raise PermissionDenied(
            localized(
                request,
                "A verified active owner account is required.",
                "يلزم حساب مالك نشط وموثّق.",
            )
        )
    if owner.pk == tenant.pk:
        raise ValidationError(
            {
                "tenant_id": localized(
                    request,
                    "The owner cannot invite themselves.",
                    "لا يمكن للمالك دعوة نفسه.",
                )
            }
        )
    if not tenant.is_active or not tenant.is_verified:
        raise PermissionDenied(
            localized(
                request,
                "A verified active tenant account is required.",
                "يلزم حساب مستأجر نشط وموثّق.",
            )
        )


def _room_details(inventory, offer):
    rooms = {
        str(room.get("id")): room
        for room in inventory.get("rooms", [])
        if room.get("id")
    }
    room_ids = [str(value) for value in offer.get("room_ids", [])]
    selected_rooms = [rooms[value] for value in room_ids if value in rooms]
    bed_id = str(offer.get("bed_id") or "")
    bed = next(
        (
            item
            for room in selected_rooms
            for item in room.get("beds", [])
            if str(item.get("id")) == bed_id
        ),
        None,
    )
    capacity_values = [room.get("capacity") for room in selected_rooms]
    capacity_values = [value for value in capacity_values if isinstance(value, int)]
    return {
        "room_ids": room_ids,
        "room_names": [str(room.get("name") or "") for room in selected_rooms],
        "bed_id": bed_id or None,
        "bed_name": str((bed or {}).get("name") or "") or None,
        "capacity": (
            offer.get("capacity")
            if isinstance(offer.get("capacity"), int)
            else (sum(capacity_values) if capacity_values else None)
        ),
        "bathroom_access": copy.deepcopy(
            offer.get("bathroom_access")
            or next(
                (
                    room.get("bathroom_access")
                    for room in selected_rooms
                    if room.get("bathroom_access")
                ),
                [],
            )
        ),
    }
