"""Real source identities with explicitly simulated financial providers."""

import copy
from django.test import override_settings
import pytest
from core_apps.features.models import Lease, OwnerPaymentProfile, RentalInventoryDayLock
from core_apps.features.transition_network_models import (
    TransitionCandidate,
    TransitionMatchRun,
)
from core_apps.properties.models import Property
from .test_transition_network import (
    rental_participants,
    matching,
    post,
    body,
    API,
)
from . import test_transition_network as test_transition_network_fixtures
from .test_rental_phase2 import authenticated

moves = test_transition_network_fixtures.moves

pytestmark = pytest.mark.django_db
ENABLED = [
    "housing_transition_planning",
    "housing_transition_execution",
    "conditional_group_execution",
]


def vacant_property(moves):
    owner, rows = moves
    prop = rows[0][1].property
    return Property.objects.create(
        owner=owner,
        title="Explicitly vacant endpoint",
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


def act(user, plan, action, expected=200, **data):
    if action == "advance":
        leg = next(item for item in plan["legs"] if item["id"] == data["leg_id"])
        data = {
            "document_hash": leg["document_hash"],
            "invoice_id": leg["invoice_id"],
            "invoice_revision": leg["invoice_revision"],
            "amount_minor": leg["first_invoice_minor"],
            **data,
        }
    result = post(
        user,
        f"advanced-executions/{plan['id']}/{action}/",
        body(plan["revision"], digest=plan["digest"], **data),
        expected,
    )
    return result.get("resource")


def create_plan(rows, candidate):
    for row in rows:
        candidate.refresh_from_db()
        post(
            row[0],
            f"transition-candidates/{candidate.id}/interest/",
            body(
                candidate.revision,
                snapshot_digest=candidate.snapshot_digest,
                decision="interested",
            ),
        )
    candidate.refresh_from_db()
    result = post(
        rows[0][0],
        f"transition-plans/{candidate.id}/prepare/",
        body(candidate.revision, snapshot_digest=candidate.snapshot_digest),
    )
    return result["resource"]


def test_open_chain_uses_actual_vacancy_and_stales_when_source_changes(moves):
    vacancy = vacant_property(moves)
    rows, run = matching(moves)
    candidate = TransitionCandidate.objects.filter(
        run__id=run["id"], snapshot__kind="open_chain", snapshot__objectives__moves=1
    ).first()
    assert candidate is not None
    data = (
        authenticated(rows[0][0])
        .get(API + f"transition-candidates/{candidate.id}/")
        .data
    )
    assert data["kind"] == "open_chain" and data["result_status"] == "unknown"
    assert data["selection"]["property_id"] == str(vacancy.id)
    assert "source_manifest" not in data and "objectives" not in data
    assert not RentalInventoryDayLock.objects.exists()
    source = rows[0][2]
    source.availability_approved = False
    source.save()
    data = (
        authenticated(rows[0][0])
        .get(API + f"transition-candidates/{candidate.id}/")
        .data
    )
    assert data["result_status"] == "stale" and not data["allowed_actions"]


def test_no_false_infeasible_when_matching_budget_exhausted(moves, monkeypatch):
    monkeypatch.setattr(
        "core_apps.features.services.transition_network.solver.MAX_PROPOSALS", 0
    )
    _, run = matching(moves)
    saved = TransitionMatchRun.objects.get(id=run["id"])
    assert saved.result_status == "unknown" and saved.pool_limited


def test_owner_and_every_participant_consent_do_not_fabricate_physical_return(moves):
    owner, _ = moves
    rows, run = matching(moves)
    candidate = TransitionCandidate.objects.get(run__id=run["id"])
    with override_settings(
        ADVANCED_HOUSING_PROVIDER_MODE="mock", ADVANCED_HOUSING_ENABLED_SERVICES=ENABLED
    ):
        plan = create_plan(rows, candidate)
        for actor in [owner, *(row[0] for row in rows)]:
            plan = act(
                actor,
                plan,
                "consents",
                decision="accept",
                policy_version=plan["policy_version"],
            )
        assert plan["state"] == "ready"
        count = Lease.objects.count()
        response = authenticated(rows[0][0]).post(
            API + f"advanced-executions/{plan['id']}/prepare/",
            body(plan["revision"], digest=plan["digest"]),
            format="json",
        )
        assert response.status_code == 409
        assert response["X-App-Error-Code"] == "physical_release_requires_confirmation"
        assert (
            Lease.objects.count() == count
            and not RentalInventoryDayLock.objects.exists()
        )


def test_linked_mock_execution_uses_own_leases_and_waits_for_handover(moves):
    owner, rows = moves
    for row in rows:
        lease = row[1]
        lease.status, lease.occupancy_status = "ended", "returned"
        lease.save()
    rows, run = matching(moves)
    candidate = TransitionCandidate.objects.filter(
        run__id=run["id"], snapshot__kind="cycle"
    ).get()
    with override_settings(
        ADVANCED_HOUSING_PROVIDER_MODE="mock", ADVANCED_HOUSING_ENABLED_SERVICES=ENABLED
    ):
        plan = create_plan(rows, candidate)
        for actor in [owner, *(row[0] for row in rows)]:
            plan = act(
                actor,
                plan,
                "consents",
                decision="accept",
                policy_version=plan["policy_version"],
            )
        OwnerPaymentProfile.objects.update_or_create(
            owner=owner,
            defaults={
                "status": "ready",
                "payout_ready": True,
                "provider": "fake",
                "provider_account_id": "move-owner",
                "accepted_policy_versions": ["rental-policy-v1"],
            },
        )
        plan = act(rows[0][0], plan, "prepare")
        assert plan["state"] == "prepared"
        assert len(plan["legs"]) == 1  # caller projection never includes peers
        owner_plan = (
            authenticated(owner).get(API + f"advanced-executions/{plan['id']}/").data
        )
        assert len(owner_plan["legs"]) == 2
        plan = owner_plan
        for leg in owner_plan["legs"]:
            plan = act(owner, plan, "advance", leg_id=leg["id"], step="sign")
        for row in rows:
            own = (
                authenticated(row[0])
                .get(API + f"advanced-executions/{plan['id']}/")
                .data
            )
            assert own["legs"][0]["outgoing_lease_id"] == str(row[1].id)
            plan = act(row[0], own, "advance", leg_id=own["legs"][0]["id"], step="sign")
        for row in rows:
            own = (
                authenticated(row[0])
                .get(API + f"advanced-executions/{plan['id']}/")
                .data
            )
            plan = act(row[0], own, "advance", leg_id=own["legs"][0]["id"], step="pay")
        assert plan["state"] == "awaiting_handover"
        assert (
            Lease.objects.filter(
                status="active", occupancy_status="not_started"
            ).count()
            == 2
        )
        # The existing possession workflow is independently authoritative.
        Lease.objects.filter(status="active").update(occupancy_status="occupied")
        plan = act(rows[0][0], plan, "reconcile")
        assert plan["state"] == "completed"
