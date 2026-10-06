import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from core_apps.properties.models import Property
from core_apps.notifications.models import Notification


def _create_property(owner, property_type, city, governorate, **kwargs):
    defaults = {
        "title": "Apartment in Dokki",
        "description": "Modern apartment",
        "price": 8000.00,
        "price_period": Property.PricePeriod.MONTHLY,
        "property_type": property_type,
        "city": city,
        "governorate": governorate,
        "district": "Dokki",
        "status": Property.Status.VERIFIED,
        "is_verified": True,
    }
    defaults.update(kwargs)
    return Property.objects.create(owner=owner, **defaults)


@pytest.mark.django_db
class TestWorkspaceAccountContract:
    def test_single_account_can_access_tenant_and_owner_endpoints(
        self, auth_client, user
    ):
        # 1. Tenant endpoints
        res_tenant_visits = auth_client.get(reverse("tenant-visit-request-list"))
        assert res_tenant_visits.status_code == status.HTTP_200_OK

        res_saved = auth_client.get(reverse("saved-property-list"))
        assert res_saved.status_code == status.HTTP_200_OK

        # 2. Owner endpoints with single session (no listings)
        res_owned = auth_client.get(reverse("my-property-list"))
        assert res_owned.status_code == status.HTTP_200_OK
        assert res_owned.json()["data"]["count"] == 0
        assert res_owned.json()["data"]["results"] == []

        res_owner_dash = auth_client.get(reverse("owner-dashboard"))
        assert res_owner_dash.status_code == status.HTTP_200_OK
        dash_data = res_owner_dash.json()["data"]
        assert dash_data["active_properties"] == 0
        assert dash_data["pending_requests"] == 0
        assert dash_data["pending_visits"] == []

        res_owner_profile = auth_client.get(reverse("owner-profile"))
        assert res_owner_profile.status_code == status.HTTP_200_OK
        prof_data = res_owner_profile.json()["data"]
        assert prof_data["stats"]["properties_count"] == 0
        assert prof_data["recent_reviews"] == []

        res_owner_cal = auth_client.get(
            f"{reverse('owner-visit-calendar')}?year=2026&month=7"
        )
        assert res_owner_cal.status_code == status.HTTP_200_OK
        cal_data = res_owner_cal.json()["data"]
        assert cal_data["visits"] == []

        res_owner_requests = auth_client.get(reverse("owner-visit-request-list"))
        assert res_owner_requests.status_code == status.HTTP_200_OK
        req_data = res_owner_requests.json()["data"]
        assert "tabs" in req_data
        assert req_data["tabs"]["all"] == 0
        assert req_data["results"] == []

    def test_auth_me_returns_identity_and_metadata_type(self, auth_client, user):
        res = auth_client.get("/api/v1/auth/users/me/")
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        payload = data.get("data", data)
        assert payload["email"] == user.email
        assert "type" in payload
        assert "is_verified" in payload

    def test_reject_booking_own_property(
        self, auth_client, user, apartment_type, cairo_city, cairo_governorate
    ):
        prop = _create_property(
            owner=user,
            property_type=apartment_type,
            city=cairo_city,
            governorate=cairo_governorate,
        )
        future_date = timezone.localdate() + timezone.timedelta(days=3)
        url = reverse("property-visit-create", kwargs={"property_id": prop.id})
        payload = {
            "visit_date": future_date.isoformat(),
            "visit_time": "14:00:00",
            "note": "Trying to book my own property",
        }
        res = auth_client.post(url, payload, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_reject_chat_with_oneself(self, auth_client, user):
        url = reverse("conversation-create")
        res = auth_client.post(url, {"user_id": str(user.id)}, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_profile_edit_syncs_across_my_account_and_owner_profile(
        self, auth_client, user
    ):
        # 1. Update profile via profiles/edit/
        edit_url = reverse("profile-edit")
        edit_payload = {
            "full_name": "سامي يوسف",
            "phone_number": "+201098765432",
            "gender": "male",
        }
        edit_res = auth_client.patch(edit_url, edit_payload, format="json")
        assert edit_res.status_code == status.HTTP_200_OK

        # 2. Verify /api/v1/profiles/my-account/
        my_acc_res = auth_client.get(reverse("my-account"))
        assert my_acc_res.status_code == status.HTTP_200_OK
        assert my_acc_res.json()["data"]["user"]["full_name"] == "سامي يوسف"

        # 3. Verify /api/v1/properties/owner/profile/
        owner_prof_res = auth_client.get(reverse("owner-profile"))
        assert owner_prof_res.status_code == status.HTTP_200_OK
        owner_data = owner_prof_res.json()["data"]
        assert owner_data["owner"]["full_name"] == "سامي يوسف"
        assert owner_data["account_details"]["phone_number"] == "+201098765432"

    def test_notification_types_preserved(
        self, auth_client, user, another_user, apartment_type, cairo_city, cairo_governorate
    ):
        # Owner owns the property
        prop = _create_property(
            owner=user,
            property_type=apartment_type,
            city=cairo_city,
            governorate=cairo_governorate,
        )

        # Tenant (another_user) requests a visit
        auth_client.force_authenticate(user=another_user)
        future_date = timezone.localdate() + timezone.timedelta(days=5)
        url = reverse("property-visit-create", kwargs={"property_id": prop.id})
        res = auth_client.post(
            url,
            {
                "visit_date": future_date.isoformat(),
                "visit_time": "15:00:00",
                "note": "Interested in viewing",
            },
            format="json",
        )
        assert res.status_code == status.HTTP_201_CREATED
        visit_id = res.json()["data"]["id"]

        # Check notification for owner
        owner_notif = Notification.objects.filter(
            user=user, notification_type=Notification.NotificationType.VISIT_REQUEST
        ).first()
        assert owner_notif is not None
        assert owner_notif.data["visit_id"] == visit_id

        # Owner accepts visit
        auth_client.force_authenticate(user=user)
        accept_url = reverse("owner-visit-request-accept", kwargs={"id": visit_id})
        accept_res = auth_client.post(accept_url, {}, format="json")
        assert accept_res.status_code == status.HTTP_200_OK

        # Check notification for tenant
        tenant_notif = Notification.objects.filter(
            user=another_user,
            notification_type=Notification.NotificationType.VISIT_ACCEPTED,
        ).first()
        assert tenant_notif is not None
        assert tenant_notif.data["visit_id"] == visit_id
