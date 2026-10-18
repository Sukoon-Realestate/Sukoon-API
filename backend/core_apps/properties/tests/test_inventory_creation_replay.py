"""An inventory retry must keep the original canonical listing/room/offer IDs."""

import json

import pytest
from django.urls import reverse

from core_apps.properties.models import Property
from .test_rental_inventory import _room_offer_payload

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("encoding", ["json", "multipart"])
def test_inventory_creation_retry_returns_original_ids(
    auth_client, user, cairo_city, cairo_governorate, encoding
):
    user.is_verified = True
    user.save(update_fields=["is_verified"])
    inventory = _room_offer_payload()
    payload = {
        "title": "Synthetic recoverable inventory",
        "city": str(cairo_city.id),
        "governorate": str(cairo_governorate.id),
        "property_type": "apartment",
        "rental_inventory": (
            json.dumps(inventory) if encoding == "multipart" else inventory
        ),
    }
    headers = {
        "HTTP_IDEMPOTENCY_KEY": "inventory-create-original",
        "HTTP_X_RENTAL_OFFERS_VERSION": "1",
    }
    endpoint = reverse("property-create")
    original = auth_client.post(endpoint, payload, format=encoding, **headers)
    assert original.status_code == 201
    retry = auth_client.post(endpoint, payload, format=encoding, **headers)
    assert retry.status_code == 201
    assert retry["Idempotency-Replayed"] == "true"
    assert retry.json()["data"]["id"] == original.json()["data"]["id"]
    assert (
        retry.json()["data"]["rental_inventory"]
        == original.json()["data"]["rental_inventory"]
    )
    assert Property.objects.filter(owner=user).count() == 1

    inventory["offers"][0]["term_overrides"]["price"] = "6000.00"
    changed = {
        **payload,
        "rental_inventory": (
            json.dumps(inventory) if encoding == "multipart" else inventory
        ),
    }
    rejected = auth_client.post(endpoint, changed, format=encoding, **headers)
    assert rejected.status_code == 409
    assert Property.objects.filter(owner=user).count() == 1
