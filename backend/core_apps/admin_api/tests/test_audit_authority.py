import pytest
from django.urls import reverse
from rest_framework.exceptions import PermissionDenied, NotFound

from core_apps.admin_api.models import StaffProfile, StaffAuthorityAudit
from core_apps.admin_api.services.staff_service import (
    invite_staff_member,
    remove_staff_member,
)
from core_apps.admin_api.services.user_service import suspend_user

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "role", ["support", "main_admin", "kyc_reviewer", "financial_approver"]
)
def test_staff_cannot_grant_system_owner(api_client, user, role):
    StaffProfile.objects.create(user=user, role_name=role)
    api_client.force_authenticate(user)
    response = api_client.post(
        reverse("admin-staff-invite"),
        {
            "name": "Unauthorized grant",
            "email": "new@example.com",
            "role_name": "system_owner",
            "reason": "Test",
        },
    )
    assert response.status_code == 403
    assert not StaffProfile.objects.filter(role_name="system_owner").exists()


def test_current_authority_overrides_cached_user(superuser, user):
    profile = StaffProfile.objects.create(user=user, role_name="system_owner")
    user.staff_profile  # Populate the stale relation deliberately.
    StaffProfile.objects.filter(pk=profile.pk).update(is_active=False)
    with pytest.raises(PermissionDenied):
        invite_staff_member(
            "new@example.com", "New Staff", "support", actor=user, reason="Test"
        )


def test_grant_and_revoke_are_audited_and_do_not_verify_identity(superuser):
    staff = invite_staff_member(
        "new@example.com", "New Staff", "support", actor=superuser, reason="Coverage"
    )
    assert not staff.user.is_verified
    remove_staff_member(staff.id, actor=superuser, reason="End of assignment")
    staff.refresh_from_db()
    assert not staff.is_active
    assert list(
        StaffAuthorityAudit.objects.order_by("id").values_list("action", flat=True)
    ) == ["grant", "revoke"]


def test_system_owner_cannot_remove_self(user):
    staff = StaffProfile.objects.create(user=user, role_name="system_owner")
    with pytest.raises(PermissionDenied):
        remove_staff_member(staff.id, actor=user, reason="Self removal")
    staff.refresh_from_db()
    assert staff.is_active


def test_inactive_profile_cannot_use_legacy_staff_flag(api_client, user):
    user.is_staff = True
    user.save()
    StaffProfile.objects.create(user=user, role_name="support", is_active=False)
    api_client.force_authenticate(user)
    assert api_client.get(reverse("admin-staff-list")).status_code == 403


def test_permissions_matrix_cannot_acknowledge_unstored_write(api_client, superuser):
    api_client.force_authenticate(superuser)
    assert (
        api_client.patch(
            reverse("admin-permissions-matrix"), {"arbitrary": True}
        ).status_code
        == 405
    )


def test_mutation_rejects_ambiguous_account_alias(user, another_user, superuser):
    another_user.first_name = user.first_name
    another_user.save()
    with pytest.raises(NotFound):
        suspend_user(user.first_name, superuser)
    user.refresh_from_db()
    another_user.refresh_from_db()
    assert user.is_active and another_user.is_active
