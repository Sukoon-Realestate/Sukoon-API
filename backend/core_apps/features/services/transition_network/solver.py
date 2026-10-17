"""Bounded two/three-person proposals using canonical physical resource keys."""

import hashlib
import itertools
import json
from time import monotonic
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from rest_framework.exceptions import APIException
from ...transition_network_models import (
    MoveIntent,
    TransitionCandidate,
    TransitionParticipant,
)
from ..planning import offer_money, selection_payload
from ..rental_lifecycle.inventory import assert_available, topology_digest, unit_keys
from ..rental_phase2 import RentalConflict
from ..student_housing.policies import validate_occupants
from ..tenancy_invitations import resolve_offer_snapshot
from .commands import check_source
from .vacancies import endpoints, available_endpoint
from config.advanced_housing import POLICY_VERSION
from core_apps.properties.models import Property

MAX_POOL = 24
MAX_CANDIDATES = 8
MAX_PROPOSALS = 1024
MAX_SEARCH_SECONDS = 3


def source_snapshot(intent):
    check_source(intent, publishing=True)
    prop = intent.lease.property
    if (
        prop.status != "verified"
        or not prop.is_verified
        or not prop.is_ownership_verified
        or not prop.owner.is_verified
        or not prop.owner.is_active
        or prop.retired_at
    ):
        raise RentalConflict(
            "The source inventory needs review.", code="snapshot_stale"
        )
    offer = next(
        (
            value
            for value in (prop.rental_inventory or {}).get("offers", [])
            if str(value.get("id")) == intent.lease.offer_id
        ),
        None,
    )
    if not offer:
        raise RentalConflict("The offer is unavailable.", code="snapshot_stale")
    _, raw = resolve_offer_snapshot(prop, intent.lease.offer_id, offer.get("revision"))
    selected = selection_payload(raw)
    rent, deposit = offer_money(selected)
    terms = selected["terms"]
    months = terms.get("rental_period")
    if (
        deposit is None
        or terms.get("price_period") != "monthly"
        or not selected.get("capacity")
        or type(months) is not int
        or months < 1
        or terms.get("suitable_for") != "all"
    ):
        raise RentalConflict(
            "The current monthly quote is incomplete.", code="quote_incomplete"
        )
    return {
        "intent_id": str(intent.id),
        "intent_revision": intent.revision,
        "lease_id": str(intent.lease.id),
        "lease_revision": intent.lease.revision,
        "transition_id": str(intent.source_transition.id),
        "transition_revision": intent.source_transition.revision,
        "selection": selected,
        "owner_id": str(prop.owner.id),
        "city_id": str(prop.city.id),
        "property_type": prop.property_type.slug,
        "topology_digest": topology_digest(prop.rental_inventory),
        "physical_keys": unit_keys(prop, selected),
        "furnished": prop.is_furnished,
        "amenities": property_amenities(prop),
        "rent_minor": rent,
        "deposit_minor": deposit,
        "available_on": str(
            intent.source_transition.requested_on + timedelta(days=intent.turnover_days)
        ),
        "release_confirmed": intent.lease.status == "ended"
        and intent.lease.occupancy_status == "returned",
    }


def property_amenities(prop):
    return sorted(
        name
        for name in (
            "wifi",
            "elevator",
            "garage",
            "security",
            "balcony",
            "air_conditioning",
            "near_metro",
            "natural_gas",
            "electricity_meter",
            "water_meter",
        )
        if getattr(prop, "has_" + name, False)
    )


def validate_cycle(intents, sources, endpoint=None):
    """Independently check every assignment; never infer eligibility from a match."""
    legs, occupied = [], []
    for index, incoming in enumerate(intents):
        outgoing = (
            None
            if endpoint is not None and index == len(intents) - 1
            else intents[(index + 1) % len(intents)]
        )
        source = endpoint if outgoing is None else sources[str(outgoing.id)]
        criteria = incoming.criteria
        start, end = date.fromisoformat(criteria["start_on"]), date.fromisoformat(
            criteria["end_on"]
        )
        gap = (start - incoming.source_transition.requested_on).days
        if (
            (
                outgoing is not None
                and start < date.fromisoformat(source["available_on"])
            )
            or not 0 <= gap <= incoming.max_gap_days
            or end
            < start
            + relativedelta(months=source["selection"]["terms"]["rental_period"])
            or criteria["city_id"] != source["city_id"]
            or criteria["rental_scope"] != source["selection"]["rental_scope"]
            or (
                criteria["property_type"]
                and criteria["property_type"] != source["property_type"]
            )
            or source["rent_minor"] > criteria["budget_max"]["amount_minor"]
            or source["rent_minor"]
            < (criteria.get("budget_min") or {}).get("amount_minor", 0)
            or source["deposit_minor"] > incoming.max_deposit_minor
            or (
                criteria.get("furnished") is not None
                and criteria["furnished"] != source["furnished"]
            )
            or not set(criteria.get("amenities", [])) <= set(source["amenities"])
        ):
            return None
        prop = (
            outgoing.lease.property
            if outgoing is not None
            else Property.objects.get(id=source["selection"]["property_id"])
        )
        keys = set(source["physical_keys"])
        for previous_prop, previous_keys, previous_start, previous_end in occupied:
            if (
                prop.id == previous_prop
                and keys & previous_keys
                and start < previous_end
                and previous_start < end
            ):
                return None
        try:
            validate_occupants(
                prop, source["selection"], [incoming.user], start, end, occupant_count=1
            )
            # Excluding this outgoing lease is permitted only beyond its actual
            # contractual end and approved departure + whole-day turnover.
            if outgoing is not None and start < outgoing.lease.end_date:
                return None
            if outgoing is None:
                if not available_endpoint(source, start, end):
                    return None
            else:
                assert_available(
                    prop, source["selection"], start, end, exclude_lease=outgoing.lease
                )
        except APIException:
            return None
        occupied.append((prop.id, keys, start, end))
        legs.append(
            {
                "user_id": str(incoming.user.id),
                "intent_id": str(incoming.id),
                "source": source,
                "start_on": str(start),
                "end_on": str(end),
                "gap_days": gap,
            }
        )
    return {
        "legs": legs,
        "result_status": (
            "feasible"
            if all(sources[str(row.id)]["release_confirmed"] for row in intents)
            else "unknown"
        ),
        "policy_version": POLICY_VERSION,
        "kind": "open_chain" if endpoint is not None else "cycle",
        "endpoint": endpoint,
        "source_manifest": {str(row.id): sources[str(row.id)] for row in intents},
        "objectives": {
            "moves": len(legs),
            "total_gap_days": sum(leg["gap_days"] for leg in legs),
            "monthly_rent_change_minor": sum(
                leg["source"]["rent_minor"] - row.lease.rent_amount_minor
                for leg, row in zip(legs, intents)
            ),
        },
        "inventory_reserved": False,
    }


def calculate(run):
    origin = run.intent
    if (
        origin.status != "matching"
        or origin.revision != run.input_revision
        or not origin.matching_consent
        or origin.expires_at <= timezone.now()
        or not origin.user.is_active
        or not origin.user.is_verified
    ):
        run.result_status = "stale"
        return
    pool = list(
        MoveIntent.objects.filter(
            status="matching",
            matching_consent=True,
            expires_at__gt=timezone.now(),
            user__is_active=True,
            user__is_verified=True,
        )
        .exclude(pk=origin.pk)
        .select_related(
            "user",
            "lease__property__owner",
            "lease__property__city",
            "lease__property__property_type",
            "source_transition",
        )
        .order_by("pk")[: MAX_POOL + 1]
    )
    run.pool_limited = len(pool) > MAX_POOL
    pool = pool[:MAX_POOL]
    sources, eligible = {}, []
    for intent in [origin, *pool]:
        try:
            sources[str(intent.id)] = source_snapshot(intent)
            eligible.append(intent)
        except APIException:
            if intent.pk == origin.pk:
                run.result_status, run.failure_code = (
                    "invalid_input",
                    "outgoing_review_required",
                )
                return
    run.searched_count = len(eligible)
    peers = [
        item
        for item in eligible
        if item.pk != origin.pk and item.user_id != origin.user_id
    ]
    vacant, vacancy_limited = endpoints(eligible)
    run.pool_limited = run.pool_limited or vacancy_limited
    candidate_count, examined, started = 0, 0, monotonic()
    options = []

    # Breadth first keeps a direct vacant endpoint and shorter cycles reachable
    # even when the bounded market is dense. The validator remains independent.
    def proposals():
        for length in (0, 1, 2):
            for others in itertools.permutations(peers, length):
                chain = [origin, *others]
                if len({item.user_id for item in chain}) != len(chain):
                    continue
                if length:
                    yield chain, None
                for endpoint in vacant:
                    yield chain, endpoint

    for chain, endpoint in proposals():
        if examined >= MAX_PROPOSALS or monotonic() - started > MAX_SEARCH_SECONDS:
            run.pool_limited = True
            break
        examined += 1
        snapshot = validate_cycle(chain, sources, endpoint=endpoint)
        if snapshot is not None:
            options.append((chain, snapshot))
    options.sort(
        key=lambda pair: (
            pair[1]["objectives"]["total_gap_days"],
            pair[1]["objectives"]["moves"],
            pair[1]["objectives"]["monthly_rent_change_minor"],
        )
    )
    for chain, snapshot in options[:MAX_CANDIDATES]:
        digest = hashlib.sha256(
            json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        candidate = TransitionCandidate.objects.create(
            run=run,
            snapshot=snapshot,
            snapshot_digest=digest,
            expires_at=min(
                timezone.now() + timedelta(hours=1),
                *(item.expires_at for item in chain)
            ),
        )
        TransitionParticipant.objects.bulk_create(
            [
                TransitionParticipant(
                    candidate=candidate,
                    intent=item,
                    user=item.user,
                    intent_revision=item.revision,
                )
                for item in chain
            ]
        )
        candidate_count += 1
    # No solution in a truncated pool proves nothing about the wider market.
    run.result_status = (
        "feasible"
        if run.candidates.filter(snapshot__result_status="feasible").exists()
        else "unknown" if candidate_count or run.pool_limited else "infeasible"
    )
