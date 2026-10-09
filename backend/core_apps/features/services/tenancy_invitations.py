import copy

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError

from core_apps.features.models import Lease, TenancyInvitation
from core_apps.notifications.models import Notification
from core_apps.notifications.services.fcm_service import FCMService
from core_apps.notifications.services.notification_service import NotificationService
from core_apps.properties.models import PropertyVisit


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
    language = getattr(request, "LANGUAGE_CODE", "en") or "en"
    return arabic if language.lower().startswith("ar") else english


def validate_accounts(owner, tenant, request=None):
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


def validate_source_relationship(property_obj, tenant, request=None):
    allowed = PropertyVisit.objects.filter(
        property=property_obj,
        tenant=tenant,
        status__in=[PropertyVisit.Status.PENDING, PropertyVisit.Status.CONFIRMED],
    ).exists()
    if not allowed:
        raise PermissionDenied(
            localized(
                request,
                "The tenant must have a current visit relationship for this property.",
                "يجب أن تكون للمستأجر علاقة زيارة حالية بهذا العقار.",
            )
        )


def _room_details(inventory, offer):
    rooms = {
        str(room.get("id")): room for room in inventory.get("rooms", []) if room.get("id")
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
        "capacity": offer.get("capacity")
        if isinstance(offer.get("capacity"), int)
        else (sum(capacity_values) if capacity_values else None),
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


def resolve_offer_snapshot(property_obj, offer_id, expected_revision=None, request=None):
    inventory = property_obj.rental_inventory or {}
    if not inventory:
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


def notify_after_commit(*, recipient, invitation, notification_type, title, body, workspace, label):
    data = {
        "workspace": workspace,
        "action_label": label,
        "action_type": "open_tenancy_invitation",
        "target_id": str(invitation.id),
    }
    NotificationService.create_notification(
        user=recipient,
        title=title,
        body=body,
        notification_type=notification_type,
        category="tenancy_invitation",
        icon_type="contract",
        data=data,
        send_push=False,
    )
    transaction.on_commit(
        lambda: FCMService.send_push_to_user(
            user=recipient,
            title=title,
            body=body,
            data={
                "notification_type": notification_type,
                "action_type": "open_tenancy_invitation",
                "target_id": str(invitation.id),
                "workspace": workspace,
                "title": title,
                "body": body,
                "action_label": label,
            },
            notification_type=notification_type,
        )
    )


def create_notification_for_invitation(request, invitation):
    notify_after_commit(
        recipient=invitation.tenant,
        invitation=invitation,
        notification_type=Notification.NotificationType.TENANCY_INVITATION,
        title=localized(request, "Rental invitation", "دعوة للإيجار"),
        body=localized(
            request,
            "Review the invitation to proceed with a lease.",
            "راجع الدعوة للمتابعة إلى عقد الإيجار.",
        ),
        workspace="tenant",
        label=localized(request, "Review invitation", "مراجعة الدعوة"),
    )


def create_notification_for_response(request, invitation):
    accepted = invitation.status == TenancyInvitation.Status.ACCEPTED
    notify_after_commit(
        recipient=invitation.owner,
        invitation=invitation,
        notification_type=Notification.NotificationType.TENANCY_INVITATION_RESPONSE,
        title=localized(request, "Invitation response", "الرد على دعوة الإيجار"),
        body=localized(
            request,
            "The tenant accepted your rental invitation."
            if accepted
            else "The tenant rejected your rental invitation.",
            "وافق المستأجر على دعوة الإيجار."
            if accepted
            else "رفض المستأجر دعوة الإيجار.",
        ),
        workspace="owner",
        label=localized(request, "Review invitation", "مراجعة الدعوة"),
    )
