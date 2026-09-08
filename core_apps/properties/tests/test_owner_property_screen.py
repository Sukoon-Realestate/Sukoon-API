import pytest
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from core_apps.common.models import ContentView
from core_apps.properties.models import (
    Property,
    PropertyFavorite,
    PropertyRating,
    PropertyVisit,
    SavedProperty,
)


def _create_property(owner, property_type, city, governorate, **kwargs):
    defaults = {
        "title": "Apartment in Nasr City",
        "description": "Furnished modern apartment",
        "price": 6500.00,
        "price_period": Property.PricePeriod.MONTHLY,
        "property_type": property_type,
        "city": city,
        "governorate": governorate,
        "district": "Nasr City",
        "status": Property.Status.VERIFIED,
        "is_verified": True,
    }
    defaults.update(kwargs)
    return Property.objects.create(owner=owner, **defaults)


@pytest.mark.django_db
class TestMyPropertyListEndpoint:
    def test_unauthenticated_returns_401(self, api_client):
        url = reverse("my-property-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_contains_status_is_verified_and_metrics(
        self, auth_client, user, another_user, apartment_type, cairo_city, cairo_governorate
    ):
        prop1 = _create_property(
            owner=user,
            property_type=apartment_type,
            city=cairo_city,
            governorate=cairo_governorate,
            title="شقة مفروشة – مدينة نصر",
            price=6500.00,
            status=Property.Status.VERIFIED,
            is_verified=True,
        )
        prop2 = _create_property(
            owner=user,
            property_type=apartment_type,
            city=cairo_city,
            governorate=cairo_governorate,
            title="ستوديو – التجمع الخامس",
            price=4200.00,
            status=Property.Status.UNDER_REVIEW,
            is_verified=False,
        )
        prop3 = _create_property(
            owner=user,
            property_type=apartment_type,
            city=cairo_city,
            governorate=cairo_governorate,
            title="شقة 3 غرف – المهندسين",
            price=8800.00,
            status=Property.Status.HIDDEN,
            is_verified=False,
        )
        # Property belonging to another owner (should not appear)
        _create_property(
            owner=another_user,
            property_type=apartment_type,
            city=cairo_city,
            governorate=cairo_governorate,
            title="Other Owner Property",
        )

        # Record views and visit requests for prop1
        ct = ContentType.objects.get_for_model(Property)
        ContentView.objects.create(
            content_type=ct,
            object_id=prop1.pkid,
            user=another_user,
            viewer_ip="192.168.1.1",
            last_viewed=timezone.now(),
        )
        PropertyVisit.objects.create(
            property=prop1,
            tenant=another_user,
            visit_date=timezone.localdate(),
            visit_time="15:00:00",
            status=PropertyVisit.Status.CONFIRMED,
        )

        url = reverse("my-property-list")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        results = response.json()["data"]["results"]
        assert len(results) == 3

        # Map results by title
        items = {item["title"]: item for item in results}

        # Card 1: Verified
        card1 = items["شقة مفروشة – مدينة نصر"]
        assert card1["status"] == Property.Status.VERIFIED
        assert card1["is_verified"] is True
        assert card1["price"] == "6500.00"
        assert card1["views_count"] == 1
        assert card1["visits_count"] == 1

        # Card 2: Under review
        card2 = items["ستوديو – التجمع الخامس"]
        assert card2["status"] == Property.Status.UNDER_REVIEW
        assert card2["is_verified"] is False
        assert card2["price"] == "4200.00"
        assert card2["views_count"] == 0
        assert card2["visits_count"] == 0

        # Card 3: Hidden
        card3 = items["شقة 3 غرف – المهندسين"]
        assert card3["status"] == Property.Status.HIDDEN
        assert card3["is_verified"] is False
        assert card3["price"] == "8800.00"


@pytest.mark.django_db
class TestPropertyStatisticsAPI:
    def test_unauthenticated_returns_401(self, api_client, user, apartment_type, cairo_city, cairo_governorate):
        prop = _create_property(
            owner=user,
            property_type=apartment_type,
            city=cairo_city,
            governorate=cairo_governorate,
        )
        url = reverse("property-statistics", kwargs={"id": prop.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_non_owner_returns_403(
        self, api_client, user, another_user, apartment_type, cairo_city, cairo_governorate
    ):
        prop = _create_property(
            owner=user,
            property_type=apartment_type,
            city=cairo_city,
            governorate=cairo_governorate,
        )
        api_client.force_authenticate(user=another_user)
        url = reverse("property-statistics", kwargs={"id": prop.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_owner_retrieves_complete_statistics(
        self, auth_client, user, another_user, apartment_type, cairo_city, cairo_governorate
    ):
        prop = _create_property(
            owner=user,
            property_type=apartment_type,
            city=cairo_city,
            governorate=cairo_governorate,
            title="Apartment Insights Test",
        )

        # Record 2 views (one recent, one older)
        ct = ContentType.objects.get_for_model(Property)
        ContentView.objects.create(
            content_type=ct,
            object_id=prop.pkid,
            user=another_user,
            viewer_ip="192.168.1.1",
            last_viewed=timezone.now(),
        )
        ContentView.objects.create(
            content_type=ct,
            object_id=prop.pkid,
            user=None,
            viewer_ip="192.168.1.2",
            last_viewed=timezone.now() - timezone.timedelta(days=10),
        )

        # Record visits with different statuses
        today = timezone.localdate()
        PropertyVisit.objects.create(
            property=prop,
            tenant=another_user,
            visit_date=today + timezone.timedelta(days=2),
            visit_time="14:00:00",
            status=PropertyVisit.Status.CONFIRMED,
        )
        PropertyVisit.objects.create(
            property=prop,
            tenant=another_user,
            visit_date=today,
            visit_time="16:00:00",
            status=PropertyVisit.Status.PENDING,
        )

        # Record favorites, saves, and ratings
        PropertyFavorite.objects.create(user=another_user, property=prop)
        SavedProperty.objects.create(user=another_user, property=prop)
        PropertyRating.objects.create(user=another_user, property=prop, rating=4)

        url = reverse("property-statistics", kwargs={"id": prop.id})
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]

        assert data["id"] == str(prop.id)
        assert data["title"] == "Apartment Insights Test"
        assert data["period"] == "30_days"
        assert data["period_label"] == "30 يوم"
        assert data["visit_requests_count"] == 2
        assert data["views_count"] == 2
        assert data["acceptance_rate"] == 100  # 1 confirmed, 0 rejected -> 100%
        assert data["saved_count"] == 2  # 1 save + 1 favorite
        assert data["recent_views_count"] == 1
        assert data["visits_count"] == 2
        assert data["upcoming_visits_count"] == 1
        assert data["visits_summary"]["confirmed"] == 1
        assert data["visits_summary"]["pending"] == 1
        assert data["visits_summary"]["canceled"] == 0
        assert data["favorites_count"] == 1
        assert data["average_rating"] == 4.0
        assert data["ratings_count"] == 1

        # 14-day views bar chart
        assert len(data["views_last_14_days"]) == 14
        assert "date" in data["views_last_14_days"][0]
        assert "day" in data["views_last_14_days"][0]
        assert "day_name" in data["views_last_14_days"][0]
        assert "count" in data["views_last_14_days"][0]

        # Top search criteria
        assert len(data["top_search_criteria"]) == 4
        criteria_keys = [c["key"] for c in data["top_search_criteria"]]
        assert criteria_keys == ["area", "price", "location", "amenities"]
        criteria_labels = [c["label"] for c in data["top_search_criteria"]]
        assert criteria_labels == ["المساحة", "السعر", "الموقع", "المرافق"]
        criteria_percentages = [c["percentage"] for c in data["top_search_criteria"]]
        assert criteria_percentages == [78, 65, 55, 42]



@pytest.mark.django_db
class TestPropertyVisibilityToggleAPI:
    def test_unauthenticated_returns_401(self, api_client, user, apartment_type, cairo_city, cairo_governorate):
        prop = _create_property(
            owner=user,
            property_type=apartment_type,
            city=cairo_city,
            governorate=cairo_governorate,
        )
        url = reverse("property-toggle-visibility", kwargs={"id": prop.id})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_non_owner_returns_403(
        self, api_client, user, another_user, apartment_type, cairo_city, cairo_governorate
    ):
        prop = _create_property(
            owner=user,
            property_type=apartment_type,
            city=cairo_city,
            governorate=cairo_governorate,
        )
        api_client.force_authenticate(user=another_user)
        url = reverse("property-toggle-visibility", kwargs={"id": prop.id})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_owner_toggles_verified_property_to_hidden_and_back(
        self, auth_client, user, apartment_type, cairo_city, cairo_governorate
    ):
        prop = _create_property(
            owner=user,
            property_type=apartment_type,
            city=cairo_city,
            governorate=cairo_governorate,
            status=Property.Status.VERIFIED,
            is_verified=True,
        )
        url = reverse("property-toggle-visibility", kwargs={"id": prop.id})

        # 1. Toggle to hidden
        res1 = auth_client.post(url)
        assert res1.status_code == status.HTTP_200_OK
        data1 = res1.json()["data"]
        assert data1["status"] == Property.Status.HIDDEN
        assert data1["is_hidden"] is True
        prop.refresh_from_db()
        assert prop.status == Property.Status.HIDDEN

        # 2. Toggle back to active (restores to VERIFIED since is_verified=True)
        res2 = auth_client.post(url)
        assert res2.status_code == status.HTTP_200_OK
        data2 = res2.json()["data"]
        assert data2["status"] == Property.Status.VERIFIED
        assert data2["is_hidden"] is False
        prop.refresh_from_db()
        assert prop.status == Property.Status.VERIFIED

    def test_owner_sets_explicit_visibility_via_patch(
        self, auth_client, user, apartment_type, cairo_city, cairo_governorate
    ):
        prop = _create_property(
            owner=user,
            property_type=apartment_type,
            city=cairo_city,
            governorate=cairo_governorate,
            status=Property.Status.VERIFIED,
            is_verified=True,
        )
        url = reverse("property-toggle-visibility", kwargs={"id": prop.id})

        # Explicitly hide
        res = auth_client.patch(url, {"is_hidden": True}, format="json")
        assert res.status_code == status.HTTP_200_OK
        assert res.json()["data"]["is_hidden"] is True

        # Explicitly unhide
        res = auth_client.patch(url, {"is_hidden": False}, format="json")
        assert res.status_code == status.HTTP_200_OK
        assert res.json()["data"]["is_hidden"] is False


@pytest.mark.django_db
class TestPropertyScreenActions:
    def test_owner_can_edit_property_details(
        self, auth_client, user, apartment_type, cairo_city, cairo_governorate
    ):
        prop = _create_property(
            owner=user,
            property_type=apartment_type,
            city=cairo_city,
            governorate=cairo_governorate,
            title="Original Title",
            price=6500.00,
        )
        url = reverse("property-update", kwargs={"id": prop.id})
        response = auth_client.patch(
            url,
            {"title": "Updated Title", "price": 7000.00},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        prop.refresh_from_db()
        assert prop.title == "Updated Title"
        assert prop.price == 7000.00

    def test_owner_can_delete_property(
        self, auth_client, user, apartment_type, cairo_city, cairo_governorate
    ):
        prop = _create_property(
            owner=user,
            property_type=apartment_type,
            city=cairo_city,
            governorate=cairo_governorate,
        )
        url = reverse("property-delete", kwargs={"id": prop.id})
        response = auth_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Property.objects.filter(id=prop.id).exists()


@pytest.mark.django_db
class TestOwnerRevenuesAPI:
    def test_unauthenticated_returns_401(self, api_client):
        url = reverse("owner-revenues")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_default_revenues_matches_screen_mockup_exactly(self, auth_client):
        url = reverse("owner-revenues")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()["data"]

        # 1. Total this month hero card
        assert data["total_this_month"] == 21500.0
        assert data["formatted_total"] == "21,500 ج"
        assert data["currency"] == "ج"
        assert data["percentage_change"] == 8.0
        assert data["comparison_text"] == "+8% عن الشهر السابق"
        assert data["is_positive"] is True

        # 2. Properties breakdown (4 cards)
        props = data["properties"]
        assert len(props) == 4

        # Card 1: شقة مدينة نصر - 6,500 - مدفوع
        assert props[0]["title"] == "شقة مدينة نصر"
        assert props[0]["amount"] == 6500.0
        assert props[0]["formatted_amount"] == "6,500 ج"
        assert props[0]["status"] == "paid"
        assert props[0]["status_label"] == "مدفوع"
        assert props[0]["status_color"] == "green"

        # Card 2: ستوديو التجمع - 4,200 - قادم
        assert props[1]["title"] == "ستوديو التجمع"
        assert props[1]["amount"] == 4200.0
        assert props[1]["formatted_amount"] == "4,200 ج"
        assert props[1]["status"] == "upcoming"
        assert "قادم 15" in props[1]["status_label"]
        assert props[1]["status_color"] == "orange"

        # Card 3: شقة المهندسين - 8,800 - مدفوع
        assert props[2]["title"] == "شقة المهندسين"
        assert props[2]["amount"] == 8800.0
        assert props[2]["formatted_amount"] == "8,800 ج"
        assert props[2]["status"] == "paid"
        assert props[2]["status_label"] == "مدفوع"
        assert props[2]["status_color"] == "green"

        # Card 4: غرفة الزمالك - 2,000 - متأخر
        assert props[3]["title"] == "غرفة الزمالك"
        assert props[3]["amount"] == 2000.0
        assert props[3]["formatted_amount"] == "2,000 ج"
        assert props[3]["status"] == "overdue"
        assert props[3]["status_label"] == "متأخر"
        assert props[3]["status_color"] == "red"

        # 3. Recent transactions (آخر المعاملات)
        txs = data["recent_transactions"]
        assert len(txs) == 3

        # Tx 1: إيجار شهري – شقة نصر (+6,500 ج)
        assert txs[0]["title"] == "إيجار شهري – شقة نصر"
        assert txs[0]["amount"] == 6500.0
        assert txs[0]["formatted_amount"] == "+6,500 ج"
        assert txs[0]["type"] == "credit"
        assert txs[0]["is_credit"] is True

        # Tx 2: إيجار – شقة المهندسين (+8,800 ج)
        assert txs[1]["title"] == "إيجار – شقة المهندسين"
        assert txs[1]["amount"] == 8800.0
        assert txs[1]["formatted_amount"] == "+8,800 ج"
        assert txs[1]["type"] == "credit"
        assert txs[1]["is_credit"] is True

        # Tx 3: رسوم المنصة (-350 ج)
        assert txs[2]["title"] == "رسوم المنصة"
        assert txs[2]["amount"] == -350.0
        assert txs[2]["formatted_amount"] == "-350 ج"
        assert txs[2]["type"] == "debit"
        assert txs[2]["is_credit"] is False

    def test_owner_with_properties_calculates_dynamically(
        self, auth_client, user, apartment_type, cairo_city, cairo_governorate
    ):
        _create_property(
            owner=user,
            property_type=apartment_type,
            city=cairo_city,
            governorate=cairo_governorate,
            title="فيلا التجمع",
            price=30000.00,
        )
        _create_property(
            owner=user,
            property_type=apartment_type,
            city=cairo_city,
            governorate=cairo_governorate,
            title="دوبلكس الشيخ زايد",
            price=25000.00,
        )

        url = reverse("owner-revenues")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()["data"]
        assert data["total_this_month"] == 55000.0
        assert data["formatted_total"] == "55,000 ج"
        assert len(data["properties"]) == 2
        assert len(data["recent_transactions"]) >= 2

    def test_owner_earnings_alias_route_works(self, auth_client):
        url = reverse("owner-earnings")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"]["total_this_month"] == 21500.0

