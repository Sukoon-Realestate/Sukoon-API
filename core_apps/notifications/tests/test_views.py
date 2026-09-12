import uuid
import pytest
from django.urls import reverse
from rest_framework import status

from core_apps.notifications.models import DeviceToken, Notification

NOTIFICATIONS_LIST_URL = reverse("notification-list")
NOTIFICATIONS_UNREAD_COUNT_URL = reverse("notification-unread-count")
NOTIFICATIONS_MARK_ALL_READ_URL = reverse("notification-mark-all-read")
NOTIFICATIONS_SETTINGS_URL = reverse("notification-settings")
DEVICE_TOKEN_CREATE_URL = reverse("device-token-create")
DEVICE_TOKEN_DELETE_URL = reverse("device-token-delete")


@pytest.mark.django_db
class TestNotificationListView:
    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(NOTIFICATIONS_LIST_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_notifications_happy_path(self, auth_client, user):
        n1 = Notification.objects.create(
            user=user,
            title="تم قبول طلب زيارتك",
            body="وافق المالك على موعد الزيارة",
            category="حجز زيارة",
            icon_type="check_circle",
            is_read=False,
        )
        n2 = Notification.objects.create(
            user=user,
            title="رسالة جديدة",
            body="مرحبا بك",
            category="الرسائل",
            icon_type="chat",
            is_read=True,
        )

        response = auth_client.get(NOTIFICATIONS_LIST_URL)
        assert response.status_code == status.HTTP_200_OK

        data = response.data
        assert "results" in data
        assert len(data["results"]) == 2
        assert data["unread_count"] == 1
        assert data["results"][0]["title"] == "رسالة جديدة"
        assert data["results"][1]["title"] == "تم قبول طلب زيارتك"

    def test_list_notifications_filter_unread(self, auth_client, user):
        Notification.objects.create(user=user, title="Unread", is_read=False)
        Notification.objects.create(user=user, title="Read", is_read=True)

        response = auth_client.get(f"{NOTIFICATIONS_LIST_URL}?unread=true")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["title"] == "Unread"


@pytest.mark.django_db
class TestNotificationDetailView:
    def test_unauthenticated_returns_401(self, api_client):
        url = reverse("notification-detail", kwargs={"pk": uuid.uuid4()})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_not_found_returns_404(self, auth_client):
        url = reverse("notification-detail", kwargs={"pk": uuid.uuid4()})
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_happy_path_marks_read_and_formats_screen_2(self, auth_client, user):
        notif = Notification.objects.create(
            user=user,
            title="تم قبول طلب زيارتك",
            body="وافق المالك أحمد محمد على موعد الزيارة. يُرجى الحضور في الوقت المحدد للاطلاع على الشقة.",
            category="حجز زيارة",
            icon_type="check_circle",
            is_read=False,
            data={
                "appointment_date": "الثلاثاء 14 يناير",
                "appointment_time": "3:00 م",
                "address": "مدينة نصر - شارع عباس العقاد",
                "visit_id": "11111111-2222-3333-4444-555555555555",
            },
        )
        url = reverse("notification-detail", kwargs={"pk": notif.id})
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        data = response.data
        assert data["title"] == "تم قبول طلب زيارتك"
        assert data["is_read"] is True
        assert data["appointment_details"]["title"] == "تفاصيل الموعد"
        assert "مدينة نصر" in data["appointment_details"]["location_label"]
        assert data["actions"]["primary"]["label"] == "عرض الزيارة"
        assert data["actions"]["secondary"]["label"] == "تجاهل"

        notif.refresh_from_db()
        assert notif.is_read is True


@pytest.mark.django_db
class TestNotificationMarkReadView:
    def test_unauthenticated_returns_401(self, api_client):
        url = reverse("notification-mark-read", kwargs={"pk": uuid.uuid4()})
        response = api_client.patch(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_not_found_returns_404(self, auth_client):
        url = reverse("notification-mark-read", kwargs={"pk": uuid.uuid4()})
        response = auth_client.patch(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_mark_read_happy_path(self, auth_client, user):
        notif = Notification.objects.create(user=user, title="Unread", is_read=False)
        url = reverse("notification-mark-read", kwargs={"pk": notif.id})
        response = auth_client.patch(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_read"] is True


@pytest.mark.django_db
class TestNotificationMarkAllReadView:
    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.post(NOTIFICATIONS_MARK_ALL_READ_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_mark_all_read_happy_path(self, auth_client, user):
        Notification.objects.create(user=user, title="N1", is_read=False)
        Notification.objects.create(user=user, title="N2", is_read=False)

        response = auth_client.post(NOTIFICATIONS_MARK_ALL_READ_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["marked_count"] == 2


@pytest.mark.django_db
class TestNotificationUnreadCountView:
    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(NOTIFICATIONS_UNREAD_COUNT_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unread_count_happy_path(self, auth_client, user):
        Notification.objects.create(user=user, title="N1", is_read=False)
        Notification.objects.create(user=user, title="N2", is_read=False)
        Notification.objects.create(user=user, title="N3", is_read=True)

        response = auth_client.get(NOTIFICATIONS_UNREAD_COUNT_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["unread_count"] == 2


@pytest.mark.django_db
class TestNotificationSettingsView:
    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(NOTIFICATIONS_SETTINGS_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_and_patch_notification_settings(self, auth_client, user):
        response = auth_client.get(NOTIFICATIONS_SETTINGS_URL)
        assert response.status_code == status.HTTP_200_OK
        assert "sections" in response.data
        assert "notifications" in response.data["sections"]
        items = response.data["sections"]["notifications"]["items"]
        item_keys = [item["key"] for item in items]
        assert "visit_notifications" in item_keys
        assert "owner_messages" in item_keys
        assert "property_updates" in item_keys
        assert "security_alerts" in item_keys
        assert "promotions_and_updates" in item_keys

        # Patch setting
        patch_res = auth_client.patch(
            NOTIFICATIONS_SETTINGS_URL,
            {"property_updates": True, "visit_notifications": False},
            format="json",
        )
        assert patch_res.status_code == status.HTTP_200_OK
        assert patch_res.data["property_updates"] is True
        assert patch_res.data["visit_notifications"] is False

        # Partial update with only a single toggle
        single_res = auth_client.patch(
            NOTIFICATIONS_SETTINGS_URL,
            {"promotions_and_updates": True},
            format="json",
        )
        assert single_res.status_code == status.HTTP_200_OK
        assert single_res.data["promotions_and_updates"] is True
        # Verify other toggles were not modified
        assert single_res.data["visit_notifications"] is False
        assert single_res.data["owner_messages"] is True
        assert single_res.data["security_alerts"] is True


@pytest.mark.django_db
class TestDeviceTokenViews:
    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.post(DEVICE_TOKEN_CREATE_URL, {"token": "123"})
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

        del_res = api_client.post(DEVICE_TOKEN_DELETE_URL, {"token": "123"})
        assert del_res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_device_register_invalid_payload_returns_400(self, auth_client):
        res = auth_client.post(DEVICE_TOKEN_CREATE_URL, {}, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_device_register_happy_path(self, auth_client, user):
        payload = {
            "token": "fcm_test_token_abc12345",
            "device_type": "ios",
            "device_name": "iPhone 16",
        }
        res = auth_client.post(DEVICE_TOKEN_CREATE_URL, payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data["token"] == "fcm_test_token_abc12345"
        assert res.data["device_type"] == "ios"

        assert DeviceToken.objects.filter(token="fcm_test_token_abc12345", is_active=True).exists()

    def test_device_unregister_happy_path(self, auth_client, user):
        DeviceToken.objects.create(
            user=user, token="fcm_test_token_to_remove", is_active=True
        )

        res = auth_client.post(
            DEVICE_TOKEN_DELETE_URL,
            {"token": "fcm_test_token_to_remove"},
            format="json",
        )
        assert res.status_code == status.HTTP_200_OK

        token_obj = DeviceToken.objects.get(token="fcm_test_token_to_remove")
        assert token_obj.is_active is False
