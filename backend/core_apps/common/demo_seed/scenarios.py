"""Readable marketplace data in addition to the model-coverage fixture graph."""
from decimal import Decimal

from django.apps import apps


def populate_scenarios(fixtures):
    # Unusable passwords by default; credentials are configured separately after
    # model coverage succeeds, never shared with a real account.
    accounts = {}
    for role in ("owner", "second-owner", "tenant", "student", "housemate", "company-admin", "employee"):
        user = fixtures.get("users.User", role)
        accounts[role] = user.email
        fixtures.get("profiles.Profile", role, user=user)
        fixtures.get("profiles.UserSettings", role, user=user)
    gov = fixtures.get("properties.Governorate", "cairo", name="Cairo", slug="demo-cairo")
    city = fixtures.get("properties.City", "cairo", name="Cairo", slug="demo-cairo", governorate=gov)
    kind = fixtures.get("properties.PropertyType", "apartment", name="Apartment", slug="demo-apartment")
    neighborhoods = ["Maadi", "Nasr City", "Heliopolis", "New Cairo", "Dokki", "Zamalek"]
    for index, neighborhood in enumerate(neighborhoods):
        owner = fixtures.get("users.User", "owner" if index % 2 == 0 else "second-owner")
        prop = fixtures.get(
            "properties.Property", f"listing-{index}", owner=owner,
            title=f"Demo: furnished apartment in {neighborhood}",
            description=f"Synthetic demo listing in {neighborhood}. Two bedrooms, a living room and an equipped kitchen. This property is not offered for rent.",
            governorate=gov, city=city, property_type=kind, district=neighborhood,
            price=Decimal(7500 + index * 1250), bedrooms=2, bathrooms=1, area=95 + index * 10,
            main_image=fixtures.image("apartment.jpg" if index % 2 == 0 else "studio.jpg"),
            is_furnished=True, has_wifi=True, has_air_conditioning=True,
            latitude=Decimal("30.0444") + Decimal(index) / 100,
            longitude=Decimal("31.2357") + Decimal(index) / 100,
        )
        for photo in ("apartment.jpg", "studio.jpg"):
            fixtures.get("properties.PropertyImage", f"listing-{index}-{photo}", property=prop,
                         image=fixtures.image(photo), name="Demo interior", description="Bundled synthetic-listing sample media.")
        tenant = fixtures.get("users.User", "tenant")
        fixtures.get("properties.SavedProperty", f"listing-{index}", user=tenant, property=prop)
        fixtures.get("properties.PropertyFavorite", f"listing-{index}", user=tenant, property=prop)
    return accounts
