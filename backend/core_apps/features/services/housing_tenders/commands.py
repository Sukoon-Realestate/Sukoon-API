from ..planning_parts.districts import district_matches

"""Transaction-owned tender commands. A package is a proposal, never a reservation."""

from collections import Counter
from datetime import timedelta
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.exceptions import PermissionDenied, ValidationError
from ...advanced_tender_models import (
    HousingTender,
    TenderParticipantRequirement,
    TenderDemandSnapshot,
    OwnerBid,
    TenderBidLine,
    PackageCandidate,
    PackageConsent,
)
from ...planning_models import HousingGroup, HousingRequest, HousingOffer
from ..planning import check_revision, civil_date, selection, offer_money, text_field
from ..rental_phase2 import RentalConflict
from ..rental_phase2_parts.remember_mutation import fingerprint
from ..rental_lifecycle.inventory import unit_keys, assert_available
from .access import admin, member, current, tender_actions
from .projections import latest_requirements
from .pricing import integer, validate_tiers, quote_allocations


def require_action(user, tender, action):
    if action not in tender_actions(user, tender):
        raise PermissionDenied(
            {
                "code": "action_unavailable",
                "message": "Refresh the current tender and permissions.",
            }
        )


def timestamp(value, name):
    parsed = parse_datetime(value) if isinstance(value, str) else None
    if (
        parsed is None
        or timezone.is_naive(parsed)
        or not timezone.now() < parsed <= timezone.now() + timedelta(days=30)
    ):
        raise ValidationError(
            {name: "Use a future timezone-aware time within 30 days."}
        )
    return parsed


def dates(data):
    start = civil_date(data.get("start_on"), "start_on", future=True)
    end = civil_date(data.get("end_on"), "end_on")
    if not 1 <= (end - start).days <= 366:
        raise ValidationError(
            {"end_on": "Use an exclusive end date within one year of arrival."}
        )
    return start, end


def source(user, data):
    group = get_object_or_404(
        HousingGroup.objects.select_for_update(),
        id=data.get("group_id"),
        status="active",
    )
    if not group.memberships.filter(user=user, status="active", role="admin").exists():
        raise PermissionDenied(
            "Only the current group coordinator can create a tender."
        )
    demand = get_object_or_404(
        HousingRequest.objects.select_for_update(), id=data.get("request_id")
    )
    if demand.user_id != user.pk or (
        demand.academic_plan_id and demand.academic_plan.group_id != group.pk
    ):
        raise PermissionDenied("Use your authorized request for this group.")
    if demand.status != "published" or demand.expires_at <= timezone.now():
        raise RentalConflict(
            "Publish a current housing request first.", code="source_changed"
        )
    check_revision(group.roster_revision, data.get("roster_revision"))
    check_revision(demand.revision, data.get("request_revision"))
    count = group.memberships.filter(status="active").count()
    if not 1 <= count <= 12:
        raise ValidationError(
            {"group_id": "This pilot supports at most 12 current group members."}
        )
    return group, demand


def create(user, data):
    if (
        data.get("execution_mode", "independent_participants")
        != "independent_participants"
    ):
        raise ValidationError({"execution_mode": "conditional_package is unsupported."})
    group, demand = source(user, data)
    return HousingTender.objects.create(
        group=group,
        request=demand,
        created_by=user,
        title=text_field(data, "title", required=True, limit=160),
        closes_at=timestamp(data.get("closes_at"), "closes_at"),
        roster_revision=group.roster_revision,
        request_revision=demand.revision,
        member_access={
            str(m.user.id): [str(m.id), m.joined_revision]
            for m in group.memberships.filter(status="active").select_related("user")
        },
    )


def respond(user, tender, data):
    require_action(user, tender, "requirements")
    if "participant_id" in data:
        raise ValidationError(
            {
                "participant_id": "The authenticated participant supplies only their own response."
            }
        )
    raw = data.get("requirement")
    keys = {
        "rental_scope",
        "start_on",
        "end_on",
        "rent_limit_minor",
        "deposit_limit_minor",
        "disclose",
        "independent_ack",
        "multi_property",
        "minimum_completion",
    }
    if not isinstance(raw, dict) or set(raw) != keys:
        raise ValidationError(
            {"requirement": "Supply the supported requirement fields only."}
        )
    if raw["rental_scope"] not in {"bed", "room", "entire_property"}:
        raise ValidationError(
            {"rental_scope": "Choose an exact supported accommodation scope."}
        )
    start, end = dates(raw)
    for flag in ["disclose", "independent_ack", "multi_property"]:
        if type(raw[flag]) is not bool:
            raise ValidationError({flag: "Use true or false."})
    integer(raw["rent_limit_minor"], "rent_limit_minor", minimum=1)
    integer(raw["deposit_limit_minor"], "deposit_limit_minor")
    integer(
        raw["minimum_completion"],
        "minimum_completion",
        minimum=1,
        maximum=tender.group.memberships.filter(status="active").count(),
    )
    prior = tender.requirements.filter(participant=user).order_by("-revision").first()
    TenderParticipantRequirement.objects.create(
        tender=tender,
        participant=user,
        revision=prior.revision + 1 if prior else 1,
        roster_revision=tender.roster_revision,
        request_revision=tender.request_revision,
        values={**raw, "start_on": str(start), "end_on": str(end)},
    )
    tender.revision += 1
    tender.save(update_fields=["revision", "updated_at"])
    return tender


def publish(user, tender):
    require_action(user, tender, "publish")
    latest = latest_requirements(tender)
    participants = sorted(
        str(x)
        for x in tender.group.memberships.filter(status="active").values_list(
            "user__id", flat=True
        )
    )
    requirements = []
    for participant in participants:
        row = latest.get(participant)
        if (
            not row
            or row.roster_revision != tender.roster_revision
            or row.request_revision != tender.request_revision
            or not row.values["disclose"]
            or not row.values["independent_ack"]
        ):
            raise RentalConflict(
                "Each current member must review and authorize their own requirements and reduced disclosure.",
                code="participant_consent_required",
            )
        dates(row.values)
        requirements.append(
            {
                "participant_id": participant,
                "requirement_revision": row.revision,
                **row.values,
            }
        )
    aggregates = Counter(
        (x["rental_scope"], x["start_on"], x["end_on"]) for x in requirements
    )
    owner_projection = {
        "participant_count": len(requirements),
        "city_id": tender.request.criteria.get("city_id", ""),
        "city_name": tender.request.criteria.get("city", {}).get("name", ""),
        "district_ids": tender.request.criteria.get("district_ids", []),
        "districts": tender.request.criteria.get("districts", []),
        "currency": "EGP",
        "price_period": "monthly",
        "requirements": [
            {"rental_scope": scope, "start_on": start, "end_on": end, "quantity": count}
            for (scope, start, end), count in sorted(aggregates.items())
        ],
    }
    snapshot = TenderDemandSnapshot.objects.create(
        tender=tender,
        revision=tender.revision + 1,
        roster_revision=tender.roster_revision,
        request_revision=tender.request_revision,
        private_requirements=requirements,
        owner_projection=owner_projection,
        digest=fingerprint(
            {
                "requirements": requirements,
                "roster_revision": tender.roster_revision,
                "request_revision": tender.request_revision,
            }
        ),
    )
    tender.active_snapshot = snapshot
    tender.status = "published"
    tender.revision += 1
    tender.save()
    return tender


def amend(user, tender, data):
    require_action(user, tender, "amend")
    if tender.request.status != "published" or tender.group.status != "active":
        raise RentalConflict(
            "Restore a current source group and request before amendment.",
            code="source_changed",
        )
    access = {
        str(m.user.id): [str(m.id), m.joined_revision]
        for m in tender.group.memberships.filter(status="active").select_related("user")
    }
    if access != tender.member_access:
        raise RentalConflict(
            "Group membership changed. Create a new tender so new members cannot inherit private history or consent.",
            code="membership_period_changed",
        )
    tender.status = "collecting_requirements"
    tender.active_snapshot = None
    tender.roster_revision = tender.group.roster_revision
    tender.request_revision = tender.request.revision
    if "closes_at" in data:
        tender.closes_at = timestamp(data["closes_at"], "closes_at")
    tender.revision += 1
    tender.save()
    return tender


def bid(request, tender):
    user, data = request.user, request.data
    supported = {
        "request_key",
        "expected_revision",
        "tender_revision",
        "snapshot_id",
        "selections",
        "start_on",
        "end_on",
        "expires_at",
        "minimum_quantity",
        "combines",
        "pricing_rule",
        "price_tiers",
        "currency",
        "price_period",
        "reserved_ack",
        "additional_charges",
        "supersedes_id",
        "supersedes_revision",
    }
    if set(data) - supported:
        raise ValidationError(
            {
                "bid": (
                    "This pilot does not support extra fees, inventory dependencies "
                    "or unstructured quote conditions."
                )
            }
        )
    require_action(user, tender, "bid")
    if data.get("snapshot_id") != str(tender.active_snapshot.id):
        raise RentalConflict(
            "Review the current published demand.", code="snapshot_changed"
        )
    check_revision(tender.revision, data.get("tender_revision"))
    previous = None
    if data.get("supersedes_id"):
        previous = get_object_or_404(
            OwnerBid.objects.select_for_update(),
            id=data["supersedes_id"],
            tender=tender,
            owner=user,
        )
        check_revision(previous.revision, data.get("supersedes_revision"))
        if (
            previous.status == "revised"
            or OwnerBid.objects.filter(supersedes=previous).exists()
        ):
            raise RentalConflict(
                "This quote already has a replacement.", code="quote_changed"
            )
    if (
        data.get("currency", "EGP") != "EGP"
        or data.get("price_period", "monthly") != "monthly"
        or data.get("additional_charges")
    ):
        raise ValidationError(
            {
                "pricing": "Only monthly EGP rent and explicit canonical deposits are supported."
            }
        )
    if data.get("reserved_ack") is not True:
        raise ValidationError({"reserved_ack": "A quote does not reserve inventory."})
    raw = data.get("selections")
    if (
        not isinstance(raw, list)
        or not 1 <= len(raw) <= 12
        or any(not isinstance(x, dict) for x in raw)
    ):
        raise ValidationError({"selections": "Quote 1 to 12 exact rental selections."})
    start, end = dates(data)
    expires = timestamp(data.get("expires_at"), "expires_at")
    minimum = integer(
        data.get("minimum_quantity", 1), "minimum_quantity", minimum=1, maximum=len(raw)
    )
    if type(data.get("combines", True)) is not bool:
        raise ValidationError({"combines": "Use a boolean."})
    lines, used = [], set()
    # A shared order prevents competing packages from locking properties differently.
    for value in sorted(raw, key=lambda x: str(x.get("property_id", ""))):
        prop, snapshot = selection(request, value, owned=True)
        if (
            not district_matches(prop, tender.request.criteria)
            or str(prop.city.id) != tender.request.criteria.get("city_id")
            or snapshot["terms"].get("price_period") != "monthly"
        ):
            raise ValidationError(
                {
                    "selections": "Inventory must match the demand city and monthly billing."
                }
            )
        rent, deposit = offer_money(snapshot)
        if deposit is None:
            raise ValidationError(
                {"selections": "The owner must configure an explicit deposit."}
            )
        keys = {f"{prop.id}/{key}" for key in unit_keys(prop, snapshot)}
        if keys & used:
            raise RentalConflict(
                "Bid lines overlap physical accommodation.", code="inventory_overlap"
            )
        used |= keys
        assert_available(prop, snapshot, start, end)
        lines.append((prop, snapshot, rent, deposit, sorted(keys)))
    rule = data.get("pricing_rule", "canonical")
    tiers = validate_tiers(
        rule, data.get("price_tiers", []), len(lines), [x[2] for x in lines]
    )
    item = OwnerBid.objects.create(
        tender=tender,
        snapshot=tender.active_snapshot,
        owner=user,
        expires_at=expires,
        start_on=start,
        end_on=end,
        minimum_quantity=minimum,
        combines=data.get("combines", True),
        pricing_rule=rule,
        price_tiers=tiers,
        supersedes=previous,
    )
    if previous:
        previous.status = "revised"
        previous.revision += 1
        previous.save(update_fields=["status", "revision", "updated_at"])
    for prop, snapshot, rent, deposit, keys in lines:
        # A tender quote is not eligible for ordinary request select-to-proceed.
        offer = HousingOffer.objects.create(
            request=tender.request,
            owner=user,
            property=prop,
            request_revision=tender.request_revision,
            selection=snapshot,
            rent_minor=rent,
            deposit_minor=deposit,
            price_period="monthly",
            status="tender_quote",
        )
        TenderBidLine.objects.create(bid=item, offer=offer, physical_keys=keys)
    return item


def validate_package(request, tender, allocations):
    if (
        not current(tender)
        or tender.status != "published"
        or not tender.active_snapshot
    ):
        raise RentalConflict(
            "The demand or group changed; create a new reviewed package.",
            code="snapshot_changed",
        )
    requirements = {
        x["participant_id"]: x for x in tender.active_snapshot.private_requirements
    }
    if not isinstance(allocations, list) or not 1 <= len(allocations) <= 12:
        raise ValidationError(
            {"allocations": "Provide 1 to 12 participant and bid-line assignments."}
        )
    people, lines, bids, line_ids = set(), [], {}, set()
    for raw in allocations:
        if (
            not isinstance(raw, dict)
            or not isinstance(raw.get("participant_id"), str)
            or not isinstance(raw.get("line_id"), str)
        ):
            raise ValidationError(
                {"allocations": "Each assignment needs participant_id and line_id."}
            )
        person = raw["participant_id"]
        if raw["line_id"] in line_ids:
            raise ValidationError(
                {
                    "allocations": "Each quoted accommodation unit can be allocated only once."
                }
            )
        line_ids.add(raw["line_id"])
        if person in people or person not in requirements:
            raise ValidationError(
                {
                    "allocations": "Allocate each current authorized participant at most once."
                }
            )
        people.add(person)
        line = get_object_or_404(
            TenderBidLine.objects.select_related("bid", "offer__property"),
            id=raw["line_id"],
            bid__tender=tender,
        )
        if (
            line.bid.status != "submitted"
            or line.bid.snapshot_id != tender.active_snapshot_id
            or line.bid.expires_at <= timezone.now()
        ):
            raise RentalConflict(
                "An owner quote expired, changed or was withdrawn.",
                code="quote_invalid",
            )
        if (
            str(line.offer.owner.id) != str(line.bid.owner.id)
            or line.offer.property.owner_id != line.bid.owner_id
        ):
            raise RentalConflict(
                "Current ownership authority changed.", code="owner_authority_changed"
            )
        req = requirements[person]
        start, end = dates(req)
        if (
            start < line.bid.start_on
            or end > line.bid.end_on
            or req["rental_scope"] != line.offer.selection.get("rental_scope")
        ):
            raise ValidationError(
                {
                    "allocations": "Accommodation scope and dates must satisfy each participant."
                }
            )
        bids.setdefault(line.bid_id, (line.bid, []))[1].append(line)
        lines.append((person, req, line, start, end))
    if len(bids) > 1 and any(not b.combines for b, _ in bids.values()):
        raise ValidationError(
            {"allocations": "A selected owner quote cannot be combined."}
        )
    costs = {}
    from core_apps.properties.models import Property

    # Match the shared executor's global physical-root ordering before checking
    # selections. Two packages can refer to the same roots in different bid order.
    list(
        Property.objects.select_for_update()
        .filter(pk__in={line.offer.property_id for _, _, line, _, _ in lines})
        .order_by("pk")
    )
    for b, chosen in bids.values():
        costs.update(quote_allocations(b, chosen))
    used, result, property_ids = [], [], set()
    for person, req, line, start, end in sorted(
        lines, key=lambda x: str(x[2].offer.property.id)
    ):
        prop, snapshot = selection(request, line.offer.selection)
        if (
            prop.owner_id != line.bid.owner_id
            or not prop.is_ownership_verified
            or prop.retired_at
        ):
            raise RentalConflict(
                "Current ownership authority changed.", code="owner_authority_changed"
            )
        rent, deposit = offer_money(snapshot)
        if rent != line.offer.rent_minor or deposit != line.offer.deposit_minor:
            raise RentalConflict(
                "The canonical offer terms changed.", code="offer_changed"
            )
        keys = {f"{prop.id}/{key}" for key in unit_keys(prop, snapshot)}
        if sorted(keys) != line.physical_keys:
            raise RentalConflict(
                "The physical inventory map changed.", code="inventory_changed"
            )
        if any(
            keys & previous and start < until and since < end
            for previous, since, until in used
        ):
            raise RentalConflict(
                "Allocations overlap physical accommodation.", code="inventory_overlap"
            )
        used.append((keys, start, end))
        assert_available(prop, snapshot, start, end)
        from core_apps.users.models import User
        from ..student_housing.policies import validate_occupants

        occupant = get_object_or_404(User, id=person, is_active=True, is_verified=True)
        validate_occupants(prop, snapshot, [occupant], start, end, occupant_count=1)
        price = costs[str(line.id)]
        if (
            price > req["rent_limit_minor"]
            or deposit is None
            or deposit > req["deposit_limit_minor"]
        ):
            raise ValidationError(
                {
                    "allocations": "An allocation exceeds an individual rent or deposit limit."
                }
            )
        if len(people) < req["minimum_completion"]:
            raise ValidationError(
                {
                    "allocations": "The proposed completion is below an individual requirement."
                }
            )
        property_ids.add(str(prop.id))
        result.append(
            {
                "participant_id": person,
                "line_id": str(line.id),
                "bid_id": str(line.bid.id),
                "bid_revision": line.bid.revision,
                "housing_offer_id": str(line.offer.id),
                "selection": snapshot,
                "rent_minor": price,
                "deposit_minor": deposit,
                "start_on": str(start),
                "end_on": str(end),
                "pricing_rule": line.bid.pricing_rule,
                "canonical_terms_match": price == rent,
            }
        )
    if len(property_ids) > 1 and any(
        not req["multi_property"] for _, req, _, _, _ in lines
    ):
        raise ValidationError(
            {
                "allocations": "A participant has not authorized a multi-property package."
            }
        )
    return sorted(result, key=lambda x: x["participant_id"]), sorted(
        set(requirements) - people
    )


def package(request, tender):
    require_action(request.user, tender, "package-runs")
    if request.data.get("execution_mode") != "independent_participants":
        raise ValidationError(
            {
                "execution_mode": "conditional_package is unsupported; no commitments were made."
            }
        )
    if request.data.get("snapshot_id") != str(tender.active_snapshot.id):
        raise RentalConflict("The published snapshot changed.", code="snapshot_changed")
    check_revision(tender.revision, request.data.get("tender_revision"))
    allocations, missing = validate_package(
        request, tender, request.data.get("allocations")
    )
    return PackageCandidate.objects.create(
        tender=tender,
        snapshot=tender.active_snapshot,
        allocations=allocations,
        unallocated_ids=missing,
        digest=fingerprint(
            {
                "snapshot": tender.active_snapshot.digest,
                "allocations": allocations,
                "mode": "independent_participants",
            }
        ),
        total_rent_minor=sum(x["rent_minor"] for x in allocations),
        total_deposit_minor=sum(x["deposit_minor"] for x in allocations),
    )


def consent(request, item):
    data = request.data
    if "participant_id" in data:
        raise ValidationError(
            {"participant_id": "Package consent cannot be supplied for another person."}
        )
    if data.get("digest") != item.digest or data.get("decision") not in {
        "accept",
        "decline",
    }:
        raise ValidationError(
            {"digest": "Review this exact package and choose accept or decline."}
        )
    if not any(x["participant_id"] == str(request.user.id) for x in item.allocations):
        raise PermissionDenied(
            "Only an allocated participant can supply their own decision."
        )
    if item.tender.active_snapshot_id != item.snapshot_id:
        raise RentalConflict(
            "The demand changed; review a new package.", code="snapshot_changed"
        )
    if data["decision"] == "accept":
        if data.get("independent_ack") is not True:
            raise ValidationError(
                {
                    "independent_ack": (
                        "Acknowledge that completed individual leases can remain valid "
                        "when others decline."
                    )
                }
            )
        fresh, _ = validate_package(request, item.tender, item.allocations)
        if fresh != item.allocations:
            raise RentalConflict(
                "The exact allocation terms changed.", code="package_changed"
            )
        if item.consents.filter(decision="decline").exists():
            raise RentalConflict(
                "A participant declined. Rebuild and review the affected package.",
                code="package_changed",
            )
    PackageConsent.objects.update_or_create(
        package=item,
        participant=request.user,
        defaults={"package_digest": item.digest, "decision": data["decision"]},
    )
    item.revision += 1
    item.save(update_fields=["revision", "updated_at"])
    return item
