"""Canonical vacant endpoints for bounded open chains; no synthetic supply."""

from datetime import date
from rest_framework.exceptions import APIException
from core_apps.properties.models import Property
from ...models import Lease
from ..planning import public_properties, selection_payload, offer_money
from ..tenancy_invitations import resolve_offer_snapshot
from ..rental_lifecycle.inventory import topology_digest, unit_keys, assert_available
from ..rental_phase2 import RentalConflict

MAX_ENDPOINTS = 12


def vacancy_snapshot(prop, offer_id):
    from .solver import property_amenities

    if (
        prop.status != "verified"
        or not prop.is_verified
        or not prop.is_ownership_verified
        or prop.retired_at
        or not prop.owner.is_active
        or not prop.owner.is_verified
    ):
        raise RentalConflict(
            "The source inventory needs review.", code="snapshot_stale"
        )
    offer = next(
        (
            row
            for row in (prop.rental_inventory or {}).get("offers", [])
            if str(row.get("id")) == str(offer_id)
        ),
        None,
    )
    if not offer:
        raise RentalConflict("The offer is unavailable.", code="snapshot_stale")
    _, raw = resolve_offer_snapshot(prop, str(offer_id), offer.get("revision"))
    selection = selection_payload(raw)
    rent, deposit = offer_money(selection)
    terms = selection["terms"]
    if (
        deposit is None
        or terms.get("price_period") != "monthly"
        or type(terms.get("rental_period")) is not int
        or terms["rental_period"] < 1
        or not selection.get("capacity")
        or terms.get("suitable_for") != "all"
    ):
        raise RentalConflict(
            "The current monthly quote is incomplete.", code="quote_incomplete"
        )
    keys = set(unit_keys(prop, selection))
    # A listing alone never establishes physical return of an existing occupant.
    for lease in Lease.objects.filter(
        property=prop,
        occupancy_status__in=["occupied", "move_out_pending", "handover_disputed"],
    ):
        if keys & set(unit_keys(prop, lease.offer_snapshot)):
            raise RentalConflict(
                "Possession has not been returned for this accommodation.",
                code="occupancy_unresolved",
            )
    return {
        "kind": "vacant",
        "selection": selection,
        "owner_id": str(prop.owner.id),
        "city_id": str(prop.city.id),
        "property_type": prop.property_type.slug,
        "topology_digest": topology_digest(prop.rental_inventory),
        "physical_keys": sorted(keys),
        "furnished": prop.is_furnished,
        "amenities": property_amenities(prop),
        "rent_minor": rent,
        "deposit_minor": deposit,
        "release_confirmed": True,
    }


def available_endpoint(source, starts_on, ends_on):
    prop = Property.objects.get(id=source["selection"]["property_id"])
    keys = set(source["physical_keys"])
    # Include future canonical leases even when an older source lacks day locks.
    for lease in Lease.objects.filter(
        property=prop,
        start_date__lt=ends_on,
        end_date__gt=starts_on,
        status__in=[
            "draft",
            "pending_signatures",
            "signed",
            "active",
            "termination_pending",
        ],
    ):
        if keys & set(unit_keys(prop, lease.offer_snapshot)):
            return False
    assert_available(prop, source["selection"], starts_on, ends_on)
    return True


def endpoints(intents):
    cities = {row.criteria["city_id"] for row in intents}
    sources, limited = [], False
    rows = public_properties().filter(city__id__in=cities).order_by("pk")[:49]
    for index, prop in enumerate(rows):
        if index == 48:
            limited = True
            break
        for offer in (prop.rental_inventory or {}).get("offers", []):
            try:
                source = vacancy_snapshot(prop, offer.get("id"))
                if not any(
                    available_endpoint(
                        source,
                        date.fromisoformat(row.criteria["start_on"]),
                        date.fromisoformat(row.criteria["end_on"]),
                    )
                    for row in intents
                ):
                    continue
            except APIException:
                continue
            if len(sources) == MAX_ENDPOINTS:
                limited = True
                return sources, limited
            sources.append(source)
    return sources, limited
