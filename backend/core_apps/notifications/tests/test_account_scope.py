"""Account events do not change workspace feeds, badges or read-all receipts."""

import pytest
from django.urls import reverse
from core_apps.notifications.models import Notification
from core_apps.profiles.services import ProfileService


@pytest.mark.django_db
def test_account_and_workspace_history_are_independent(auth_client, user, another_user):
    account = Notification.objects.create(
        user=user, title="Recovery changed", data={"scope": "account"}
    )
    historical_security = Notification.objects.create(
        user=user, title="Security", notification_type="security_alert"
    )
    workspace = Notification.objects.create(
        user=user, title="Visit", data={"workspace": "owner"}
    )
    foreign = Notification.objects.create(
        user=another_user, title="Other account", data={"scope": "account"}
    )
    listing = reverse("notification-list")
    payload = auth_client.get(listing, {"scope": "owner"}).data
    assert payload["unread_count"] == 1
    assert [row["id"] for row in payload["results"]] == [str(workspace.id)]
    payload = auth_client.get(listing, {"scope": "account"}).data
    assert payload["unread_count"] == 2
    assert {row["id"] for row in payload["results"]} == {
        str(account.id),
        str(historical_security.id),
    }
    assert all(row["data"]["scope"] == "account" for row in payload["results"])
    assert (
        ProfileService.get_owner_unread_counts(user)["unread_notifications_count"] == 1
    )
    assert (
        ProfileService.get_tenant_unread_counts(user)["unread_notifications_count"] == 0
    )
    result = auth_client.post(reverse("notification-mark-all-read") + "?scope=account")
    assert result.status_code == 200
    assert result.data["marked_count"] == 2
    workspace.refresh_from_db()
    foreign.refresh_from_db()
    assert not workspace.is_read and not foreign.is_read
    assert (
        auth_client.get(reverse("notification-unread-count"), {"scope": "owner"}).data["unread_count"] == 1
    )
    assert (
        auth_client.get(
            reverse("notification-unread-count"), {"scope": "account"}
        ).data["unread_count"]
        == 0
    )


@pytest.mark.django_db
def test_workspace_mark_all_preserves_account_history(auth_client, user):
    account = Notification.objects.create(
        user=user, title="Account", data={"scope": "account"}
    )
    Notification.objects.create(
        user=user, title="Workspace", data={"workspace": "individual"}
    )
    result = auth_client.post(reverse("notification-mark-all-read"))
    assert result.data["marked_count"] == 1
    account.refresh_from_db()
    assert not account.is_read
    assert (
        auth_client.post(
            reverse("notification-mark-all-read") + "?scope=all"
        ).status_code
        == 400
    )
