import pytest
from copy import deepcopy
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


def edit_payload(current):
    result = deepcopy(current)
    result["expected_revision"] = current["revision"]
    for offer in result["offers"]:
        offer["term_overrides"] = {
            key: value
            for key, value in offer.pop("terms").items()
            if key not in offer["inherited_fields"]
        }
    return result


def test_offer_revision_changes_only_with_its_own_resolved_terms_or_accommodation():
    payload = _room_offer_payload()
    payload["rooms"].append(
        {"client_key": "room-b", "name": "Room B", "capacity": 2, "beds": []}
    )
    payload["offers"].append(
        {
            **deepcopy(payload["offers"][0]),
            "client_key": "offer-b",
            "room_ids": ["room-b"],
            "name": "Room B",
        }
    )
    current = normalize_inventory(payload)
    same = normalize_inventory(edit_payload(current), current)
    assert same["revision"] == 2
    assert [offer["revision"] for offer in same["offers"]] == [1, 1]
    edit = edit_payload(same)
    edit["offers"][0]["term_overrides"]["price"] = "6000.00"
    changed = normalize_inventory(edit, same)
    assert [offer["revision"] for offer in changed["offers"]] == [2, 1]
    edit = edit_payload(changed)
    edit["rooms"][1]["capacity"] = 3
    capacity = normalize_inventory(edit, changed)
    assert [offer["revision"] for offer in capacity["offers"]] == [2, 2]
    edit = edit_payload(capacity)
    edit["shared_defaults"]["rental_period"] = 4
    inherited = normalize_inventory(edit, capacity)
    assert [offer["revision"] for offer in inherited["offers"]] == [3, 3]


def test_bed_revision_ignores_unselected_bed_but_tracks_parent_room():
    payload = _room_offer_payload()
    payload["rooms"][0].update(
        capacity=2,
        beds=[
            {"client_key": "bed-a", "name": "Bed A"},
            {"client_key": "bed-b", "name": "Bed B"},
        ],
    )
    payload["offers"][0].update(rental_scope="bed", bed_id="bed-a")
    current = normalize_inventory(payload)
    edit = edit_payload(current)
    edit["rooms"][0]["beds"][1]["name"] = "Another label"
    other = normalize_inventory(edit, current)
    assert other["offers"][0]["revision"] == 1
    edit = edit_payload(other)
    edit["rooms"][0]["name"] = "Reviewed room name"
    room = normalize_inventory(edit, other)
    assert room["offers"][0]["revision"] == 2
