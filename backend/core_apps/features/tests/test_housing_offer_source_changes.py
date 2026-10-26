"""A changed listing records exact offer impact, not a replacement commitment."""

# flake8: noqa: F401,F811
from copy import deepcopy
import uuid
import pytest
from .test_housing_request_reviews import cycle, read, post, command, API
from .test_rental_phase2 import rental_participants, authenticated
from core_apps.properties.models import Property
from core_apps.properties.services.property import PropertyService
from core_apps.properties.tests.test_viewing_listing_changes import edit_offer
from core_apps.features.planning_models import HousingOffer, PlanningEvent
from core_apps.features.services.planning import selection_payload
from core_apps.features.services.tenancy_invitations import resolve_offer_snapshot
from core_apps.features.services.housing_request_notifications import notification_copy
from core_apps.features.services.planning_notifications import deliver_planning_events
from core_apps.features.services.request_counts import pending_request_counts

pytestmark = pytest.mark.django_db


def restore_listing(prop):
    # Simulated moderation completion only; the moderation lifecycle has separate tests.
    Property.objects.filter(pk=prop.pk).update(
        status=Property.Status.VERIFIED, is_verified=True
    )
    prop.refresh_from_db()


def test_material_change_preserves_old_price_and_requires_explicit_replacement(cycle):
    owner, tenant, other, parent, original, _, original_body = cycle
    offer = HousingOffer.objects.get(id=original["id"])
    prop = offer.property
    old_snapshot = deepcopy(offer.selection)
    terms = {**prop.rental_inventory["offers"][0]["terms"], "price": "12000"}
    prop = edit_offer(prop, terms=terms)
    restore_listing(prop)
    changed = read(original, tenant)
    assert changed["status"] == "incompatible"
    assert changed["revision"] == original["revision"] + 1
    assert changed["selection"] == old_snapshot
    assert changed["rent"] == original["rent"]
    assert changed["allowed_actions"] == ["decline"]
    assert changed["source_changes"][0]["listing_changes"] == [
        {"field": "price", "before": "10000", "after": "12000"}
    ]
    assert "reconfirm" not in read(original, owner)["allowed_actions"]
    assert (
        authenticated(other).get(API + f"housing-offers/{offer.id}/").status_code == 404
    )
    assert (
        authenticated(tenant)
        .get(API + f'housing-requests/{parent["id"]}/offers/', {"scope": "history"})
        .data["count"]
        == 1
    )
    notices = PlanningEvent.objects.filter(
        destination__event_kind="housing_offer_source_changed"
    )
    assert {x.recipient_id: x.destination["workspace"] for x in notices} == {
        owner.pk: "owner",
        tenant.pk: "individual",
    }
    assert all(x.destination["housing_offer_id"] == str(offer.id) for x in notices)
    assert all(x.destination["target_id"] == parent["id"] for x in notices)
    assert "source changed" in notification_copy(notices.first())["title"]
    assert deliver_planning_events(event_kinds=["housing_offer_source_changed"]) == 2
    assert deliver_planning_events(event_kinds=["housing_offer_source_changed"]) == 0
    _, current = resolve_offer_snapshot(
        prop, old_snapshot["offer_id"], old_snapshot["offer_revision"] + 1
    )
    body = {
        **command(),
        "request_id": parent["id"],
        "request_revision": parent["revision"],
        "selection": selection_payload(current),
        "replaces_offer_id": original["id"],
        "replaced_offer_revision": changed["revision"],
    }
    replacement = post(
        owner, f'housing-requests/{parent["id"]}/offers/', body, 201
    ).data["resource"]
    assert replacement["rent"]["amount_minor"] == 1200000
    assert replacement["replaces_offer_id"] == original["id"]
    assert replacement["source_changes"] == []
    assert read(original, owner)["source_changes"] == changed["source_changes"]
    assert read(original, owner)["status"] == "superseded"
    assert (
        post(owner, f'housing-requests/{parent["id"]}/offers/', body, 201).data[
            "resource"
        ]["id"]
        == replacement["id"]
    )
    # The old notification authorizes the same request/offer history after replacement.
    assert notification_copy(notices.first())


def test_unrelated_offer_and_editorial_change_do_not_reset_response(cycle):
    owner, _, _, _, original, _, _ = cycle
    offer = HousingOffer.objects.get(id=original["id"])
    prop = offer.property
    sibling = deepcopy(prop.rental_inventory["offers"][0])
    sibling.update(id=str(uuid.uuid4()), name="Other unit")
    prop.rental_inventory["offers"].append(sibling)
    prop.save(update_fields=["rental_inventory"])
    inventory = deepcopy(prop.rental_inventory)
    inventory["revision"] += 1
    inventory["offers"][1]["availability"] = "unavailable"
    prop = PropertyService.update_property(
        prop, {"rental_inventory": inventory, "title": "New caption"}
    )
    restore_listing(prop)
    current = read(original, owner)
    assert current["source_changes"] == [] and current["review_state"] == "current"
    assert current["revision"] == original["revision"] and current["status"] == "sent"


@pytest.mark.parametrize(
    "field,change",
    [
        ("availability", {"availability": "unavailable"}),
        ("capacity", {"capacity": 1}),
    ],
)
def test_unit_change_is_recorded_once_and_terminal_history_is_preserved(
    cycle, field, change
):
    owner, _, _, _, original, _, _ = cycle
    offer = HousingOffer.objects.get(id=original["id"])
    prop = edit_offer(offer.property, **change)
    current = read(original, owner)
    assert field in [
        x["field"] for x in current["source_changes"][0]["listing_changes"]
    ]
    prop = PropertyService.update_property(prop, {"title": "Another caption"})
    assert len(read(original, owner)["source_changes"]) == 1
    offer.refresh_from_db()
    offer.status = "withdrawn"
    offer.save(update_fields=["status"])
    edit_offer(prop, terms={"price": "13000", "price_period": "monthly"})
    assert len(read(original, owner)["source_changes"]) == 1


def test_required_amenity_changes_affect_only_requests_that_required_it(cycle):
    owner, _, _, _, original, _, _ = cycle
    offer = HousingOffer.objects.get(id=original["id"])
    prop = offer.property
    prop.has_wifi = True
    prop.save(update_fields=["has_wifi"])
    prop = PropertyService.update_property(prop, {"has_wifi": False})
    assert read(original, owner)["source_changes"] == []
    restore_listing(prop)
    prop.has_wifi = True
    prop.save(update_fields=["has_wifi"])
    parent = offer.request
    parent.criteria["amenities"] = ["wifi"]
    parent.save(update_fields=["criteria"])
    PropertyService.update_property(prop, {"has_wifi": False})
    current = read(original, owner)
    assert current["source_changes"][0]["listing_changes"] == [
        {"field": "amenity:wifi", "before": True, "after": False}
    ]


@pytest.mark.django_db(transaction=True)
def test_listing_edit_and_offer_replacement_serialize_without_old_terms_becoming_current(
    cycle,
):
    from .test_cycle_concurrency import parallel_calls

    owner, _, _, parent, original, _, initial = cycle
    offer = HousingOffer.objects.get(id=original["id"])
    prop = offer.property
    body = {
        **initial,
        **command(),
        "replaces_offer_id": original["id"],
        "replaced_offer_revision": original["revision"],
    }

    def run(index):
        if index == 0:
            edit_offer(Property.objects.get(pk=prop.pk), availability="unavailable")
            return None
        return authenticated(owner).post(
            API + f'housing-requests/{parent["id"]}/offers/', body, format="json"
        )

    _, response = parallel_calls(run)
    assert response.status_code in (201, 400, 409), response.data
    # If replacement won the lock, it too must receive the subsequent source change.
    for row in HousingOffer.objects.filter(property=prop, status="sent"):
        assert row.review_state == "incompatible" and len(row.source_changes) == 1
