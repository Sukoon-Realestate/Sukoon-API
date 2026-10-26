"""Campaign receipts per eligible space, one account Push, no unknown-send retry."""

import uuid
from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from core_apps.common.idempotency import fingerprint, IdempotencyConflict
from core_apps.notifications.models import (
    DeviceToken,
    Notification,
    NotificationScopePreference,
)
from core_apps.notifications.services import preferences
from core_apps.notifications.services.fcm_service import FCMService
from core_apps.users.models import User
from ..models import PushCampaign, CampaignRecipient, CampaignDelivery
from ..permissions import require_staff_actor

AUDIENCES = {"all", "tenants", "landlords", "verified", "students", "companies"}


def eligible_spaces(user, audience):
    from core_apps.features.models import Lease, RentalInterest
    from core_apps.features.planning_models import HousingRequest
    from core_apps.features.student_models import StudentProfile
    from core_apps.features.company_models import CompanyMembership
    from core_apps.properties.models import Property, PropertyVisit

    if not user.is_active or user.closed_at:
        return set()
    if audience == "verified" and not user.is_verified:
        return set()
    # Personal search is available to every active account. Owning property
    # does not remove that role or imply the absence of a tenant relationship.
    spaces = {"individual"}
    if Property.objects.filter(owner=user).exists():
        spaces.add("owner")
    if StudentProfile.objects.filter(user=user).exists():
        spaces.add("student")
    if CompanyMembership.objects.filter(
        user=user, is_active=True, company__review_status="verified"
    ).exists():
        spaces.add("company")
    if audience == "landlords":
        return spaces & {"owner"}
    if audience == "students":
        return spaces & {"student"}
    if audience == "companies":
        return spaces & {"company"}
    if audience == "tenants":
        actual_renter = (
            Lease.objects.filter(tenant=user).exists()
            or RentalInterest.objects.filter(tenant=user).exists()
            or HousingRequest.objects.filter(user=user).exists()
            or PropertyVisit.objects.filter(tenant=user).exists()
        )
        return spaces & {"individual", "student"} if actual_renter else set()
    return spaces


def valid_devices(user):
    return DeviceToken.objects.filter(user=user, is_active=True).filter(
        Q(
            auth_session__isnull=True,
            user__security_epoch=0,
            user__requires_bound_session=False,
        )
        | Q(
            auth_session__isnull=False,
            auth_session__revoked_at__isnull=True,
            auth_session__expires_at__gt=timezone.now(),
            auth_session__security_epoch=F("user__security_epoch"),
            auth_session__user_id=F("user_id"),
        )
    )


def consented_spaces(user, audience):
    return {
        scope
        for scope in eligible_spaces(user, audience)
        if preferences.get(user, scope).promotions_and_updates
    }


def push_scope(user, spaces):
    # No fabricated "last workspace" for an account without recorded use.
    return (
        NotificationScopePreference.objects.filter(
            user=user,
            scope__in=spaces,
            push_enabled=True,
            promotions_and_updates=True,
            last_used_at__isnull=False,
        )
        .order_by("-last_used_at", "scope")
        .values_list("scope", flat=True)
        .first()
    )


@transaction.atomic
def preview(actor, data):
    from .push_campaigns import registration

    actor = require_staff_actor(actor, {"system_owner"}, lock=True)
    title, body, audience = (
        data.get("title"),
        data.get("body"),
        data.get("audience", "all"),
    )
    if (
        not isinstance(title, str)
        or not title.strip()
        or len(title) > 180
        or not isinstance(body, str)
        or not body.strip()
        or len(body) > 2000
        or audience not in AUDIENCES
    ):
        raise ValidationError("Supply a title, body and supported audience.")
    try:
        key = uuid.UUID(str(data.get("request_key")))
    except (TypeError, ValueError) as error:
        raise ValidationError({"request_key": "A stable UUID is required."}) from error
    digest = fingerprint({"title": title, "body": body, "audience": audience})
    existing = PushCampaign.objects.filter(creator=actor, request_key=key).first()
    if existing:
        if existing.fingerprint != digest:
            raise IdempotencyConflict()
        return existing
    opted_in = NotificationScopePreference.objects.filter(
        promotions_and_updates=True
    ).values("user_id")
    candidates = list(
        User.objects.filter(is_active=True)
        .filter(Q(settings__promotions_and_updates=True) | Q(pk__in=opted_in))
        .order_by("pk")[:5001]
    )
    if len(candidates) > 5000:
        raise ValidationError("Narrow the audience to at most 5000 accounts.")
    targets = []
    for user in candidates:
        spaces = consented_spaces(user, audience)
        if not spaces:
            continue
        scope = push_scope(user, spaces)
        device = (
            valid_devices(user).order_by("-updated_at", "-pk").first()
            if scope
            else None
        )
        targets.append((user, sorted(spaces), scope, device))
    snapshot_digest = fingerprint(
        {
            "content": digest,
            "targets": [
                (user.pk, spaces, scope, registration(device) if device else None)
                for user, spaces, scope, device in targets
            ],
        }
    )
    item = PushCampaign.objects.create(
        creator=actor,
        request_key=key,
        fingerprint=digest,
        title=title,
        body=body,
        audience=audience,
        preview_digest=snapshot_digest,
    )
    for user, spaces, scope, device in targets:
        for workspace in spaces:
            recipient = CampaignRecipient.objects.create(
                campaign=item, user=user, workspace=workspace
            )
            if workspace == scope and device:
                CampaignDelivery.objects.create(
                    recipient=recipient,
                    device=device,
                    registration_digest=registration(device),
                )
    return item


def _receipts(limit):
    ids = list(
        CampaignRecipient.objects.filter(
            campaign__protocol_version=2,
            campaign__state="queued",
            receipt_state="queued",
        )
        .order_by("pk")
        .values_list("pk", flat=True)[:limit]
    )
    for identity in ids:
        initial = CampaignRecipient.objects.get(pk=identity)
        with transaction.atomic():
            campaign = PushCampaign.objects.select_for_update().get(
                pk=initial.campaign_id
            )
            row = CampaignRecipient.objects.select_for_update().get(pk=identity)
            if campaign.state != "queued" or row.receipt_state != "queued":
                continue
            user = User.objects.select_for_update().filter(pk=row.user_id).first()
            if not user or row.workspace not in consented_spaces(
                user, campaign.audience
            ):
                row.receipt_state = "skipped"
            else:
                row.notification = Notification.objects.create(
                    user=user,
                    scope=row.workspace,
                    title=campaign.title,
                    body=campaign.body,
                    notification_type="promotion",
                    data={
                        "action_type": "open_notifications",
                        "event_id": str(campaign.id),
                    },
                )
                row.receipt_state = "delivered"
            row.save(update_fields=["notification", "receipt_state", "updated_at"])


def _finish():
    for item in PushCampaign.objects.filter(state="queued", protocol_version=2)[:100]:
        if (
            not item.recipients.filter(receipt_state="queued").exists()
            and not CampaignDelivery.objects.filter(
                recipient__campaign=item, state__in=["queued", "sending"]
            ).exists()
        ):
            PushCampaign.objects.filter(pk=item.pk, state="queued").update(
                state="complete", revision=F("revision") + 1
            )


def dispatch(*, limit=25):
    from .push_campaigns import registration

    if not settings.ADMIN_CAMPAIGNS_ENABLED:
        return {"disabled": 1}
    _receipts(limit * 4)
    CampaignDelivery.objects.filter(
        recipient__campaign__protocol_version=2,
        state="sending",
        attempt_started_at__lt=timezone.now() - timedelta(minutes=5),
    ).update(state="delivery_unknown", failure_code="worker_interrupted")
    candidates = list(
        CampaignDelivery.objects.filter(
            state="queued",
            recipient__campaign__state="queued",
            recipient__campaign__protocol_version=2,
        )
        .order_by("pk")
        .values_list("pk", flat=True)[:limit]
    )
    counts = {"accepted_by_provider": 0, "delivery_unknown": 0, "skipped": 0}
    if candidates and (
        not FCMService.get_credentials() or not FCMService.get_project_id()
    ):
        return {"provider_unavailable_before_send": 1}
    for identity in candidates:
        initial = CampaignDelivery.objects.select_related("recipient").get(pk=identity)
        with transaction.atomic():
            campaign = PushCampaign.objects.select_for_update().get(
                pk=initial.recipient.campaign_id
            )
            delivery = CampaignDelivery.objects.select_for_update().get(pk=identity)
            if campaign.state != "queued" or delivery.state != "queued":
                continue
            user = (
                User.objects.select_for_update()
                .filter(pk=initial.recipient.user_id)
                .first()
            )
            target = (
                valid_devices(user).filter(pk=delivery.device_id).first()
                if user
                else None
            )
            recipients = {
                row.workspace: row for row in campaign.recipients.filter(user=user)
            }
            # Wait until all that account's receipts were evaluated, then choose
            # its latest targeted, still eligible space with Push enabled.
            if any(row.receipt_state == "queued" for row in recipients.values()):
                continue
            eligible = consented_spaces(user, campaign.audience) if user else set()
            eligible &= {
                scope
                for scope, row in recipients.items()
                if row.receipt_state == "delivered"
            }
            scope = push_scope(user, eligible) if user else None
            if (
                not scope
                or not target
                or registration(target) != delivery.registration_digest
            ):
                delivery.state, delivery.failure_code = "skipped", "eligibility_changed"
                delivery.save()
                counts["skipped"] += 1
                continue
            recipient = recipients[scope]
            delivery.recipient = recipient
            delivery.state, delivery.attempt_token, delivery.attempt_started_at = (
                "sending",
                uuid.uuid4(),
                timezone.now(),
            )
            delivery.save()
        try:
            accepted = FCMService.send_push_to_device(
                token=target.token,
                title=campaign.title,
                body=campaign.body,
                data={
                    **recipient.notification.data,
                    "notification_id": str(recipient.notification.id),
                },
                language=target.language,
                device_type=target.device_type,
            )
        except Exception:
            accepted = False
        state = "accepted_by_provider" if accepted else "delivery_unknown"
        CampaignDelivery.objects.filter(
            pk=identity, state="sending", attempt_token=delivery.attempt_token
        ).update(state=state)
        counts[state] += 1
    _finish()
    return counts
