"""Public bookings retain the same complete accommodation snapshot as invitations."""

import copy
import json
import os
import uuid
from datetime import datetime, time, timedelta
from pathlib import Path

import pytest
from django.utils import timezone

from core_apps.features.models import TenancyInvitation
from core_apps.features.tests.test_rental_phase2 import (
    authenticated,
    rental_participants,
)
from core_apps.properties.models import PropertyVisit

PROPERTIES = "/api/v1/properties/"
FEATURES = "/api/v1/features/v1/"


def inventory_fixture(property_obj, offer_id, scope="bed"):
    room_a, room_b, bed = (str(uuid.uuid4()) for _ in range(3))
    rooms = [
        {
            "id": room_a,
            "name": "الغرفة الأولى",
            "capacity": 2,
            "bathroom_access": ["shared"],
            "beds": [{"id": bed, "name": "السرير الأول"}],
        },
        {"id": room_b, "name": "Second room", "capacity": 1, "beds": []},
    ]
    selected_rooms = (
        []
        if scope == "entire_property"
        else ([room_a, room_b] if scope == "room_group" else [room_a])
    )
    offer = {
        "id": offer_id,
        "revision": 1,
        "rental_scope": scope,
        "name": "Selected accommodation",
        "room_ids": selected_rooms,
        "availability": "available",
        "archived": False,
        "terms": {"price": "1500.00", "price_period": "monthly"},
        "offer_link": "https://example.test/offers/selected",
    }
    if scope == "bed":
        offer["bed_id"] = bed
    property_obj.rental_inventory = {
        "schema_version": 1,
        "revision": 1,
        "mode": "whole" if scope == "entire_property" else "partial",
        "rooms": rooms,
        "offers": [offer],
    }
    property_obj.save(update_fields=["rental_inventory"])
    return {
        "property_id": str(property_obj.id),
        "offer_id": offer_id,
        "offer_revision": 1,
        "rental_scope": scope,
        "name": "Selected accommodation",
        "room_ids": selected_rooms,
        "room_names": (
            []
            if scope == "entire_property"
            else (
                ["الغرفة الأولى", "Second room"]
                if scope == "room_group"
                else ["الغرفة الأولى"]
            )
        ),
        "bed_id": bed if scope == "bed" else None,
        "bed_name": "السرير الأول" if scope == "bed" else None,
        "capacity": (
            None if scope == "entire_property" else (3 if scope == "room_group" else 2)
        ),
        "bathroom_access": [] if scope == "entire_property" else ["shared"],
        "availability": "available",
        "archived": False,
        "offer_link": "https://example.test/offers/selected",
        "terms": {"price": "1500.00", "price_period": "monthly"},
    }


def available_appointment(owner, property_obj):
    tomorrow = timezone.localdate() + timedelta(days=1)
    response = authenticated(owner).put(
        PROPERTIES + f"owner/properties/{property_obj.id}/availability/",
        {
            "availability_date": tomorrow.isoformat(),
            "slots": [{"time": "14:00:00", "is_enabled": True}],
        },
        format="json",
    )
    assert response.status_code == 200, response.data
    return {"visit_date": tomorrow.isoformat(), "visit_time": "14:00:00"}


def changed_inventory(property_obj):
    inventory = copy.deepcopy(property_obj.rental_inventory)
    inventory["revision"] += 1
    inventory["offers"][0]["revision"] += 1
    inventory["offers"][0]["terms"]["price"] = "2700.00"
    inventory["offers"][0]["name"] = "Renamed current offer"
    inventory["rooms"][0]["name"] = "Renamed current room"
    inventory["rooms"][0]["capacity"] = 3
    inventory["rooms"][0]["beds"][0]["name"] = "Renamed current bed"
    property_obj.rental_inventory = inventory
    property_obj.save(update_fields=["rental_inventory"])


@pytest.mark.django_db
@pytest.mark.parametrize("scope", ["entire_property", "room", "room_group", "bed"])
def test_public_booking_details_decision_and_invitation_share_complete_frozen_snapshot(
    rental_participants, monkeypatch, scope
):
    owner, tenant, _, property_obj, offer_id = rental_participants
    expected = inventory_fixture(property_obj, offer_id, scope)
    owner_client, tenant_client = authenticated(owner), authenticated(tenant)
    payload = {
        **available_appointment(owner, property_obj),
        "offer_id": offer_id,
        "expected_offer_revision": 1,
        "note": "Synthetic booking snapshot regression",
    }
    operation_key = str(uuid.uuid4())
    booked = tenant_client.post(
        PROPERTIES + f"{property_obj.id}/visits/",
        payload,
        format="json",
        HTTP_IDEMPOTENCY_KEY=operation_key,
    )
    assert booked.status_code == 201, booked.data
    visit = PropertyVisit.objects.get(id=booked.data["id"])
    assert booked.data["offer_snapshot"] == expected
    assert visit.offer_snapshot == expected
    owner_path = PROPERTIES + f"owner/visits/requests/{visit.id}/"
    tenant_path = PROPERTIES + f"visits/requests/{visit.id}/"
    examples = {"booking": booked.json()}
    property_detail = tenant_client.get(PROPERTIES + f"{property_obj.id}/")
    assert property_detail.status_code == 200, property_detail.data
    examples["property_detail"] = property_detail.json()
    for name, client, endpoint in (
        ("tenant_detail", tenant_client, tenant_path),
        ("owner_detail", owner_client, owner_path),
    ):
        detail = client.get(endpoint)
        assert detail.status_code == 200, detail.data
        assert detail.data["offer_snapshot"] == expected
        examples[name] = detail.json()
    accepted = owner_client.post(owner_path + "accept/", {}, format="json")
    assert accepted.status_code == 200, accepted.data
    visit.refresh_from_db()
    after_start = timezone.make_aware(datetime.combine(visit.visit_date, time(14, 1)))
    monkeypatch.setattr(timezone, "now", lambda: after_start)
    decision = tenant_client.post(
        PROPERTIES + f"visits/{visit.id}/post-visit-decision/",
        {
            "decision": "proceed",
            "attended": True,
            "expected_revision": visit.revision,
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert decision.status_code == 200, decision.data
    examples["decision"] = decision.json()
    assert decision.data["offer_snapshot"] == expected
    visit.refresh_from_db()
    assert visit.post_visit_decision.offer_snapshot == expected
    invitation = owner_client.post(
        FEATURES + "tenancy-invitations/",
        {
            "property_id": str(property_obj.id),
            "tenant_id": str(tenant.id),
            "offer_id": offer_id,
            "expected_offer_revision": 1,
            "source_visit_id": str(visit.id),
            "source_decision_id": str(visit.post_visit_decision.id),
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert invitation.status_code == 201, invitation.data
    assert invitation.data["offer_snapshot"] == expected
    examples["invitation"] = invitation.json()

    changed_inventory(property_obj)
    for client, endpoint in ((owner_client, owner_path), (tenant_client, tenant_path)):
        detail = client.get(endpoint)
        assert detail.status_code == 200
        assert detail.data["offer_snapshot"] == expected
    replay = tenant_client.post(
        PROPERTIES + f"{property_obj.id}/visits/",
        payload,
        format="json",
        HTTP_IDEMPOTENCY_KEY=operation_key,
    )
    assert replay.status_code == 201 and replay.data["id"] == str(visit.id)
    assert replay.data["offer_snapshot"] == expected
    visit.refresh_from_db()
    assert visit.offer_snapshot == visit.post_visit_decision.offer_snapshot == expected
    assert TenancyInvitation.objects.get().offer_snapshot == expected
    assert PropertyVisit.objects.count() == 1
    output = os.environ.get("SOKOUN_POST_VISIT_BOOKING_ARTIFACT_DIR")
    if output:
        directory = Path(output)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"visit-offer-snapshot-{scope}.json").write_text(
            json.dumps(
                {
                    "source": "actual_local_django_public_booking",
                    "scope": scope,
                    "scenarios": examples,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        )


@pytest.mark.django_db
def test_existing_thin_snapshot_is_never_backfilled_from_current_inventory(
    rental_participants,
):
    owner, tenant, _, property_obj, offer_id = rental_participants
    inventory_fixture(property_obj, offer_id)
    thin = {
        "property_id": str(property_obj.id),
        "offer_id": offer_id,
        "offer_revision": 1,
        **copy.deepcopy(property_obj.rental_inventory["offers"][0]),
    }
    visit = PropertyVisit.objects.create(
        property=property_obj,
        tenant=tenant,
        status="confirmed",
        visit_date=timezone.localdate() - timedelta(days=1),
        visit_time=time(14),
        offer_id=offer_id,
        offer_snapshot=thin,
    )
    changed_inventory(property_obj)
    for client, endpoint in (
        (authenticated(tenant), PROPERTIES + f"visits/requests/{visit.id}/"),
        (authenticated(owner), PROPERTIES + f"owner/visits/requests/{visit.id}/"),
    ):
        detail = client.get(endpoint)
        assert detail.status_code == 200
        assert detail.data["offer_snapshot"] == thin
        assert "room_names" not in detail.data["offer_snapshot"]
    decision = authenticated(tenant).post(
        PROPERTIES + f"visits/{visit.id}/post-visit-decision/",
        {
            "decision": "proceed",
            "attended": True,
            "expected_revision": visit.revision,
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert decision.status_code == 200, decision.data
    visit.refresh_from_db()
    assert visit.offer_snapshot == visit.post_visit_decision.offer_snapshot == thin
    assert visit.offer_snapshot["terms"]["price"] == "1500.00"


@pytest.mark.django_db
@pytest.mark.parametrize("invalid", ["stale", "archived", "missing"])
def test_offer_validation_still_rejects_invalid_booking_without_creating_visit(
    rental_participants, invalid
):
    owner, tenant, _, property_obj, offer_id = rental_participants
    inventory_fixture(property_obj, offer_id)
    appointment = available_appointment(owner, property_obj)
    if invalid == "archived":
        property_obj.rental_inventory["offers"][0]["archived"] = True
        property_obj.save(update_fields=["rental_inventory"])
    response = authenticated(tenant).post(
        PROPERTIES + f"{property_obj.id}/visits/",
        {
            **appointment,
            "offer_id": str(uuid.uuid4()) if invalid == "missing" else offer_id,
            "expected_offer_revision": 2 if invalid == "stale" else 1,
        },
        format="json",
    )
    assert response.status_code == 400, response.data
    assert not PropertyVisit.objects.exists()
