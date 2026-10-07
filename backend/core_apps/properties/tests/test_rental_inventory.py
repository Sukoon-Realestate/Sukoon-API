import pytest
from rest_framework.exceptions import ValidationError

from core_apps.properties.rental_inventory import normalize_inventory


def _room_offer_payload():
    return {
        "schema_version": 1,
        "mode": "partial",
        "expected_revision": 0,
        "rooms": [
            {"client_key": "room-a", "name": "Room A", "capacity": 1, "beds": []}
        ],
        "shared_defaults": {"rental_period": 3, "deposit": "one_month"},
        "offers": [
            {
                "client_key": "offer-a",
                "name": "Room A",
                "rental_scope": "room",
                "room_ids": ["room-a"],
                "term_overrides": {"price": "5000.00", "price_period": "monthly"},
                "inherited_fields": ["rental_period", "deposit"],
                "availability": "available",
                "archived": False,
            }
        ],
    }


def test_inventory_assigns_stable_ids_and_resolves_terms():
    result = normalize_inventory(_room_offer_payload())
    assert result["revision"] == 1
    assert result["offers"][0]["room_ids"] == [result["rooms"][0]["id"]]
    assert result["offers"][0]["terms"]["rental_period"] == 3
    assert result["offers"][0]["terms"]["price"] == "5000.00"


def test_inventory_rejects_stale_revision():
    with pytest.raises(ValidationError, match="inventory_revision_conflict"):
        normalize_inventory(
            _room_offer_payload(), existing={"revision": 4, "rooms": [], "offers": []}
        )


def test_inventory_rejects_overlapping_room_offers():
    payload = _room_offer_payload()
    payload["offers"].append({**payload["offers"][0], "client_key": "offer-b"})
    with pytest.raises(ValidationError, match="inventory_overlap"):
        normalize_inventory(payload)


def test_bed_must_belong_to_selected_room():
    payload = _room_offer_payload()
    payload["rooms"][0] = {
        "client_key": "room-a",
        "name": "Shared",
        "capacity": 2,
        "beds": [{"client_key": "bed-a", "name": "Bed A"}],
    }
    payload["offers"][0].update({"rental_scope": "bed", "bed_id": "missing-bed"})
    with pytest.raises(ValidationError, match="Bed does not belong"):
        normalize_inventory(payload)
