"""Deterministic bounded package construction, with explicit search limits.

Rank by covered people, then total monthly rent and deposit. Feasibility is
rechecked against canonical resources before publishing; no run reserves supply.
"""

from collections import defaultdict
from datetime import date
from time import monotonic
from types import SimpleNamespace
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.utils import timezone
from rest_framework.exceptions import APIException, NotFound
from core_apps.users.models import User
from ...advanced_tender_models import TenderPackageRun, TenderBidLine, PackageCandidate
from ..planning import check_revision, selection, offer_money
from ..rental_phase2 import fingerprint, RentalConflict
from ..rental_lifecycle.inventory import assert_available, unit_keys
from ..student_housing.policies import validate_occupants
from .access import admin, current, get_tender
from .commands import require_action, validate_package
from .pricing import quote_allocations

MAX_LINES = 48
MAX_NODES = 10000
MAX_SECONDS = 3
MAX_ALTERNATIVES = 4


def source(tender):
    return {
        "demand": tender.active_snapshot.digest,
        "bids": [
            {"id": str(x.id), "revision": x.revision}
            for x in tender.bids.filter(
                status="submitted",
                snapshot=tender.active_snapshot,
                expires_at__gt=timezone.now(),
            ).order_by("id")
        ],
    }


def create(request, tender):
    require_action(request.user, tender, "package-runs")
    check_revision(tender.revision, request.data.get("tender_revision"))
    if request.data.get("snapshot_id") != str(tender.active_snapshot.id):
        raise RentalConflict("The published snapshot changed.", code="snapshot_changed")
    data = source(tender)
    run = TenderPackageRun.objects.create(
        tender=tender,
        snapshot=tender.active_snapshot,
        created_by=request.user,
        source_digest=fingerprint(data),
        input=data,
    )
    from .jobs import enqueue

    transaction.on_commit(lambda: enqueue(str(run.id)))
    return run


def get_run(user, identifier, *, lock=False):
    query = TenderPackageRun.objects.select_related("tender", "snapshot")
    if lock:
        query = query.select_for_update(of=("self",))
    run = get_object_or_404(query, id=identifier)
    tender = get_tender(user, run.tender.id)
    if not admin(user, tender):
        raise NotFound()
    return run


def payload(run, user):
    get_run(user, run.id)
    return {
        "id": str(run.id),
        "revision": run.revision,
        "tender_id": str(run.tender.id),
        "snapshot_id": str(run.snapshot.id),
        "status": run.status,
        "result": run.result,
        "package_ids": [str(x) for x in run.packages.values_list("id", flat=True)],
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }


def calculate(run):
    tender = run.tender
    if (
        not current(tender)
        or tender.status != "published"
        or tender.active_snapshot_id != run.snapshot_id
        or fingerprint(source(tender)) != run.source_digest
        or not admin(run.created_by, tender)
    ):
        run.status = "source_changed"
        run.result = {"optimality_proven": False, "feasible_count": 0}
        return
    request = SimpleNamespace(user=run.created_by)
    requirements = {x["participant_id"]: x for x in run.snapshot.private_requirements}
    people = {
        str(x.id): x
        for x in User.objects.filter(
            id__in=requirements, is_active=True, is_verified=True
        )
    }
    lines = list(
        TenderBidLine.objects.filter(bid__id__in=[b["id"] for b in run.input["bids"]])
        .select_related("bid", "offer__property", "offer__owner")
        .prefetch_related("bid__lines")
        .order_by("id")[: MAX_LINES + 1]
    )
    truncated = len(lines) > MAX_LINES
    lines = lines[:MAX_LINES]
    from core_apps.properties.models import Property

    list(
        Property.objects.select_for_update()
        .filter(pk__in={line.offer.property_id for line in lines})
        .order_by("pk")
    )
    choices, prepared = defaultdict(list), {}
    excluded = 0
    # Inspect every bounded canonical selection once, not in the search loop.
    for line in lines:
        try:
            prop, selected = selection(request, line.offer.selection)
            rent, deposit = offer_money(selected)
            if (
                prop.owner_id != line.bid.owner_id
                or not prop.is_ownership_verified
                or prop.retired_at
            ):
                raise ValueError
            if rent != line.offer.rent_minor or deposit != line.offer.deposit_minor:
                raise ValueError
            keys = {f"{prop.id}/{x}" for x in unit_keys(prop, selected)}
            if sorted(keys) != line.physical_keys:
                raise ValueError
        except (APIException, ValueError, Http404):
            excluded += 1
            continue
        prepared[str(line.id)] = (line, prop, selected, keys, deposit)
        for person, req in requirements.items():
            start, end = date.fromisoformat(req["start_on"]), date.fromisoformat(
                req["end_on"]
            )
            if (
                person not in people
                or req["rental_scope"] != selected["rental_scope"]
                or start < line.bid.start_on
                or end > line.bid.end_on
                or deposit is None
                or deposit > req["deposit_limit_minor"]
            ):
                continue
            try:
                assert_available(prop, selected, start, end)
                validate_occupants(
                    prop, selected, [people[person]], start, end, occupant_count=1
                )
            except (APIException, Http404):
                continue
            choices[person].append(str(line.id))
    ordered = sorted(requirements, key=lambda person: (len(choices[person]), person))
    visited, limited, candidates = 0, truncated, []
    deadline = monotonic() + MAX_SECONDS

    def visit(index, assigned, occupied):
        nonlocal visited, limited
        visited += 1
        if visited > MAX_NODES or monotonic() > deadline:
            limited = True
            return
        if index < len(ordered):
            person, req = ordered[index], requirements[ordered[index]]
            start, end = date.fromisoformat(req["start_on"]), date.fromisoformat(
                req["end_on"]
            )
            for key in choices[person]:
                line, prop, selected, physical, _ = prepared[key]
                # Each quoted line is a distinct unit, never extra quantity from reusing it.
                if any(
                    key == old[1]
                    or (physical & old[2] and start < old[4] and old[3] < end)
                    for old in occupied
                ):
                    continue
                visit(
                    index + 1,
                    [*assigned, (person, key)],
                    [*occupied, (person, key, physical, start, end)],
                )
                if visited > MAX_NODES or monotonic() > deadline:
                    limited = True
                    return
            visit(index + 1, assigned, occupied)
            return
        if not assigned:
            return
        bids, prices = defaultdict(list), {}
        for person, key in assigned:
            bids[prepared[key][0].bid_id].append(prepared[key][0])
        if len(bids) > 1 and any(not lines[0].bid.combines for lines in bids.values()):
            return
        if len({prepared[key][1].pk for _, key in assigned}) > 1 and any(
            not requirements[person]["multi_property"] for person, _ in assigned
        ):
            return
        try:
            for chosen in bids.values():
                prices.update(quote_allocations(chosen[0].bid, chosen))
        except (APIException, Http404):
            return
        if any(
            prices[key] > requirements[person]["rent_limit_minor"]
            or len(assigned) < requirements[person]["minimum_completion"]
            for person, key in assigned
        ):
            return
        score = (
            -len(assigned),
            sum(prices[key] for _, key in assigned),
            sum(prepared[key][4] for _, key in assigned),
            tuple(sorted(assigned)),
        )
        candidates.append(
            (
                score,
                [
                    {"participant_id": person, "line_id": key}
                    for person, key in assigned
                ],
            )
        )
        candidates.sort(key=lambda item: item[0])
        del candidates[MAX_ALTERNATIVES:]

    visit(0, [], [])
    for _, proposed in candidates:
        try:
            allocations, missing = validate_package(request, tender, proposed)
        except (APIException, Http404):
            continue
        package = PackageCandidate.objects.create(
            tender=tender,
            snapshot=run.snapshot,
            allocations=allocations,
            unallocated_ids=missing,
            digest=fingerprint(
                {
                    "snapshot": run.snapshot.digest,
                    "allocations": allocations,
                    "mode": "independent_participants",
                }
            ),
            total_rent_minor=sum(x["rent_minor"] for x in allocations),
            total_deposit_minor=sum(x["deposit_minor"] for x in allocations),
        )
        run.packages.add(package)
    count = run.packages.count()
    run.status = (
        "feasible" if count else ("limit_reached" if limited else "no_feasible_package")
    )
    run.result = {
        "states_explored": min(visited, MAX_NODES),
        "node_limit": MAX_NODES,
        "candidate_lines": len(lines),
        "excluded_lines": excluded,
        "feasible_count": count,
        "search_limited": limited,
        "optimality_proven": not limited,
        "ranking": ["participant_coverage", "monthly_rent", "deposit"],
        "reserves_inventory": False,
        "currency": "EGP",
        "price_period": "monthly",
    }
