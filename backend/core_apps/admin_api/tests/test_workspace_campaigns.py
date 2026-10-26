from datetime import timedelta
from uuid import uuid4
from unittest.mock import patch
import pytest
from django.utils import timezone
from core_apps.admin_api.models import CampaignDelivery, CampaignRecipient
from core_apps.admin_api.services.push_campaigns import (
    preview,
    transition,
    dispatch,
    payload,
)
from core_apps.admin_api.services.workspace_campaigns import eligible_spaces
from core_apps.notifications.models import DeviceToken, Notification
from core_apps.notifications.services import preferences
from core_apps.profiles.models import UserSettings
from core_apps.features.company_models import Company, CompanyMembership
from core_apps.features.student_models import StudentProfile
from core_apps.features.planning_models import HousingRequest
from core_apps.properties.models import Property, PropertyType, Governorate, City

pytestmark = pytest.mark.django_db


@pytest.fixture
def four_spaces(user, settings):
    settings.ADMIN_CAMPAIGNS_ENABLED = True
    UserSettings.objects.filter(user=user).update(promotions_and_updates=True)
    region = Governorate.objects.create(name="Campaign test")
    city = City.objects.create(name="Campaign city", governorate=region)
    kind, _ = PropertyType.objects.get_or_create(
        slug="apartment", defaults={"name": "Apartment"}
    )
    Property.objects.create(
        owner=user,
        title="Local only",
        property_type=kind,
        governorate=region,
        city=city,
    )
    StudentProfile.objects.create(user=user)
    company = Company.objects.create(
        name="Local test",
        registration_number="QA",
        contact_email="local@example.invalid",
        review_status="verified",
    )
    CompanyMembership.objects.create(user=user, company=company, is_employee=True)
    for scope in ("individual", "owner", "student", "company"):
        preferences.touch(user, scope)
    item = preferences.get(user, "company")
    item.push_enabled = False
    item.save()
    DeviceToken.objects.create(user=user, token="first-local-device")
    DeviceToken.objects.create(user=user, token="latest-local-device")
    return company


def campaign(actor):
    item = preview(
        actor,
        {
            "title": "Local QA",
            "body": "Synthetic",
            "audience": "all",
            "request_key": str(uuid4()),
        },
    )
    transition(
        actor, item.id, {"expected_revision": 1, "preview_digest": item.preview_digest}
    )
    return item


def run_dispatch(**kwargs):
    with patch(
        "core_apps.admin_api.services.workspace_campaigns.FCMService.get_credentials",
        return_value=object(),
    ):
        return dispatch(**kwargs)


def test_four_receipts_one_push_latest_enabled_space_and_independent_read(
    superuser, user, four_spaces
):
    item = campaign(superuser)
    report = payload(item)
    assert report["recipientCount"] == 1 and report["receiptCount"] == 4
    assert report["pushAccountCount"] == 1
    with patch(
        "core_apps.admin_api.services.workspace_campaigns.FCMService.send_push_to_device",
        return_value=True,
    ) as send:
        assert run_dispatch()["accepted_by_provider"] == 1
        assert run_dispatch()["accepted_by_provider"] == 0
        assert send.call_count == 1
        assert send.call_args.kwargs["token"] == "latest-local-device"
        assert send.call_args.kwargs["data"]["workspace"] == "student"
    assert set(Notification.objects.values_list("scope", flat=True)) == {
        "individual",
        "owner",
        "student",
        "company",
    }
    owner_notice = Notification.objects.get(scope="owner")
    owner_notice.is_read = True
    owner_notice.save()
    assert Notification.objects.filter(is_read=False).count() == 3


def test_changed_membership_and_push_preference_rechecked(superuser, user, four_spaces):
    campaign(superuser)
    CompanyMembership.objects.filter(user=user).update(is_active=False)
    preferences.NotificationScopePreference.objects.filter(
        user=user, scope="student"
    ).update(push_enabled=False)
    with patch(
        "core_apps.admin_api.services.workspace_campaigns.FCMService.send_push_to_device",
        return_value=True,
    ) as send:
        run_dispatch()
        assert send.call_args.kwargs["data"]["workspace"] == "owner"
    assert Notification.objects.count() == 3
    assert CampaignRecipient.objects.get(workspace="company").receipt_state == "skipped"


def test_cancel_after_partial_send_preserves_delivered_receipts(
    superuser, user, another_user, four_spaces
):
    UserSettings.objects.filter(user=another_user).update(promotions_and_updates=True)
    preferences.touch(another_user, "individual")
    DeviceToken.objects.create(user=another_user, token="other-local-device")
    item = campaign(superuser)
    with patch(
        "core_apps.admin_api.services.workspace_campaigns.FCMService.send_push_to_device",
        return_value=True,
    ) as send:
        run_dispatch(limit=1)
        item.refresh_from_db()
        transition(
            superuser,
            item.id,
            {"expected_revision": item.revision, "preview_digest": item.preview_digest},
            cancel=True,
        )
        run_dispatch()
        assert send.call_count == 1
    assert Notification.objects.filter(user=user).count() == 4
    assert not Notification.objects.filter(user=another_user).exists()
    assert CampaignDelivery.objects.filter(state="cancelled").count() == 1


def test_tenant_audience_uses_actual_relationship_not_absence_of_property(
    user, four_spaces
):
    assert eligible_spaces(user, "tenants") == set()
    HousingRequest.objects.create(
        user=user, title="Housing needed", expires_at=timezone.now() + timedelta(days=2)
    )
    assert eligible_spaces(user, "tenants") == {"individual", "student"}
    assert eligible_spaces(user, "landlords") == {"owner"}


def test_no_recorded_workspace_use_creates_receipt_without_inventing_push_target(
    superuser, user, settings
):
    settings.ADMIN_CAMPAIGNS_ENABLED = True
    UserSettings.objects.filter(user=user).update(promotions_and_updates=True)
    DeviceToken.objects.create(user=user, token="unused-workspace-device")
    campaign(superuser)
    with patch(
        "core_apps.admin_api.services.workspace_campaigns.FCMService.send_push_to_device"
    ) as send:
        run_dispatch()
        send.assert_not_called()
    assert Notification.objects.get().scope == "individual"
    assert not CampaignDelivery.objects.exists()
