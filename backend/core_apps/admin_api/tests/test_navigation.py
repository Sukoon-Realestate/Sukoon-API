from uuid import uuid4
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from core_apps.admin_api.models import StaffProfile, UserReport
from core_apps.admin_api.services.report_service import get_reports_overview_stats

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "role,support,closure,finance,properties,users",
    [
        ("system_owner", True, True, True, True, True),
        ("main_admin", False, False, False, True, True),
        ("support", True, False, False, False, False),
        ("support_supervisor", True, False, False, False, False),
        ("account_closure_reviewer", False, True, False, False, False),
        ("financial_approver", False, False, True, False, False),
        ("payout_operator", False, False, True, False, False),
        ("refund_operator", False, False, True, False, False),
        ("psp_reconciliation", False, False, True, False, False),
        ("property_reviewer", False, False, False, True, False),
        ("kyc_reviewer", False, False, False, False, False),
        ("dispute_resolver", False, False, False, False, False),
    ],
)
def test_navigation_keeps_existing_authorities_separate(
    api_client, user, role, support, closure, finance, properties, users
):
    StaffProfile.objects.create(user=user, role_name=role)
    api_client.force_authenticate(user)
    result = api_client.get(reverse("admin-session"))
    assert result.status_code == 200
    assert result["Cache-Control"] == "private, no-store"
    paths = result.data["allowedPaths"]
    assert len(paths) == len(set(paths))
    assert "/security" in paths
    for path, allowed in [
        ("/support", support),
        ("/account-closure", closure),
        ("/financials", finance),
        ("/properties", properties),
        ("/users", users),
    ]:
        assert (path in paths) is allowed
    assert ("/system/health" in paths) is (role == "system_owner")
    assert ("/financials/payouts" in paths) is (role in {"payout_operator", "psp_reconciliation"})
    assert ("/financials/refunds" in paths) is (role in {"refund_operator", "financial_approver", "psp_reconciliation"})


def test_independent_recovery_account_stays_limited_even_as_superuser(
    api_client, superuser
):
    profile = StaffProfile.objects.create(
        user=superuser, role_name="security_recovery_reviewer"
    )
    api_client.force_authenticate(superuser)
    result = api_client.get(reverse("admin-session"))
    assert result.status_code == 200
    assert result.data["role"] == "security_recovery_reviewer"
    assert result.data["allowedPaths"] == ["/security"]
    assert result.data["canManageStaff"] is False
    assert api_client.get(reverse("admin-system-health")).status_code == 403
    profile.is_active = False
    profile.save(update_fields=["is_active"])
    assert api_client.get(reverse("admin-session")).status_code == 403


def test_navigation_uses_current_profile_after_role_change(api_client, user):
    profile = StaffProfile.objects.create(user=user, role_name="system_owner")
    api_client.force_authenticate(user)
    assert (
        "/financials" in api_client.get(reverse("admin-session")).data["allowedPaths"]
    )
    StaffProfile.objects.filter(pk=profile.pk).update(role_name="support")
    result = api_client.get(reverse("admin-session"))
    assert result.data["role"] == "support"
    assert "/financials" not in result.data["allowedPaths"]
    StaffProfile.objects.filter(pk=profile.pk).update(is_active=False)
    assert api_client.get(reverse("admin-session")).status_code == 403


def test_report_filter_keeps_exact_identity_across_statuses(
    api_client, user, another_user, superuser
):
    target = UserReport.objects.create(
        reporter=user,
        reported_user=another_user,
        reason="Historical resolved report",
        status="dismissed",
    )
    UserReport.objects.create(
        reporter=user,
        reported_user=another_user,
        reason="A different active report",
        status="active",
    )
    api_client.force_authenticate(superuser)
    endpoint = "/api/v1/admin/reports/"
    result = api_client.get(endpoint, {"id": str(target.id)})
    assert result.status_code == 200
    assert [str(item["id"]) for item in result.data["results"]] == [str(target.id)]
    assert api_client.get(endpoint, {"id": str(uuid4())}).data["results"] == []
    assert api_client.get(endpoint, {"id": "SUP-201"}).status_code == 400


def test_report_overview_uses_all_reason_counts_and_excludes_future_decisions(
    user, another_user
):
    now = timezone.now()
    UserReport.objects.create(
        reporter=user,
        reported_user=another_user,
        reason="Other reason",
        reason_type="other",
        status="dismissed",
        reviewed_at=now,
    )
    UserReport.objects.create(
        reporter=user,
        reported_user=another_user,
        reason="Future decision",
        reason_type="fraud",
        status="banned",
        reviewed_at=now + timedelta(days=1),
    )
    result = get_reports_overview_stats()
    assert result["solvedToday"] == 1
    assert sum(item["count"] for item in result["disputeReasons"]) == 2
    assert result["avgResolutionTime"] == "غير متاح"
    assert timezone.datetime.fromisoformat(result["measured_at"]) >= now
