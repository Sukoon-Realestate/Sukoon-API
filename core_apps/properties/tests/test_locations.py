import pytest
from django.db import IntegrityError
from django.urls import reverse
from rest_framework import status

from core_apps.properties.models import City, Governorate, Property


@pytest.mark.django_db
class TestLocationModels:
    def test_governorate_slug_is_generated_from_name(self):
        governorate = Governorate.objects.create(name="Red Sea")
        assert governorate.slug == "red-sea"

        governorate.name = "South Sinai"
        governorate.save()
        assert governorate.slug == "south-sinai"

    def test_arabic_governorate_name_is_transliterated_for_slug(self):
        governorate = Governorate.objects.create(name="القاهرة")
        assert governorate.slug == "alqahra"

    def test_city_slug_is_generated_from_name(self, cairo_governorate):
        city = City.objects.create(name="New Cairo", governorate=cairo_governorate)
        assert city.slug == "new-cairo"

        city.name = "Fifth Settlement"
        city.save()
        assert city.slug == "fifth-settlement"

    def test_arabic_city_name_is_transliterated_for_slug(self, cairo_governorate):
        city = City.objects.create(name="مدينة نصر", governorate=cairo_governorate)
        assert city.slug == "mdyna-nsr"

    def test_city_belongs_to_governorate(self, cairo_city, cairo_governorate):
        assert cairo_city.governorate == cairo_governorate
        assert str(cairo_governorate) == "Cairo"
        assert str(cairo_city) == "Cairo, Cairo"

    def test_city_name_is_unique_within_governorate(
        self, cairo_city, cairo_governorate
    ):
        with pytest.raises(IntegrityError):
            City.objects.create(
                governorate=cairo_governorate,
                name=cairo_city.name,
                slug="different-slug",
            )


@pytest.mark.django_db
class TestGovernorateList:
    def test_list_requires_authentication(self, api_client):
        response = api_client.get(reverse("governorate-list"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_user_can_list(self, auth_client, cairo_governorate):
        response = auth_client.get(reverse("governorate-list"))
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"]["results"][0]["name"] == "Cairo"


@pytest.mark.django_db
class TestCityList:
    def test_list_filters_by_governorate(
        self, auth_client, cairo_city, cairo_governorate
    ):
        giza = Governorate.objects.create(name="Giza", slug="giza")
        City.objects.create(name="Dokki", slug="dokki", governorate=giza)

        response = auth_client.get(
            reverse("city-list"), {"governorate": str(cairo_governorate.id)}
        )
        assert response.status_code == status.HTTP_200_OK
        results = response.json()["data"]["results"]
        assert [item["name"] for item in results] == ["Cairo"]


@pytest.mark.django_db
class TestPropertyLocationLinks:
    def test_create_property_with_location_ids(
        self, auth_client, cairo_city, cairo_governorate
    ):
        response = auth_client.post(
            reverse("property-create"),
            {
                "title": "Linked property",
                "price": "12000.00",
                "property_type": "apartment",
                "governorate": str(cairo_governorate.id),
                "city": str(cairo_city.id),
                "district": "Maadi",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        property_obj = Property.objects.get(title="Linked property")
        assert property_obj.governorate == cairo_governorate
        assert property_obj.city == cairo_city

    def test_rejects_city_from_another_governorate(
        self, auth_client, cairo_governorate
    ):
        giza = Governorate.objects.create(name="Giza", slug="giza")
        dokki = City.objects.create(name="Dokki", slug="dokki", governorate=giza)
        response = auth_client.post(
            reverse("property-create"),
            {
                "title": "Invalid location",
                "price": "12000.00",
                "property_type": "apartment",
                "governorate": str(cairo_governorate.id),
                "city": str(dokki.id),
                "district": "Dokki",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "City:" in response.json()["message"]
