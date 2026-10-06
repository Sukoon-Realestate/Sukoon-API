from datetime import date, time, timedelta
import uuid

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from core_apps.properties.models import Property, PropertyVisit


def create_property(owner, apartment_type, cairo_city, cairo_governorate, title="شقة مدينة نصر"):
    return Property.objects.create(
        owner=owner,
        title=title,
        price=6500,
        price_period=Property.PricePeriod.MONTHLY,
        property_type=apartment_type,
        bedrooms=3,
        governorate=cairo_governorate,
        city=cairo_city,
        district="مدينة نصر",
    )


@pytest.mark.django_db
class TestOwnerVisitRequestListScreen:
    """Tests for Screen 1: طلبات الزيارة (Owner Visit Requests List)."""

    def test_unauthenticated_returns_401(self, api_client):
        url = reverse("owner-visit-request-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_returns_card_data_and_tab_counts(
        self,
        auth_client,
        user,
        another_user,
        apartment_type,
        cairo_city,
        cairo_governorate,
    ):
        prop = create_property(user, apartment_type, cairo_city, cairo_governorate)
        today = timezone.localdate()

        # Visit 1: Verified tenant, today 3:00 PM, pending
        another_user.is_verified = True
        another_user.save()
        v1 = PropertyVisit.objects.create(
            property=prop,
            tenant=another_user,
            visit_date=today,
            visit_time=time(15, 0),
            status=PropertyVisit.Status.PENDING,
        )

        # Visit 2: Confirmed visit tomorrow 12:00 PM
        v2 = PropertyVisit.objects.create(
            property=prop,
            tenant=another_user,
            visit_date=today + timedelta(days=1),
            visit_time=time(12, 0),
            status=PropertyVisit.Status.CONFIRMED,
        )

        url = reverse("owner-visit-request-list")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()["data"]
        assert "tabs" in data
        assert data["tabs"]["new"] == 1
        assert data["tabs"]["confirmed"] == 1
        assert data["tabs"]["all"] == 2

        results = data["results"]
        assert len(results) == 2

        card = next(c for c in results if c["id"] == str(v1.id))
        assert card["property"]["title"] == "شقة مدينة نصر"
        assert card["property"]["district"] == "مدينة نصر"
        assert "النهارده 3م" in card["schedule_label"]
        assert card["status"] == "pending"
        assert card["status_label"] == "جديد"
        assert card["actions"]["can_accept"] is True
        assert card["actions"]["can_reject"] is True
        assert card["actions"]["can_chat"] is True
        assert card["is_verified_tenant"] is True
        assert card["verification_warning"] == ""

    def test_unverified_tenant_warning(
        self,
        auth_client,
        user,
        another_user,
        apartment_type,
        cairo_city,
        cairo_governorate,
    ):
        prop = create_property(user, apartment_type, cairo_city, cairo_governorate)
        today = timezone.localdate()
        another_user.is_verified = False
        another_user.save()

        v = PropertyVisit.objects.create(
            property=prop,
            tenant=another_user,
            visit_date=today,
            visit_time=time(17, 0),
            status=PropertyVisit.Status.PENDING,
        )

        url = reverse("owner-visit-request-list")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        card = response.json()["data"]["results"][0]
        assert card["is_verified_tenant"] is False
        assert card["verification_warning"] == "هذا المستأجر لم يوثق هويته بعد"
        assert card["status_label"] == "انتظار"

    def test_filter_by_status(
        self,
        auth_client,
        user,
        another_user,
        apartment_type,
        cairo_city,
        cairo_governorate,
    ):
        prop = create_property(user, apartment_type, cairo_city, cairo_governorate)
        today = timezone.localdate()

        PropertyVisit.objects.create(
            property=prop,
            tenant=another_user,
            visit_date=today,
            visit_time=time(10, 0),
            status=PropertyVisit.Status.PENDING,
        )
        PropertyVisit.objects.create(
            property=prop,
            tenant=another_user,
            visit_date=today,
            visit_time=time(14, 0),
            status=PropertyVisit.Status.CONFIRMED,
        )

        url = reverse("owner-visit-request-list")
        resp_pending = auth_client.get(url, {"status": "pending"})
        assert resp_pending.status_code == status.HTTP_200_OK
        assert len(resp_pending.json()["data"]["results"]) == 1
        assert resp_pending.json()["data"]["results"][0]["status"] == "pending"

        resp_confirmed = auth_client.get(url, {"status": "confirmed"})
        assert resp_confirmed.status_code == status.HTTP_200_OK
        assert len(resp_confirmed.json()["data"]["results"]) == 1
        assert resp_confirmed.json()["data"]["results"][0]["status"] == "confirmed"

    def test_does_not_return_other_owner_visits(
        self,
        api_client,
        user,
        another_user,
        apartment_type,
        cairo_city,
        cairo_governorate,
    ):
        prop = create_property(another_user, apartment_type, cairo_city, cairo_governorate)
        PropertyVisit.objects.create(
            property=prop,
            tenant=user,
            visit_date=timezone.localdate(),
            visit_time=time(12, 0),
            status=PropertyVisit.Status.PENDING,
        )

        api_client.force_authenticate(user)
        response = api_client.get(reverse("owner-visit-request-list"))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["data"]["results"]) == 0


@pytest.mark.django_db
class TestOwnerVisitRequestDetailScreen:
    """Tests for Screen 2: تفاصيل الطلب (Owner Visit Request Details)."""

    def test_unauthenticated_returns_401(self, api_client):
        url = reverse("owner-visit-request-detail", kwargs={"id": uuid.uuid4()})
        assert api_client.get(url).status_code == status.HTTP_401_UNAUTHORIZED

    def test_not_found_or_other_owner_returns_404(
        self,
        api_client,
        user,
        another_user,
        apartment_type,
        cairo_city,
        cairo_governorate,
    ):
        prop = create_property(another_user, apartment_type, cairo_city, cairo_governorate)
        v = PropertyVisit.objects.create(
            property=prop,
            tenant=another_user,
            visit_date=timezone.localdate(),
            visit_time=time(15, 0),
        )

        api_client.force_authenticate(user)
        url = reverse("owner-visit-request-detail", kwargs={"id": v.id})
        assert api_client.get(url).status_code == status.HTTP_404_NOT_FOUND

    def test_pending_visit_detail_masks_phone_and_formats_labels(
        self,
        auth_client,
        user,
        another_user,
        apartment_type,
        cairo_city,
        cairo_governorate,
    ):
        another_user.profile.phone_number = "+201012345432"
        another_user.profile.save()
        another_user.is_verified = True
        another_user.save()

        prop = create_property(
            user, apartment_type, cairo_city, cairo_governorate, title="شقة مفروشة"
        )
        visit_date = date(2025, 6, 14)  # Saturday
        v = PropertyVisit.objects.create(
            property=prop,
            tenant=another_user,
            visit_date=visit_date,
            visit_time=time(15, 0),
            note="مهتمة بالشقة ومحتاجة تاكدي من المساحة وحالة التشطيب.",
            status=PropertyVisit.Status.PENDING,
        )

        url = reverse("owner-visit-request-detail", kwargs={"id": v.id})
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()["data"]
        assert data["id"] == str(v.id)
        assert data["tenant"]["name"] == another_user.get_full_name
        assert data["tenant"]["is_verified"] is True
        assert data["tenant"]["phone_number"] == ""
        assert data["tenant"]["masked_phone_number"] == "010****432"
        assert data["tenant"]["is_phone_revealed"] is False
        assert "يظهر بعد القبول فقط" in data["tenant"]["phone_notice"]
        assert data["property"]["title"] == "شقة مفروشة"
        assert data["property"]["display_name"] == "شقة مفروشة – مدينة نصر"
        assert "يونيو 2025" in data["day_label"]
        assert "3:00 م" in data["time_label"]
        assert data["note"] == "مهتمة بالشقة ومحتاجة تاكدي من المساحة وحالة التشطيب."
        assert data["actions"]["can_accept"] is True
        assert data["actions"]["can_reject"] is True
        assert data["actions"]["can_chat"] is False

    def test_confirmed_visit_detail_reveals_phone(
        self,
        auth_client,
        user,
        another_user,
        apartment_type,
        cairo_city,
        cairo_governorate,
    ):
        another_user.profile.phone_number = "+201012345432"
        another_user.profile.save()

        prop = create_property(user, apartment_type, cairo_city, cairo_governorate)
        v = PropertyVisit.objects.create(
            property=prop,
            tenant=another_user,
            visit_date=timezone.localdate(),
            visit_time=time(15, 0),
            status=PropertyVisit.Status.CONFIRMED,
        )

        url = reverse("owner-visit-request-detail", kwargs={"id": v.id})
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()["data"]
        assert data["tenant"]["phone_number"] == "+201012345432"
        assert data["tenant"]["is_phone_revealed"] is True
        assert data["actions"]["can_accept"] is False
        assert data["actions"]["can_reject"] is False
        assert data["actions"]["can_chat"] is True


@pytest.mark.django_db
class TestOwnerVisitRequestRejectModal:
    """Tests for Screen 3: رفض طلب الزيارة (Reject Modal / Action)."""

    def test_owner_rejects_pending_visit_with_reason(
        self,
        auth_client,
        user,
        another_user,
        apartment_type,
        cairo_city,
        cairo_governorate,
    ):
        prop = create_property(user, apartment_type, cairo_city, cairo_governorate)
        v = PropertyVisit.objects.create(
            property=prop,
            tenant=another_user,
            visit_date=timezone.localdate() + timedelta(days=1),
            visit_time=time(14, 0),
            status=PropertyVisit.Status.PENDING,
        )

        url = reverse("owner-visit-request-reject", kwargs={"id": v.id})
        payload = {
            "reason": "timing_not_suitable",
            "custom_reason": "الوقت لا يناسب المالك",
        }
        response = auth_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_200_OK

        v.refresh_from_db()
        assert v.status == PropertyVisit.Status.REJECTED

    def test_cannot_reject_already_confirmed_visit(
        self,
        auth_client,
        user,
        another_user,
        apartment_type,
        cairo_city,
        cairo_governorate,
    ):
        prop = create_property(user, apartment_type, cairo_city, cairo_governorate)
        v = PropertyVisit.objects.create(
            property=prop,
            tenant=another_user,
            visit_date=timezone.localdate() + timedelta(days=1),
            visit_time=time(14, 0),
            status=PropertyVisit.Status.CONFIRMED,
        )

        url = reverse("owner-visit-request-reject", kwargs={"id": v.id})
        response = auth_client.post(url, {"reason": "timing_not_suitable"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestOwnerVisitRequestAcceptAction:
    """Tests for Screen 2 Accept Action: قبول الزيارة."""

    def test_owner_accepts_pending_visit(
        self,
        auth_client,
        user,
        another_user,
        apartment_type,
        cairo_city,
        cairo_governorate,
    ):
        another_user.profile.phone_number = "+201012345432"
        another_user.profile.save()

        prop = create_property(user, apartment_type, cairo_city, cairo_governorate)
        v = PropertyVisit.objects.create(
            property=prop,
            tenant=another_user,
            visit_date=timezone.localdate() + timedelta(days=1),
            visit_time=time(14, 0),
            status=PropertyVisit.Status.PENDING,
        )

        url = reverse("owner-visit-request-accept", kwargs={"id": v.id})
        response = auth_client.post(url, {}, format="json")
        assert response.status_code == status.HTTP_200_OK

        v.refresh_from_db()
        assert v.status == PropertyVisit.Status.CONFIRMED
        assert response.json()["data"]["tenant"]["phone_number"] == "+201012345432"

    def test_cannot_accept_already_confirmed_visit(
        self,
        auth_client,
        user,
        another_user,
        apartment_type,
        cairo_city,
        cairo_governorate,
    ):
        prop = create_property(user, apartment_type, cairo_city, cairo_governorate)
        v = PropertyVisit.objects.create(
            property=prop,
            tenant=another_user,
            visit_date=timezone.localdate() + timedelta(days=1),
            visit_time=time(14, 0),
            status=PropertyVisit.Status.CONFIRMED,
        )

        url = reverse("owner-visit-request-accept", kwargs={"id": v.id})
        response = auth_client.post(url, {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestOwnerVisitCalendarScreen:
    """Tests for Screen 4: تقويم الزيارات (Owner Visit Calendar enhancements)."""

    def test_calendar_returns_arabic_labels_and_tenant_initial(
        self,
        auth_client,
        user,
        another_user,
        apartment_type,
        cairo_city,
        cairo_governorate,
    ):
        another_user.first_name = "محمد"
        another_user.last_name = "أحمد"
        another_user.save()

        prop = create_property(user, apartment_type, cairo_city, cairo_governorate)
        visit_date = date(2025, 1, 15)
        PropertyVisit.objects.create(
            property=prop,
            tenant=another_user,
            visit_date=visit_date,
            visit_time=time(15, 0),
            status=PropertyVisit.Status.CONFIRMED,
        )

        url = reverse("owner-visit-calendar")
        response = auth_client.get(
            url,
            {"year": 2025, "month": 1, "date": "2025-01-15"},
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()["data"]
        assert data["month_label"] == "يناير 2025"
        assert data["selected_date_label"] == "زيارات يوم 15"

        visit_card = data["visits"][0]
        assert visit_card["tenant"]["name"] == "محمد أحمد"
        assert visit_card["tenant"]["initial"] == "م"
        assert visit_card["time_formatted"] == "3:00 م"
        assert visit_card["status_label"] == "مؤكدة"

    def test_calendar_accepts_date_as_day_number(
        self,
        auth_client,
        user,
        another_user,
        apartment_type,
        cairo_city,
        cairo_governorate,
    ):
        prop = create_property(user, apartment_type, cairo_city, cairo_governorate)
        visit_date = date(2026, 10, 1)
        PropertyVisit.objects.create(
            property=prop,
            tenant=another_user,
            visit_date=visit_date,
            visit_time=time(10, 0),
            status=PropertyVisit.Status.CONFIRMED,
        )

        url = reverse("owner-visit-calendar")
        # Test date=1
        response = auth_client.get(
            url,
            {"year": 2026, "month": 10, "date": 1},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert data["selected_date"] == "2026-10-01"
        assert data["selected_date_label"] == "زيارات يوم 1"
        assert len(data["visits"]) == 1

    def test_calendar_accepts_day_parameter(
        self,
        auth_client,
        user,
        another_user,
        apartment_type,
        cairo_city,
        cairo_governorate,
    ):
        prop = create_property(user, apartment_type, cairo_city, cairo_governorate)
        visit_date = date(2026, 10, 1)
        PropertyVisit.objects.create(
            property=prop,
            tenant=another_user,
            visit_date=visit_date,
            visit_time=time(10, 0),
            status=PropertyVisit.Status.CONFIRMED,
        )

        url = reverse("owner-visit-calendar")
        # Test day=1
        response = auth_client.get(
            url,
            {"year": 2026, "month": 10, "day": 1},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert data["selected_date"] == "2026-10-01"
        assert data["selected_date_label"] == "زيارات يوم 1"
        assert len(data["visits"]) == 1

        # Test day with empty value does not crash and returns whole month
        response_empty_day = auth_client.get(
            url,
            {"year": 2026, "month": 10, "day": ""},
        )
        assert response_empty_day.status_code == status.HTTP_200_OK
        assert response_empty_day.json()["data"]["selected_date"] is None
