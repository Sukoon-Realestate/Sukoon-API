import pytest
from core_apps.properties.models import PropertyType, Governorate, City, Property


@pytest.fixture
def apartment_type(db):
    return PropertyType.objects.get_or_create(slug="apartment", defaults={"name": "Apartment"})[0]


@pytest.fixture
def cairo_governorate(db):
    return Governorate.objects.get_or_create(slug="cairo", defaults={"name": "Cairo"})[0]


@pytest.fixture
def cairo_city(db, cairo_governorate):
    return City.objects.get_or_create(
        governorate=cairo_governorate, slug="cairo", defaults={"name": "Cairo"}
    )[0]


@pytest.fixture
def make_property(db, apartment_type, cairo_governorate, cairo_city):
    def _create(owner, **kwargs):
        defaults = {
            "title": "Apartment",
            "price": 10000,
            "property_type": apartment_type,
            "governorate": cairo_governorate,
            "city": cairo_city,
        }
        defaults.update(kwargs)
        return Property.objects.create(owner=owner, **defaults)

    return _create

