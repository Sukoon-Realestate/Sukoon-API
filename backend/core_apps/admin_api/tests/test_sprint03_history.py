"""Historical reachability, stable SQL pages and actual campaign recipient caps."""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from core_apps.admin_api.filters import AdminUserFilter
from core_apps.admin_api.models import (
    KYCSubmission,
    StaffAuthorityAudit,
    PlatformPreferenceAudit,
    PushCampaign,
)
from core_apps.admin_api.services.financials_service_parts.get_transactions_list import (
    get_transactions_list,
)
from core_apps.admin_api.services.system_service_parts.get_audit_logs import get_audit_logs
from core_apps.admin_api.services import workspace_campaigns
from core_apps.features.models import PaymentAttempt, PaymentQuote, RentInvoice
from core_apps.profiles.models import UserSettings
from core_apps.users.models import User

pytestmark = pytest.mark.django_db


def test_current_kyc_filters_ignore_superseded_and_return_distinct(user, another_user):
    KYCSubmission.objects.create(
        profile=user.profile, status="rejected", superseded_at=timezone.now()
    )
    KYCSubmission.objects.create(profile=user.profile, status="pending")
    KYCSubmission.objects.create(profile=user.profile, status="pending")
    KYCSubmission.objects.create(profile=another_user.profile, status="pending")
    KYCSubmission.objects.create(profile=another_user.profile, status="rejected")
    qs = User.objects.all()
    assert list(AdminUserFilter({"kyc_status": "pending"}, queryset=qs).qs) == [user]
    assert list(AdminUserFilter({"kyc_status": "rejected"}, queryset=qs).qs) == [another_user]
    User.objects.filter(pk=user.pk).update(is_verified=True)
    assert not AdminUserFilter({"kyc_status": "pending"}, queryset=qs).qs.exists()
    assert list(AdminUserFilter({"kyc_status": "verified"}, queryset=qs).qs) == [user]


def test_payment_history_past_500_stable_pages_search_and_bounded_hydration(
    user, django_assert_num_queries
):
    invoice = RentInvoice.objects.create(
        payer=user,
        purpose="subscription",
        business_reference="historical-subscription",
        reference="historical-invoice",
        due_date=date.today(),
        amount_minor=100,
    )
    quote = PaymentQuote.objects.create(
        invoice=invoice,
        request_key=uuid4(),
        invoice_revision=1,
        payer_amount_minor=100,
        policy_version="test",
        fingerprint="test",
        expires_at=timezone.now() + timedelta(days=1),
    )
    PaymentAttempt.objects.bulk_create(
        [
            PaymentAttempt(
                invoice=invoice,
                quote=quote,
                payer=user,
                request_key=uuid4(),
                invoice_revision=1,
                amount_minor=100,
                payment_status="captured",
            )
            for _ in range(505)
        ]
    )
    PaymentAttempt.objects.update(created_at=timezone.now() - timedelta(days=500))
    page = get_transactions_list(search="historical-invoice", status_filter="paid", paginated=True)
    assert page.count() == 505
    with django_assert_num_queries(2):
        first = page[:10]
    assert len(first) == 10
    assert len(page[500:510]) == 5
    all_rows = get_transactions_list(status_filter="paid")
    assert first == all_rows[:10] and page[500:510] == all_rows[500:510]
    assert first == page[:10]


def test_audit_history_past_100_and_cross_source_stable_totals(
    user, another_user, django_assert_num_queries
):
    StaffAuthorityAudit.objects.bulk_create(
        [
            StaffAuthorityAudit(
                actor=user, target=another_user, action="history-target", reason="past cap"
            )
            for _ in range(105)
        ]
    )
    PlatformPreferenceAudit.objects.create(actor=user, revision=1, before={}, after={})
    page = get_audit_logs(paginated=True)
    assert page.count() == 106
    with django_assert_num_queries(3):
        rows = page[:10]
    assert len(rows) == 10
    assert len(page[100:110]) == 6
    filtered = get_audit_logs(search="history-target", paginated=True)
    assert filtered.count() == 105 and len(filtered[100:110]) == 5
    assert page[:10] == get_audit_logs()[:10]


def test_campaign_cap_counts_eligible_accounts_and_scan_budget_separately(
    user, another_user, superuser, settings, monkeypatch
):
    settings.ADMIN_CAMPAIGN_RECIPIENT_LIMIT = 1
    settings.ADMIN_CAMPAIGN_SCAN_LIMIT = 100
    UserSettings.objects.all().update(promotions_and_updates=True)
    monkeypatch.setattr(
        workspace_campaigns,
        "consented_spaces",
        lambda account, audience: {"individual"} if account.pk == user.pk else set(),
    )
    command = {
        "title": "Synthetic",
        "body": "Local only",
        "audience": "all",
        "request_key": str(uuid4()),
    }
    item = workspace_campaigns.preview(superuser, command)
    assert item.recipients.count() == 1
    monkeypatch.setattr(workspace_campaigns, "consented_spaces", lambda *args: {"individual"})
    with pytest.raises(ValidationError, match="eligible accounts"):
        workspace_campaigns.preview(superuser, {**command, "request_key": str(uuid4())})
    settings.ADMIN_CAMPAIGN_SCAN_LIMIT = 1
    monkeypatch.setattr(workspace_campaigns, "consented_spaces", lambda *args: set())
    with pytest.raises(ValidationError, match="scan budget"):
        workspace_campaigns.preview(superuser, {**command, "request_key": str(uuid4())})
    assert PushCampaign.objects.count() == 1


def test_campaign_large_opted_in_population_small_eligible_audience(superuser, monkeypatch):
    users = User.objects.bulk_create(
        [
            User(
                email=f"sprint03-{index}@example.invalid",
                password="!",
                first_name="Synthetic",
                last_name="Audience",
            )
            for index in range(5001)
        ]
    )
    UserSettings.objects.bulk_create(
        [UserSettings(user=account, promotions_and_updates=True) for account in users]
    )
    target = users[-1].pk
    monkeypatch.setattr(
        workspace_campaigns,
        "consented_spaces",
        lambda account, audience: {"individual"} if account.pk == target else set(),
    )
    item = workspace_campaigns.preview(
        superuser,
        {
            "title": "Synthetic",
            "body": "Local only",
            "audience": "landlords",
            "request_key": str(uuid4()),
        },
    )
    assert list(item.recipients.values_list("user_id", flat=True)) == [target]
