"""Durable preview/confirm/dispatch. Unknown FCM results are never retried."""

import uuid
from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.db.models import Count, F, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError
from core_apps.common.idempotency import fingerprint, IdempotencyConflict
from core_apps.notifications.models import DeviceToken, Notification
from core_apps.notifications.services.fcm_service import FCMService
from core_apps.users.models import User
from ..models import PushCampaign, CampaignRecipient, CampaignDelivery, StaffProfile
from ..permissions import require_staff_actor


def users(audience):
    result = User.objects.filter(is_active=True, settings__promotions_and_updates=True)
    if audience == "verified":
        result = result.filter(is_verified=True)
    elif audience == "landlords":
        result = result.filter(properties__isnull=False)
    elif audience == "tenants":
        result = result.filter(properties__isnull=True)
    return result.distinct()


def devices(audience):
    return DeviceToken.objects.filter(is_active=True, user__in=users(audience)).filter(
        Q(auth_session__isnull=True, user__security_epoch=0)
        | Q(
            auth_session__isnull=False,
            auth_session__revoked_at__isnull=True,
            auth_session__expires_at__gt=timezone.now(),
            auth_session__security_epoch=F("user__security_epoch"),
            auth_session__user_id=F("user_id"),
        )
    )


def registration(device):
    return fingerprint(
        {
            "user": device.user_id,
            "token": device.token,
            "session": device.auth_session_id,
        }
    )


def payload(item):
    counts = dict(
        CampaignDelivery.objects.filter(recipient__campaign=item)
        .values_list("state")
        .annotate(total=Count("pk"))
    )
    return {
        "id": str(item.id),
        "title": item.title,
        "body": item.body,
        "audience": item.audience,
        "state": item.state,
        "revision": item.revision,
        "preview_digest": item.preview_digest,
        "request_key": str(item.request_key),
        "recipientCount": item.recipients.values("user_id").distinct().count(),
        "receiptCount": item.recipients.count(),
        "workspaceCounts": dict(
            item.recipients.values_list("workspace").annotate(total=Count("pk"))
        ),
        "pushAccountCount": CampaignDelivery.objects.filter(recipient__campaign=item)
        .values("recipient__user_id")
        .distinct()
        .count(),
        "deliveryCounts": counts,
        "openRate": None,
        "timeAgo": item.created_at.isoformat(),
        "can_confirm": item.state == "preview" and settings.ADMIN_CAMPAIGNS_ENABLED,
        "delivery_semantics": "Provider acceptance is not device delivery. Unknown results are not retried.",
    }


@transaction.atomic
def transition(actor, identity, data, *, cancel=False):
    require_staff_actor(actor, {StaffProfile.RoleName.SYSTEM_OWNER}, lock=True)
    item = get_object_or_404(PushCampaign.objects.select_for_update(), id=identity)
    if data.get("preview_digest") != item.preview_digest:
        raise IdempotencyConflict("The preview differs. Review the original campaign.")
    if cancel and item.state == "cancelled":
        return item
    if not cancel and item.confirmed_at:
        return item  # Original confirmation recovery cannot restart delivery.
    if (
        type(data.get("expected_revision")) is not int
        or data["expected_revision"] != item.revision
    ):
        raise IdempotencyConflict("Campaign changed. Refresh before confirming.")
    if cancel:
        item.state, item.cancelled_at = "cancelled", timezone.now()
        CampaignDelivery.objects.filter(
            recipient__campaign=item, state="queued"
        ).update(state="cancelled")
        CampaignRecipient.objects.filter(campaign=item, receipt_state="queued").update(
            receipt_state="cancelled"
        )
    else:
        if not settings.ADMIN_CAMPAIGNS_ENABLED:
            error = APIException(
                "Campaign dispatch is not enabled on this environment."
            )
            error.status_code = 503
            raise error
        if item.state != "preview":
            raise IdempotencyConflict(
                "This campaign is no longer awaiting confirmation."
            )
        item.state, item.confirmed_at = "queued", timezone.now()
    item.revision += 1
    item.save()
    return item


def dispatch_legacy(*, limit=25):
    if not settings.ADMIN_CAMPAIGNS_ENABLED:
        return {"disabled": 1}
    # A crashed/unknown send cannot be replayed, even by another worker.
    CampaignDelivery.objects.filter(
        state="sending", attempt_started_at__lt=timezone.now() - timedelta(minutes=5)
    ).update(state="delivery_unknown", failure_code="worker_interrupted")
    # Credential acquisition occurs before claiming any send. Its failure is a
    # known pre-send outage and must not consume a delivery as "unknown".
    if not FCMService.get_credentials() or not FCMService.get_project_id():
        return {"provider_unavailable_before_send": 1}
    counts = {"accepted_by_provider": 0, "delivery_unknown": 0, "skipped": 0}
    candidates = list(
        CampaignDelivery.objects.filter(
            state="queued",
            recipient__campaign__state="queued",
            recipient__campaign__protocol_version=1,
        )
        .order_by("pk")
        .values_list("pk", flat=True)[:limit]
    )
    for identity in candidates:
        initial = CampaignDelivery.objects.select_related("recipient__campaign").get(
            pk=identity
        )
        with transaction.atomic():
            campaign = PushCampaign.objects.select_for_update().get(
                pk=initial.recipient.campaign_id
            )
            recipient = CampaignRecipient.objects.select_for_update().get(
                pk=initial.recipient_id
            )
            delivery = CampaignDelivery.objects.select_for_update().get(pk=identity)
            if campaign.state != "queued" or delivery.state != "queued":
                continue
            target = (
                devices(campaign.audience)
                .filter(pk=delivery.device_id, user_id=recipient.user_id)
                .first()
            )
            if not target or registration(target) != delivery.registration_digest:
                delivery.state, delivery.failure_code = "skipped", "eligibility_changed"
                delivery.save()
                counts["skipped"] += 1
                continue
            if not recipient.notification_id:
                recipient.notification = Notification.objects.create(
                    user_id=recipient.user_id,
                    title=campaign.title,
                    body=campaign.body,
                    notification_type="promotion",
                    data={
                        "action_type": "open_notifications",
                        "event_id": str(campaign.id),
                    },
                )
                recipient.save(update_fields=["notification"])
            delivery.state, delivery.attempt_token, delivery.attempt_started_at = (
                "sending",
                uuid.uuid4(),
                timezone.now(),
            )
            delivery.save()
        # No network operations hold database locks. A false result from the
        # existing adapter may mean a lost acknowledgement; treat it as unknown.
        try:
            accepted = FCMService.send_push_to_device(
                token=target.token,
                title=campaign.title,
                body=campaign.body,
                data={
                    "action_type": "open_notifications",
                    "notification_id": str(recipient.notification.id),
                },
            )
        except Exception:
            accepted = False
        state = "accepted_by_provider" if accepted else "delivery_unknown"
        CampaignDelivery.objects.filter(
            pk=identity, state="sending", attempt_token=delivery.attempt_token
        ).update(state=state)
        counts[state] += 1
    for item in PushCampaign.objects.filter(state="queued", protocol_version=1)[:100]:
        if not CampaignDelivery.objects.filter(
            recipient__campaign=item, state__in=["queued", "sending"]
        ).exists():
            PushCampaign.objects.filter(pk=item.pk, state="queued").update(
                state="complete", revision=F("revision") + 1
            )
    return counts


def preview(actor, data):
    from .workspace_campaigns import preview as scoped_preview

    return scoped_preview(actor, data)


def dispatch(*, limit=25):
    from .workspace_campaigns import dispatch as scoped_dispatch

    if PushCampaign.objects.filter(protocol_version=1, state="queued").exists():
        dispatch_legacy(limit=limit)
    return scoped_dispatch(limit=limit)
