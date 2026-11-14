"""Raw HTTP methods/bytes/headers and native admin current-authority gates."""

from unittest.mock import patch

import pytest
from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.test import RequestFactory
from django.urls import resolve, reverse

from core_apps.admin_api.models import StaffProfile
from core_apps.common.admin_site import RecoveryAdminAuthenticationForm
from core_apps.common.app_associations import (
    AndroidAssetLinksView,
    AppleAppSiteAssociationView,
)
from core_apps.common.runtime_views import HealthView


@pytest.mark.parametrize(
    "method", ["GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "TRACE"]
)
@pytest.mark.django_db
def test_raw_health_preserves_method_contract(method):
    request = RequestFactory().generic(method, "/health/")
    assert resolve("/health/").func.view_class is HealthView
    with patch("core_apps.common.runtime_views.redis_client") as connect:
        response = HealthView.as_view()(request)
        assert response.status_code == 200
        assert response.content == b'{"ready": true}'
        assert response["Content-Type"] == "application/json"
        connect.side_effect = RuntimeError("private redis credentials")
        response = HealthView.as_view()(request)
        assert response.status_code == 503 and response.content == b'{"ready": false}'


@pytest.mark.parametrize("cls", [AndroidAssetLinksView, AppleAppSiteAssociationView])
@pytest.mark.parametrize("method", ["POST", "HEAD", "OPTIONS", "PUT", "DELETE"])
def test_association_adapters_retain_get_only_allow_header(cls, method):
    response = cls.as_view()(RequestFactory().generic(method, "/.well-known/"))
    assert response.status_code == 405
    assert response["Allow"] == "GET" and response.content == b""


@pytest.mark.django_db
def test_disabled_staff_profile_cannot_open_native_admin_or_log_in(client, superuser):
    StaffProfile.objects.create(
        user=superuser, role_name="system_owner", is_active=False
    )
    client.force_login(superuser)
    assert client.get(reverse("admin:index")).status_code == 403
    with pytest.raises(ValidationError):
        RecoveryAdminAuthenticationForm().confirm_login_allowed(superuser)


@pytest.mark.django_db
def test_native_admin_write_checks_sensitive_factor_after_request_snapshot(superuser):
    request = RequestFactory().post("/admin/")
    request.user = superuser
    with patch(
        "core_apps.users.services.totp.require_sensitive_access",
        side_effect=DRFPermissionDenied("Restricted"),
    ):
        from django.core.exceptions import PermissionDenied

        with pytest.raises(PermissionDenied):
            admin.site.has_permission(request)


@pytest.mark.parametrize("failure", ["provider", "programming"])
def test_private_delete_keeps_original_on_failure_and_classifies_provider(
    failure, settings, tmp_path
):
    from cloudinary.exceptions import GeneralError
    from core_apps.common.private_storage import PrivateStorageUnavailable
    from core_apps.support.storage import SupportPrivateStorage

    settings.SUPPORT_PRIVATE_STORAGE_PROVIDER = "cloudinary"
    settings.SUPPORT_PRIVATE_MEDIA_ROOT = str(tmp_path)
    original = tmp_path / "retained.bin"
    original.write_bytes(b"synthetic original")
    error = (
        GeneralError("private provider details")
        if failure == "provider"
        else TypeError("programming fault")
    )
    with patch("core_apps.virtual_tours.cloudinary_storage.remove", side_effect=error):
        with pytest.raises(
            PrivateStorageUnavailable if failure == "provider" else TypeError
        ):
            SupportPrivateStorage().delete("retained.bin")
    assert original.read_bytes() == b"synthetic original"
