"""Four independent feeds/preferences; provider calls are local test doubles."""

from unittest.mock import patch
import pytest
from django.urls import reverse
from core_apps.notifications.models import Notification, DeviceToken, PushDelivery
from core_apps.notifications.services import preferences
from core_apps.notifications.services.push_delivery import queue_notification, dispatch
from core_apps.profiles.services import ProfileService
from core_apps.profiles.models import UserSettings

pytestmark = pytest.mark.django_db
SPACES = ("individual", "owner", "student", "company")


def test_background_badges_do_not_change_last_used_campaign_target(auth_client, user):
    for space in SPACES:
        assert (
            auth_client.get(
                "/api/v1/features/v1/workspace-summary/", {"scope": space}
            ).status_code
            == 200
        )
        assert preferences.get(user, space).last_used_at is None
    assert (
        auth_client.get(
            "/api/v1/features/v1/workspace-summary/",
            {
                "scope": "company",
                "active_workspace": "true",
            },
        ).status_code
        == 200
    )
    visited = preferences.get(user, "company").last_used_at
    assert visited is not None
    auth_client.get("/api/v1/features/v1/workspace-summary/", {"scope": "individual"})
    assert preferences.get(user, "individual").last_used_at is None
    assert preferences.get(user, "company").last_used_at == visited


def test_account_with_four_spaces_has_independent_feed_count_and_read_all(
    auth_client, user, another_user
):
    notices = {
        space: Notification.objects.create(
            user=user, title=space, data={"workspace": space}
        )
        for space in SPACES
    }
    account = Notification.objects.create(
        user=user, title="Account", data={"scope": "account"}
    )
    foreign = Notification.objects.create(
        user=another_user, title="Private", data={"workspace": "owner"}
    )
    for scope, notice in notices.items():
        result = auth_client.get(reverse("notification-list"), {"scope": scope})
        assert result.status_code == 200
        assert [row["id"] for row in result.data["results"]] == [str(notice.id)]
        assert result.data["unread_count"] == 1
    assert (
        auth_client.post(reverse("notification-mark-all-read") + "?scope=owner").data[
            "marked_count"
        ]
        == 1
    )
    for scope, notice in notices.items():
        notice.refresh_from_db()
        assert notice.is_read == (scope == "owner")
        assert auth_client.get(
            reverse("notification-unread-count"), {"scope": scope}
        ).data["unread_count"] == int(scope != "owner")
    assert (
        ProfileService.get_owner_unread_counts(user)["unread_notifications_count"] == 0
    )
    assert (
        ProfileService.get_tenant_unread_counts(user, scope="company")[
            "unread_notifications_count"
        ]
        == 1
    )
    account.refresh_from_db()
    foreign.refresh_from_db()
    assert not account.is_read and not foreign.is_read


def test_explicit_owner_wins_over_company_action_and_old_notice_keeps_identity(user):
    notice = Notification.objects.create(
        user=user,
        title="Owner contract",
        data={
            "workspace": "owner",
            "action_type": "open_company_contract",
            "revision": 1,
        },
    )
    assert notice.scope == "owner"
    identity = notice.id
    notice.is_read = True
    notice.save(update_fields=["is_read"])
    assert notice.id == identity and notice.data["revision"] == 1


def test_missing_historical_context_is_preserved_once_in_account_history(user):
    notice = Notification.objects.create(user=user, title="Old notice without context")
    assert notice.scope == "account"
    assert Notification.objects.filter(user=user).count() == 1


def test_scope_preferences_preserve_opt_outs_and_do_not_change_another_scope(
    auth_client, user
):
    UserSettings.objects.filter(user=user).update(owner_messages=False)
    url = reverse("notification-settings")
    for space in SPACES:
        result = auth_client.get(url, {"scope": space})
        assert result.data["owner_messages"] is False
    result = auth_client.patch(
        url + "?scope=student",
        {"push_enabled": False, "owner_messages": True},
        format="json",
    )
    assert result.status_code == 200
    assert not result.data["push_enabled"] and result.data["owner_messages"]
    for space in ("individual", "owner", "company"):
        assert preferences.get(user, space).push_enabled
        assert not preferences.get(user, space).owner_messages
    account = auth_client.get(url, {"scope": "account"}).data
    assert set(row["key"] for row in account["sections"]["notifications"]["items"]) == {
        "push_enabled",
        "security_alerts",
    }
    assert (
        auth_client.patch(
            url + "?scope=owner", {"security_alerts": False}, format="json"
        ).status_code
        == 400
    )
    assert (
        auth_client.patch(
            url + "?scope=company", {"push_enabled": "false"}, format="json"
        ).status_code
        == 400
    )


def test_retry_checks_current_scope_preference_without_repeating_business(user):
    DeviceToken.objects.create(user=user, token="local-test-device")
    owner = Notification.objects.create(
        user=user, title="Owner", data={"workspace": "owner"}
    )
    student = Notification.objects.create(
        user=user, title="Student", data={"workspace": "student"}
    )
    queue_notification(owner)
    queue_notification(student)
    pref = preferences.get(user, "owner")
    pref.push_enabled = False
    pref.save(update_fields=["push_enabled"])
    with patch(
        "core_apps.notifications.services.push_delivery.FCMService.send_push_to_device",
        return_value=True,
    ) as send:
        assert dispatch() == 1
        assert send.call_count == 1
        assert send.call_args.kwargs["data"]["workspace"] == "student"
    assert Notification.objects.filter(user=user).count() == 2
    assert PushDelivery.objects.get(notification=owner).suppressed
    assert not owner.is_read


def test_invalid_scope_does_not_mark_anything(auth_client, user):
    Notification.objects.create(user=user, title="Owner", data={"workspace": "owner"})
    for scope in ("all", "community", "unknown"):
        assert (
            auth_client.post(
                reverse("notification-mark-all-read") + f"?scope={scope}"
            ).status_code
            == 400
        )
    assert not Notification.objects.filter(is_read=True).exists()
