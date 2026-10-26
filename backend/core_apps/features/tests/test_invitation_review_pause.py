"""A listing review pauses commitments without discarding their invitation."""

# flake8: noqa: F401,F811 -- shared pytest fixtures.
import uuid
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from core_apps.features.models import TenancyInvitation
from core_apps.features.services.tenancy_invitations import refresh_effective_status
from core_apps.features.services.tenancy_invitations_parts.notify_after_commit import (
    create_notification_for_invitation,
)
from core_apps.notifications.models import Notification, DeviceToken, PushDelivery
from core_apps.notifications.services.push_delivery import dispatch
from core_apps.properties.services.property import PropertyService
from .test_cycle_concurrency import parallel_calls
from .test_tenancy_invitation_revoke import invitation
from .test_tenancy_invitations import (
    participants,
    owned_property,
    authenticated,
    create_invitation,
)

pytestmark = pytest.mark.django_db
API = "/api/v1/features/v1/tenancy-invitations/"


def respond(invitation, decision):
    return authenticated(invitation.tenant).post(
        f"{API}{invitation.id}/respond/",
        {
            "decision": decision,
            "revision": invitation.revision,
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )


@pytest.mark.parametrize("state", ["pending", "accepted"])
@pytest.mark.parametrize("language", ["ar", "en"])
def test_editorial_review_preserves_invitation_and_original_deadline(
    invitation, state, language
):
    invitation.status = state
    invitation.save(update_fields=["status"])
    deadline = invitation.expires_at
    PropertyService.update_property(invitation.property, {"title": "Corrected title"})
    client = authenticated(invitation.tenant)
    detail = client.get(f"{API}{invitation.id}/", HTTP_ACCEPT_LANGUAGE=language)
    assert detail.status_code == 200
    assert detail.data["status"] == state and detail.data["revision"] == 1
    assert not detail.data["eligible_for_lease"]
    assert detail.data["actions"] == {
        "can_respond": state == "pending",
        "can_accept": False,
        "can_reject": state == "pending",
    }
    message = detail.data["blocking_reasons"][0]
    assert ("مراجعة" in message) if language == "ar" else ("reviewed" in message)
    invitation.refresh_from_db()
    assert invitation.expires_at == deadline and invitation.revoked_at is None
    if state == "pending":
        blocked = respond(invitation, "accepted")
        assert blocked.status_code == 409
        assert blocked.data["code"] == "property_review_pending"
    # Approval restores only current eligibility, not a fresh invitation or deadline.
    prop = invitation.property
    prop.status, prop.is_verified = prop.Status.VERIFIED, True
    prop.save(update_fields=["status", "is_verified"])
    detail = client.get(f"{API}{invitation.id}/")
    assert detail.data["eligible_for_lease"] == (state == "accepted")
    if state == "pending":
        assert respond(invitation, "accepted").status_code == 200
    invitation.refresh_from_db()
    assert invitation.expires_at == deadline


def test_rejection_remains_available_during_review(invitation):
    PropertyService.update_property(invitation.property, {"title": "Corrected title"})
    assert respond(invitation, "rejected").status_code == 200
    invitation.refresh_from_db()
    assert invitation.status == "rejected"


def test_review_does_not_extend_expiry_or_resurrect_hard_revocation(invitation):
    PropertyService.update_property(invitation.property, {"title": "Corrected title"})
    invitation.expires_at = timezone.now() - timedelta(seconds=1)
    invitation.save(update_fields=["expires_at"])
    detail = authenticated(invitation.tenant).get(f"{API}{invitation.id}/")
    assert detail.data["status"] == "expired"
    assert not detail.data["actions"]["can_accept"]


def test_stale_refresh_cannot_overwrite_a_response(invitation):
    stale = TenancyInvitation.objects.get(pk=invitation.pk)
    assert respond(invitation, "rejected").status_code == 200
    # The old reader had an expired snapshot before the new decision arrived.
    stale.expires_at = timezone.now() - timedelta(seconds=1)
    refresh_effective_status(stale)
    invitation.refresh_from_db()
    assert invitation.status == stale.status == "rejected"
    assert invitation.revision == stale.revision == 2


def test_visit_continuation_preserves_pending_invitation_during_review(
    participants, owned_property
):
    owner, tenant, _ = participants
    created, _ = create_invitation(owner, tenant, owned_property)
    assert created.status_code == 201
    PropertyService.update_property(owned_property, {"title": "Corrected title"})
    visit = owned_property.visits.first()
    response = authenticated(tenant).get(
        f"/api/v1/properties/visits/requests/{visit.id}/"
    )
    assert response.status_code == 200
    continuation = response.data["rental_continuation"]
    assert continuation["status"] == "invitation_pending"
    assert continuation["blocked_reason"] == "property_review_pending"
    assert continuation["invitation_id"] == created.data["id"]


def test_push_retry_reuses_saved_invitation_and_notification(
    participants, owned_property
):
    owner, tenant, _ = participants
    DeviceToken.objects.create(
        user=tenant, token="invitation-review-device", device_type="android"
    )
    with patch(
        "core_apps.notifications.services.fcm_service.FCMService.send_push_to_device",
        return_value=False,
    ) as push:
        created, _ = create_invitation(owner, tenant, owned_property)
        assert created.status_code == 201
        assert push.call_count == 0
        notice = Notification.objects.get(notification_type="tenancy_invitation")
        delivery = PushDelivery.objects.get(notification=notice)
        dispatch()
    delivery.refresh_from_db()
    assert delivery.attempts == 1 and delivery.accepted_at is None
    # A newer response must not discard the older event or create a second operation.
    item = TenancyInvitation.objects.get(id=created.data["id"])
    assert respond(item, "accepted").status_code == 200
    PushDelivery.objects.filter(pk=delivery.pk).update(
        next_attempt_at=timezone.now() - timedelta(seconds=1)
    )
    with patch(
        "core_apps.notifications.services.fcm_service.FCMService.send_push_to_device",
        return_value=True,
    ) as push:
        assert dispatch() == 1
        assert push.call_count == 1
    delivery.refresh_from_db()
    assert delivery.notification_id == notice.pk and delivery.accepted_at
    assert TenancyInvitation.objects.count() == 1
    assert Notification.objects.filter(category="tenancy_invitation").count() == 2


def test_queued_event_rechecks_recipient_access(invitation, participants):
    DeviceToken.objects.create(
        user=invitation.tenant, token="invitation-access-device", device_type="android"
    )
    create_notification_for_invitation(None, invitation)
    delivery = PushDelivery.objects.get(
        notification__notification_type="tenancy_invitation"
    )
    TenancyInvitation.objects.filter(pk=invitation.pk).update(tenant=participants[2])
    with patch(
        "core_apps.notifications.services.fcm_service.FCMService.send_push_to_device"
    ) as push:
        dispatch()
        push.assert_not_called()
    delivery.refresh_from_db()
    assert delivery.suppressed


def test_hard_unavailability_still_revokes_and_cannot_be_reopened(invitation):
    prop = invitation.property
    prop.status, prop.is_verified = prop.Status.HIDDEN, False
    prop.save(update_fields=["status", "is_verified"])
    client = authenticated(invitation.tenant)
    assert client.get(f"{API}{invitation.id}/").data["status"] == "revoked"
    prop.status, prop.is_verified = prop.Status.VERIFIED, True
    prop.save(update_fields=["status", "is_verified"])
    assert client.get(f"{API}{invitation.id}/").data["status"] == "revoked"


def test_student_invitation_and_owner_reply_use_recipient_workspace(
    participants, owned_property
):
    owner, tenant, _ = participants
    owned_property.visits.update(renter_workspace="student")
    created, _ = create_invitation(owner, tenant, owned_property)
    assert created.status_code == 201
    notice = Notification.objects.get(notification_type="tenancy_invitation")
    assert notice.scope == notice.data["workspace"] == "student"
    item = TenancyInvitation.objects.get(id=created.data["id"])
    assert respond(item, "rejected").status_code == 200
    reply = Notification.objects.get(notification_type="tenancy_invitation_response")
    assert reply.user == owner and reply.scope == reply.data["workspace"] == "owner"


@pytest.mark.django_db(transaction=True)
def test_acceptance_and_listing_edit_preserve_the_invitation_under_contention(
    invitation,
):
    def execute(index):
        if index == 0:
            PropertyService.update_property(
                invitation.property, {"title": "Concurrent edit"}
            )
            return "edited"
        return respond(invitation, "accepted").status_code

    outcomes = parallel_calls(execute)
    assert outcomes[0] == "edited" and outcomes[1] in {200, 409}
    detail = authenticated(invitation.tenant).get(f"{API}{invitation.id}/")
    assert detail.status_code == 200
    assert detail.data["status"] == ("accepted" if outcomes[1] == 200 else "pending")
    assert not detail.data["eligible_for_lease"]
    assert detail.data["blocking_reasons"]
