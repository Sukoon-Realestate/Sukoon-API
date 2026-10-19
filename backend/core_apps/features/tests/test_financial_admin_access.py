"""Financial admin registration must not break anonymous login or stale sessions."""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from rest_framework.exceptions import PermissionDenied
from core_apps.features.models import RentalAuditEvent
from core_apps.features.services.financial_authority import require_financial_actor
from core_apps.users.models import User


@pytest.mark.django_db
def test_anonymous_admin_login_renders_without_financial_authority(client, settings):
    settings.STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
    response = client.get(reverse("admin:login"))
    assert response.status_code == 200
    assert b'name="username"' in response.content
    assert b'Inspect original evidence' not in response.content
    assert not RentalAuditEvent.objects.exists()


@pytest.mark.django_db
def test_anonymous_financial_review_denies_without_creating_an_actor_audit():
    with pytest.raises(PermissionDenied):
        require_financial_actor(AnonymousUser(), {"financial_approver"}, "chargeback.review")
    assert not RentalAuditEvent.objects.exists()


@pytest.mark.django_db
def test_removed_actor_snapshot_cannot_raise_a_server_error_or_retain_authority():
    user = User.objects.create_user(
        email="removed-finance@example.invalid", password="isolated-only", is_staff=True
    )
    identity = user.pk
    user.delete()
    user.pk = identity
    with pytest.raises(PermissionDenied):
        require_financial_actor(user, {"financial_approver"}, "chargeback.review")
    assert not RentalAuditEvent.objects.exists()
