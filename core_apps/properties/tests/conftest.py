import pytest
from core_apps.properties.models import PropertyType

DEFAULT_PROPERTY_TYPES = [
    {"name": "Apartment", "slug": "apartment"},
    {"name": "House", "slug": "house"},
    {"name": "Villa", "slug": "villa"},
    {"name": "Studio", "slug": "studio"},
    {"name": "Penthouse", "slug": "penthouse"},
]


@pytest.fixture(autouse=True)
def property_types(db):
    for entry in DEFAULT_PROPERTY_TYPES:
        PropertyType.objects.get_or_create(
            slug=entry["slug"], defaults={"name": entry["name"]}
        )


@pytest.fixture
def apartment_type(db):
    return PropertyType.objects.get_or_create(
        slug="apartment", defaults={"name": "Apartment"}
    )[0]
