import copy
import uuid
from datetime import timedelta
import pytest
from django.test import override_settings
from django.utils import timezone
from core_apps.features.models import Lease, RentalInventoryDayLock, RentInvoice
from core_apps.features.planning_models import TenancyTransition
from core_apps.features.transition_network_models import (
    MoveIntent,
    TransitionCandidate,
    TransitionMatchRun,
)
from core_apps.features.services.transition_network.jobs import process_transition_match
from core_apps.features.services.tenancy_invitations import resolve_offer_snapshot
from core_apps.properties.models import Property
from . import test_rental_phase2 as rental_fixtures
from .test_rental_phase2 import authenticated

rental_participants = rental_fixtures.rental_participants

API = "/api/v1/features/v1/"
pytestmark = pytest.mark.django_db


def body(revision=0, **kwargs):
    return {"request_key": str(uuid.uuid4()), "expected_revision": revision, **kwargs}


def post(user, path, payload, expected=200):
    response = authenticated(user).post(API + path, payload, format="json")
    assert response.status_code == expected, response.data
    return response.data


@pytest.fixture
def moves(rental_participants, settings):
    settings.ADVANCED_HOUSING_ENABLED_SERVICES = ["housing_transition_planning"]
    owner, first, second, prop, offer_id = rental_participants
    prop.rental_inventory["offers"][0]["terms"].update(
        deposit="none", rental_period=1, suitable_for="all"
    )
    prop.save()
    other = Property.objects.create(
        owner=owner,
        title="Second authorized home",
        price=prop.price,
        property_type=prop.property_type,
        governorate=prop.governorate,
        city=prop.city,
        district="District",
        status="verified",
        is_verified=True,
        is_ownership_verified=True,
        rental_inventory=copy.deepcopy(prop.rental_inventory),
    )
    finish = timezone.localdate() + timedelta(days=10)
    result = []
    for user, property_obj in [(first, prop), (second, other)]:
        _, snapshot = resolve_offer_snapshot(property_obj, offer_id, 2)
        lease = Lease.objects.create(
            owner=owner,
            tenant=user,
            property=property_obj,
            template_id="test",
            template_version="1",
            start_date=finish - timedelta(days=60),
            end_date=finish,
            rent_amount_minor=1000000,
            status="active",
            occupancy_status="occupied",
            offer_id=offer_id,
            offer_snapshot=snapshot,
            terms={"occupants": 1},
            legacy_read_only=False,
        )
        source = TenancyTransition.objects.create(
            lease=lease,
            author=user,
            kind="replacement",
            requested_on=finish,
            reason="Authorized move plan",
            availability_approved=True,
        )
        criteria = {
            "city_id": str(prop.city.id),
            "rental_scope": "entire_property",
            "property_type": "",
            "budget_min": {"amount_minor": 0, "currency": "EGP", "exponent": 2},
            "budget_max": {"amount_minor": 1500000, "currency": "EGP", "exponent": 2},
            "price_period": "monthly",
            "start_on": str(finish + timedelta(days=1)),
            "end_on": str(finish + timedelta(days=35)),
            "people": 1,
        }
        payload = body(
            lease_id=str(lease.id),
            source_transition_id=str(source.id),
            criteria=criteria,
            max_deposit_minor=1000000,
            max_gap_days=1,
            turnover_days=1,
        )
        created = post(user, "move-intents/", payload, 201)["resource"]
        result.append((user, lease, source, created, payload))
    return owner, result


def publish(row):
    user, _, _, item, _ = row
    return post(
        user,
        f"move-intents/{item['id']}/publish/",
        body(item["revision"], matching_consent=True),
    )["resource"]


def matching(moves):
    _, rows = moves
    for row in rows:
        publish(row)
    intent = MoveIntent.objects.get(id=rows[0][3]["id"])
    payload = body(intent.revision)
    run = post(rows[0][0], f"move-intents/{intent.id}/match-runs/", payload)["resource"]
    process_transition_match(run["id"])
    return rows, run


def test_move_create_replay_privacy_and_operation_recovery(moves):
    owner, rows = moves
    user, lease, source, item, payload = rows[0]
    replay = post(user, "move-intents/", payload, 201)
    assert replay["resource"]["id"] == item["id"]
    receipt = authenticated(user).get(
        API + f"rental-operations/{payload['request_key']}/",
        {"subject_id": str(lease.id)},
    )
    assert receipt.status_code == 200 and receipt.data["status"] == "confirmed"
    assert (
        authenticated(owner).get(API + f"move-intents/{item['id']}/").status_code == 404
    )
    assert (
        authenticated(rows[1][0]).get(API + f"move-intents/{item['id']}/").status_code
        == 404
    )
    post(user, "move-intents/", {**payload, "max_gap_days": 2}, 409)
    assert MoveIntent.objects.count() == 2


def test_move_matching_qualified_and_nonbinding_with_private_projection(moves):
    before = (
        Lease.objects.count(),
        RentalInventoryDayLock.objects.count(),
        RentInvoice.objects.count(),
    )
    rows, run = matching(moves)
    candidate = TransitionCandidate.objects.get(run__id=run["id"])
    response = authenticated(rows[0][0]).get(
        API + f"transition-candidates/{candidate.id}/"
    )
    assert response.status_code == 200
    data = response.data
    assert data["result_status"] == "unknown"  # physical releases remain unconfirmed
    assert data["participant_count"] == 2 and data["gap_days"] == 1
    assert data["selection"]["property_id"] == str(rows[1][1].property.id)
    assert data["execution_available"] is False and data["inventory_reserved"] is False
    assert (
        not {"participants", "criteria", "max_deposit_minor", "legs", "user_id"}
        & data.keys()
    )
    assert before == (
        Lease.objects.count(),
        RentalInventoryDayLock.objects.count(),
        RentInvoice.objects.count(),
    )
    process_transition_match(run["id"])
    assert TransitionCandidate.objects.filter(run__id=run["id"]).count() == 1


@pytest.mark.parametrize("change", ["gap", "scope", "budget"])
def test_move_hard_constraints_never_relaxed(moves, change):
    item = MoveIntent.objects.first()
    if change == "gap":
        item.max_gap_days = 0
    elif change == "scope":
        item.criteria["rental_scope"] = "room"
    else:
        item.criteria["budget_max"]["amount_minor"] = 1
    item.save()
    rows, run = matching(moves)
    assert not TransitionCandidate.objects.filter(run__id=run["id"]).exists()
    assert TransitionMatchRun.objects.get(id=run["id"]).result_status == "infeasible"


def test_move_interest_is_exact_individual_and_stales_on_quote_change(moves):
    rows, run = matching(moves)
    candidate = TransitionCandidate.objects.get(run__id=run["id"])
    payload = body(
        candidate.revision,
        snapshot_digest=candidate.snapshot_digest,
        decision="interested",
    )
    post(
        rows[0][0],
        f"transition-candidates/{candidate.id}/interest/",
        {**payload, "participant_id": str(rows[1][0].id)},
        400,
    )
    accepted = post(
        rows[0][0], f"transition-candidates/{candidate.id}/interest/", payload
    )
    assert (
        post(rows[0][0], f"transition-candidates/{candidate.id}/interest/", payload)
        == accepted
    )
    assert candidate.participants.get(user=rows[1][0]).decision == "pending"
    prop = rows[1][1].property
    prop.rental_inventory["offers"][0]["revision"] += 1
    prop.rental_inventory["offers"][0]["terms"]["price"] = "11000"
    prop.save()
    data = (
        authenticated(rows[0][0])
        .get(API + f"transition-candidates/{candidate.id}/")
        .data
    )
    assert data["result_status"] == "stale" and data["allowed_actions"] == []
    post(
        rows[1][0],
        f"transition-candidates/{candidate.id}/interest/",
        body(2, snapshot_digest=candidate.snapshot_digest, decision="interested"),
        409,
    )


def test_move_owner_permission_withdrawal_and_disabled_history(moves):
    owner, rows = moves
    rows[0][2].availability_approved = False
    rows[0][2].save()
    item = rows[0][3]
    post(
        rows[0][0],
        f"move-intents/{item['id']}/publish/",
        body(1, matching_consent=True),
        409,
    )
    with override_settings(ADVANCED_HOUSING_ENABLED_SERVICES=[]):
        assert (
            authenticated(rows[0][0])
            .get(API + f"move-intents/{item['id']}/")
            .status_code
            == 200
        )
        post(
            rows[0][0],
            f"move-intents/{item['id']}/publish/",
            body(1, matching_consent=True),
            403,
        )


def test_move_execution_never_enabled_by_client_request(moves):
    rows, run = matching(moves)
    candidate = TransitionCandidate.objects.get(run__id=run["id"])
    post(rows[0][0], f"transition-plans/{candidate.id}/prepare/", body(1), 403)
    grant = authenticated(rows[0][0]).get(
        API + "planning-capabilities/",
        {
            "capability": "housing_transition_execution",
            "action": "prepare",
            "subject_id": str(candidate.id),
        },
    )
    assert grant.status_code == 200 and grant.data["allowed_actions"] == []


def test_move_minimum_term_is_checked_without_relaxing_dates(moves):
    _, rows = moves
    item = MoveIntent.objects.get(id=rows[0][3]["id"])
    item.criteria["end_on"] = str(rows[0][2].requested_on + timedelta(days=5))
    item.save()
    _, run = matching(moves)
    assert not TransitionCandidate.objects.filter(run__id=run["id"]).exists()
    assert TransitionMatchRun.objects.get(id=run["id"]).result_status == "infeasible"


@pytest.mark.parametrize("terms", [{"occupants": 2}, {}, {"occupants": True}])
def test_move_source_occupant_rights_require_explicit_single_person(moves, terms):
    _, rows = moves
    user, lease, source, item, payload = rows[0]
    lease.terms = terms
    lease.save(update_fields=["terms"])
    response = authenticated(user).post(
        API + f"move-intents/{item['id']}/publish/",
        body(item["revision"], matching_consent=True),
        format="json",
    )
    assert response.status_code == 409
    assert response["X-App-Error-Code"] == "source_occupants_review_required"
    intent = MoveIntent.objects.get(id=item["id"])
    assert intent.status == "draft" and intent.matching_consent is False


def test_move_occupant_change_revokes_candidate_and_interest(moves):
    rows, run = matching(moves)
    candidate = TransitionCandidate.objects.get(run__id=run["id"])
    lease = rows[1][1]
    lease.terms = {"occupants": 2}
    lease.save(update_fields=["terms"])
    response = authenticated(rows[0][0]).get(
        API + f"transition-candidates/{candidate.id}/"
    )
    assert response.data["result_status"] == "stale"
    assert response.data["allowed_actions"] == []
    post(
        rows[0][0],
        f"transition-candidates/{candidate.id}/interest/",
        body(
            candidate.revision,
            snapshot_digest=candidate.snapshot_digest,
            decision="interested",
        ),
        409,
    )


def test_move_missing_worker_and_disabled_capability_preserve_queued_work(moves):
    _, rows = moves
    for row in rows:
        publish(row)
    intent = MoveIntent.objects.get(id=rows[0][3]["id"])
    run = post(
        rows[0][0], f"move-intents/{intent.id}/match-runs/", body(intent.revision)
    )["resource"]
    with override_settings(ADVANCED_HOUSING_ENABLED_SERVICES=[]):
        assert process_transition_match(run["id"]) == "paused"
        assert TransitionMatchRun.objects.get(id=run["id"]).status == "queued"
        response = authenticated(rows[0][0]).get(
            API + f'transition-match-runs/{run["id"]}/'
        )
        assert (
            response.status_code == 200 and response.data["result_status"] == "unknown"
        )
    assert process_transition_match(run["id"]) == "result_ready"
    assert TransitionCandidate.objects.filter(run__id=run["id"]).count() == 1


def test_move_origin_replacement_approval_change_invalidates_proposal(moves):
    rows, run = matching(moves)
    candidate = TransitionCandidate.objects.get(run__id=run["id"])
    source = rows[1][2]
    source.availability_approved = False
    source.save()
    result = authenticated(rows[0][0]).get(
        API + f"transition-candidates/{candidate.id}/"
    )
    assert result.data["result_status"] == "stale"
    assert result.data["allowed_actions"] == []


@pytest.mark.django_db(transaction=True)
def test_move_duplicate_workers_create_only_one_proposal(moves, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from django.db import connection, close_old_connections

    if connection.vendor != "postgresql":
        pytest.skip("Row locking requires PostgreSQL")
    monkeypatch.setattr(
        "core_apps.features.services.transition_network.jobs.enqueue", lambda _: True
    )
    _, rows = moves
    for row in rows:
        publish(row)
    intent = MoveIntent.objects.get(id=rows[0][3]["id"])
    run = post(
        rows[0][0], f"move-intents/{intent.id}/match-runs/", body(intent.revision)
    )["resource"]

    def worker(_):
        close_old_connections()
        try:
            return process_transition_match(run["id"])
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(worker, range(2))) == ["result_ready", "result_ready"]
    assert TransitionCandidate.objects.filter(run__id=run["id"]).count() == 1
