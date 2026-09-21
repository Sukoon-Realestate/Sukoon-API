import pytest
from core_apps.admin_api.services import (
    get_dashboard_overview_stats,
    suspend_user,
    unsuspend_user,
    approve_kyc_submission,
    reject_kyc_submission,
    invite_staff_member,
    remove_staff_member,
)
from core_apps.admin_api.models import KYCSubmission


@pytest.mark.django_db
def test_dashboard_stats(user):
    stats = get_dashboard_overview_stats()
    assert "metrics" in stats
    assert "user_distribution" in stats
    assert stats["user_distribution"]["total"] >= 1


@pytest.mark.django_db
def test_user_suspend_unsuspend(user, superuser):
    suspend_user(user.id, admin_user=superuser, reason="Violation test")
    user.refresh_from_db()
    assert user.is_active is False

    unsuspend_user(user.id, admin_user=superuser)
    user.refresh_from_db()
    assert user.is_active is True


@pytest.mark.django_db
def test_kyc_approve_reject(user, superuser):
    sub = KYCSubmission.objects.create(profile=user.profile, status=KYCSubmission.Status.PENDING)
    approve_kyc_submission(sub.id, reviewer=superuser)
    sub.refresh_from_db()
    user.refresh_from_db()
    assert sub.status == KYCSubmission.Status.APPROVED
    assert user.is_verified is True

    reject_kyc_submission(sub.id, reviewer=superuser, reason="Document blurred")
    sub.refresh_from_db()
    user.refresh_from_db()
    assert sub.status == KYCSubmission.Status.REJECTED
    assert user.is_verified is False


@pytest.mark.django_db
def test_staff_invite_and_remove(superuser):
    staff = invite_staff_member("newstaff@example.com", "Test Admin", "مشرف رئيسي")
    assert staff.user.is_staff is True
    assert staff.is_active is True

    remove_staff_member(staff.id)
    staff.refresh_from_db()
    assert staff.is_active is False
