from datetime import timedelta
from unittest.mock import patch
import json
import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from core_apps.users.models import AuthSession
from core_apps.users.services.sessions import issue_refresh
from core_apps.notifications.models import DeviceToken
from core_apps.notifications.services import FCMService
from core_apps.features.tests.test_recovery_fence import recovery
from core_apps.features.tests.test_rental_phase3 import phase3_lease

pytestmark = pytest.mark.django_db


def test_statement_export_requires_approved_sensitive_policy(phase3_lease, settings):
    import uuid
    from core_apps.features.models import RentalDocument

    _, tenant, lease = phase3_lease
    settings.SECURITY_TEST_BYPASS = False
    token = issue_refresh(tenant)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    response = client.post(
        "/api/v1/features/v1/rental-statements/",
        {"lease_id": str(lease.id), "request_key": str(uuid.uuid4())},
        format="json",
    )
    assert response.status_code == 409
    assert not RentalDocument.objects.filter(document_type="statement").exists()


@pytest.mark.parametrize("path", ["set_email", "reset_email", "reset_email_confirm"])
def test_old_identity_routes_cannot_bypass_new_contact_verification(user, path):
    original = user.email
    client = APIClient()
    client.force_authenticate(user)
    response = client.post(
        f"/api/v1/auth/users/{path}/",
        {"new_email": "synthetic-other@example.invalid"},
        format="json",
    )
    assert response.status_code == 403
    user.refresh_from_db()
    assert user.email == original


def test_expired_or_wrong_account_push_sessions_are_not_delivery_targets(
    user, another_user
):
    token = issue_refresh(user)
    session = AuthSession.objects.get(id=token["session_id"])
    DeviceToken.objects.create(
        user=user, token="synthetic-session-device", auth_session=session
    )
    other = issue_refresh(another_user)
    DeviceToken.objects.create(
        user=user,
        token="synthetic-wrong-account-device",
        auth_session=AuthSession.objects.get(id=other["session_id"]),
    )
    with patch.object(FCMService, "send_push_to_device", return_value=True) as send:
        assert FCMService.send_push_to_user(user, "Generic", "Generic") == 1
        assert send.call_args.kwargs["token"] == "synthetic-session-device"
        session.expires_at = timezone.now() - timedelta(seconds=1)
        session.save(update_fields=["expires_at"])
        send.reset_mock()
        assert FCMService.send_push_to_user(user, "Generic", "Generic") == 0
        send.assert_not_called()


def test_deferred_global_restore_gate_does_not_replace_company_session_authority(
    recovery, user
):
    path, state = recovery
    path.write_text(json.dumps({**state, "mode": "quarantined"}))
    fresh = issue_refresh(user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {fresh.access_token}")
    response = client.get("/api/v1/features/v1/companies/")
    assert response.status_code == 200
    assert response.data["results"] == []
    # The deployed account session fence remains authoritative even while the
    # separate global restore-control integration is deferred.
    user.security_epoch += 1
    user.save(update_fields=["security_epoch"])
    assert client.get("/api/v1/features/v1/companies/").status_code == 401
