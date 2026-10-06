import pytest
from core_apps.admin_api.models import KYCSubmission, UserReport, StaffProfile


@pytest.mark.django_db
def test_kyc_submission_str(user):
    sub = KYCSubmission.objects.create(
        profile=user.profile,
        status=KYCSubmission.Status.PENDING,
    )
    assert user.email in str(sub)


@pytest.mark.django_db
def test_user_report_str(user):
    report = UserReport.objects.create(
        reported_user=user,
        reason="Test violation",
    )
    assert user.email in str(report)


@pytest.mark.django_db
def test_staff_profile_str(user):
    staff = StaffProfile.objects.create(
        user=user,
        role_name=StaffProfile.RoleName.MAIN_ADMIN,
    )
    assert "Main Admin" in str(staff) or user.email in str(staff)
