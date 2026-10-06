import uuid

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework import status

from core_apps.properties.models import (
    City,
    Governorate,
    Property,
    PropertyRating,
    PropertyType,
    SavedProperty,
)
from core_apps.properties.services import SavedPropertyService


def create_property(owner, **kwargs):
    governorate = Governorate.objects.get_or_create(
        slug="cairo", defaults={"name": "Cairo"}
    )[0]
    city = City.objects.get_or_create(
        governorate=governorate,
        slug="nasr-city",
        defaults={"name": "Nasr City"},
    )[0]
    property_type = kwargs.pop(
        "property_type", PropertyType.objects.get(slug="apartment")
    )
    defaults = {
        "title": "Furnished apartment in Nasr City",
        "price": 6500,
        "bedrooms": 2,
        "bathrooms": 1,
        "area": 90,
        "district": "Nasr City",
        "governorate": governorate,
        "city": city,
        "property_type": property_type,
    }
    defaults.update(kwargs)
    return Property.objects.create(owner=owner, **defaults)


@pytest.mark.django_db
class TestSavedPropertyService:
    def test_save_is_idempotent(self, user, another_user):
        property_obj = create_property(another_user)

        first_saved, first_created = SavedPropertyService.save_property(
            user, property_obj
        )
        second_saved, second_created = SavedPropertyService.save_property(
            user, property_obj
        )

        assert first_created is True
        assert second_created is False
        assert first_saved == second_saved
        assert SavedProperty.objects.count() == 1

    def test_remove_saved_property(self, user, another_user):
        property_obj = create_property(another_user)
        saved_property = SavedProperty.objects.create(user=user, property=property_obj)

        SavedPropertyService.remove_saved_property(saved_property)

        assert not SavedProperty.objects.filter(
            user=user, property=property_obj
        ).exists()


@pytest.mark.django_db
class TestSavedPropertyAPI:
    def test_list_requires_authentication(self, api_client):
        response = api_client.get(reverse("saved-property-list"))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_empty_list_supports_empty_state(self, auth_client):
        response = auth_client.get(reverse("saved-property-list"))

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"] == {
            "count": 0,
            "per_page": 9,
            "total_pages": 1,
            "results": [],
        }

    def test_list_returns_only_current_users_saved_cards(
        self, auth_client, user, another_user
    ):
        visible = create_property(another_user)
        hidden = create_property(another_user, title="Another tenant's saved home")
        SavedProperty.objects.create(user=user, property=visible)
        SavedProperty.objects.create(user=another_user, property=hidden)
        PropertyRating.objects.create(user=user, property=visible, rating=4)
        PropertyRating.objects.create(user=another_user, property=visible, rating=5)

        response = auth_client.get(reverse("saved-property-list"))

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert data["count"] == 1
        assert len(data["results"]) == 1
        card = data["results"][0]
        assert card["id"] == str(visible.id)
        assert card["title"] == visible.title
        assert card["property_type"] == "apartment"
        assert card["area"] == 90
        assert card["price"] == "6500.00"
        assert card["rating"] == 4.5
        assert card["is_saved"] is True
        assert card["saved_at"] is not None

    def test_list_filters_match_filter_sheet(self, auth_client, user, another_user):
        apartment = create_property(
            another_user,
            title="Matching apartment",
            price=8000,
            bedrooms=4,
            is_furnished=True,
            has_wifi=True,
            has_air_conditioning=True,
        )
        create_property(
            another_user,
            title="Too expensive apartment",
            price=9000,
            bedrooms=4,
            is_furnished=True,
            has_wifi=True,
            has_air_conditioning=True,
        )
        for property_obj in Property.objects.all():
            SavedProperty.objects.create(user=user, property=property_obj)

        response = auth_client.get(
            reverse("saved-property-list"),
            {
                "property_type": "apartment",
                "price_max": 8000,
                "bedrooms_min": 4,
                "is_furnished": "true",
                "has_wifi": "true",
                "has_air_conditioning": "true",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert data["count"] == 1
        assert data["results"][0]["id"] == str(apartment.id)

    def test_list_query_count_is_bounded(self, auth_client, user, another_user):
        for index in range(5):
            property_obj = create_property(another_user, title=f"Saved {index}")
            SavedProperty.objects.create(user=user, property=property_obj)

        with CaptureQueriesContext(connection) as queries:
            response = auth_client.get(reverse("saved-property-list"))

        assert response.status_code == status.HTTP_200_OK
        assert len(queries.captured_queries) <= 3

    def test_list_rejects_invalid_filter_value(self, auth_client):
        response = auth_client.get(
            reverse("saved-property-list"), {"bedrooms_min": "many"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_save_requires_authentication(self, api_client, another_user):
        property_obj = create_property(another_user)
        response = api_client.post(
            reverse("saved-property-create", kwargs={"property_id": property_obj.id})
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_save_happy_path_and_duplicate_are_idempotent(
        self, auth_client, user, another_user
    ):
        property_obj = create_property(another_user)
        url = reverse("saved-property-create", kwargs={"property_id": property_obj.id})

        first_response = auth_client.post(url, {}, format="json")
        second_response = auth_client.post(url, {}, format="json")

        assert first_response.status_code == status.HTTP_201_CREATED
        assert first_response.json()["data"]["property_id"] == str(property_obj.id)
        assert first_response.json()["data"]["is_saved"] is True
        assert second_response.status_code == status.HTTP_200_OK
        assert (
            SavedProperty.objects.filter(user=user, property=property_obj).count() == 1
        )

    def test_save_not_found(self, auth_client):
        response = auth_client.post(
            reverse("saved-property-create", kwargs={"property_id": uuid.uuid4()}),
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_unsave_happy_path(self, auth_client, user, another_user):
        property_obj = create_property(another_user)
        SavedProperty.objects.create(user=user, property=property_obj)

        response = auth_client.delete(
            reverse("saved-property-delete", kwargs={"property_id": property_obj.id})
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not SavedProperty.objects.filter(
            user=user, property=property_obj
        ).exists()

    def test_unsave_requires_authentication(self, api_client, another_user):
        property_obj = create_property(another_user)
        response = api_client.delete(
            reverse("saved-property-delete", kwargs={"property_id": property_obj.id})
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unsave_cannot_remove_another_users_record(self, auth_client, another_user):
        property_obj = create_property(another_user)
        SavedProperty.objects.create(user=another_user, property=property_obj)

        response = auth_client.delete(
            reverse("saved-property-delete", kwargs={"property_id": property_obj.id})
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert SavedProperty.objects.filter(
            user=another_user, property=property_obj
        ).exists()
