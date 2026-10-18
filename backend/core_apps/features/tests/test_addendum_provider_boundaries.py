"""Synthetic provider-boundary checks, never evidence of a live integration."""

from datetime import timedelta
from types import SimpleNamespace
import pytest
from django.utils import timezone
from django.core.cache import cache
from rest_framework.exceptions import ValidationError
from core_apps.features.models import (
    PolicyDecision,
    RentalOperationalCase,
    LedgerTransaction,
)
from core_apps.features.asset_passport_models import AssetItem
from core_apps.features.services.rental_phase2 import RentalConflict
from core_apps.features.services.purchase_routing import (
    routing,
    require_legacy_checkout,
)
from core_apps.features.services.housing_scenarios import routes
from core_apps.features.services.asset_passport import analysis, investigations
from core_apps.features.tests.test_rental_phase2 import rental_participants
from core_apps.features.tests.test_advanced_company_passport import (
    passport,
    advanced_enabled,
)
from core_apps.features.tests.test_advanced_company_passport_v2 import add_observations

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("purpose", ["subscription", "advertising", "unknown-product"])
def test_digital_or_unknown_cannot_use_rental_checkout(purpose, settings):
    settings.RENTAL_RUNTIME_ENVIRONMENT = "production"
    settings.RENTAL_FAKE_PROVIDER_ALLOWED = False
    assert not routing(purpose, "ios")["enabled"]
    assert not routing(purpose, "android")["enabled"]
    with pytest.raises(RentalConflict):
        require_legacy_checkout(purpose)
    assert not LedgerTransaction.objects.exists()


def test_physical_route_is_distinct_but_not_claimed_ready():
    for purpose in ["rent", "deposit", "maintenance"]:
        value = routing(purpose, "ios")
        assert value["route"] == "egyptian_psp" and not value["enabled"]
    assert routing("subscription", "ios")["required_route"] == "storekit"
    assert routing("subscription", "android")["required_route"] == "play_billing"
    assert not routing("subscription", "web")["external_checkout_allowed"]


def route_args():
    return {
        "latitude": 30.1,
        "longitude": 31.1,
        "mode": "driving",
        "departure_at": (timezone.now() + timedelta(days=1)).isoformat(),
    }


def route_policy(user, settings):
    settings.PLANNING_ROUTES_API_KEY = "synthetic-never-sent"
    cache.clear()
    return PolicyDecision.objects.create(
        evidence_requirements={"fixture": "synthetic only"},
        actions_and_consequences={"fixture": "no live consequence"},
        historical_treatment="No live applicability",
        audit_reason="Isolated test fixture",
        disclosure="Synthetic test only",
        code="D22",
        version="SYNTHETIC-ROUTES-ONLY",
        status="approved",
        owner="local-test",
        approver=user,
        source="synthetic-test",
        evidence_reference="unit-test-only",
        scope=["routes.estimate"],
        effective_at=timezone.now() - timedelta(seconds=1),
        rules={
            "route_validity_seconds": 180,
            "storage_policy_reference": "synthetic-only",
        },
    )


def test_route_missing_policy_coordinates_and_departure_are_unknown(user):
    prop = SimpleNamespace(latitude=30.0, longitude=31.0)
    assert (
        routes.estimate(user, prop, route_args())["unknown_reason"]
        == "route_provider_policy_required"
    )
    assert (
        routes.estimate(user, prop, {**route_args(), "departure_at": ""})[
            "unknown_reason"
        ]
        == "departure_time_required"
    )
    assert (
        routes.estimate(
            user, SimpleNamespace(latitude=None, longitude=None), route_args()
        )["unknown_reason"]
        == "coordinates_unavailable"
    )


def test_directional_route_frozen_expiry_and_source_change(user, settings, monkeypatch):
    route_policy(user, settings)
    calls = []
    monkeypatch.setattr(routes, "provider_budget", lambda *_: None)

    def provider(origins, query):
        calls.append((origins, query))
        return [
            {
                "status": "ok",
                "duration_seconds": 1201,
                "distance_meters": 9100,
                "timing_fallback": False,
            }
        ]

    monkeypatch.setattr(routes, "route_matrix", provider)
    prop, assumptions = SimpleNamespace(latitude=30.0, longitude=31.0), route_args()
    result = routes.estimate(user, prop, assumptions)
    assert (
        result["minutes"] == 21
        and result["distance_meters"] == 9100
        and not result["simulated"]
    )
    assert result["origin"] == {"latitude": 30.0, "longitude": 31.0} and result[
        "destination"
    ] == {"latitude": 30.1, "longitude": 31.1}
    assert (
        routes.estimate(user, prop, assumptions, frozen=result) == result
        and len(calls) == 1
    )
    with pytest.raises(RentalConflict):
        routes.estimate(user, prop, {**assumptions, "mode": "walking"}, frozen=result)
    with pytest.raises(RentalConflict):
        routes.estimate(
            user,
            prop,
            assumptions,
            frozen={
                **result,
                "expires_at": (timezone.now() - timedelta(seconds=1)).isoformat(),
            },
        )


@pytest.mark.parametrize(
    "row",
    [
        {"status": "unknown"},
        {
            "status": "ok",
            "duration_seconds": 100,
            "distance_meters": 10,
            "timing_fallback": True,
        },
    ],
)
def test_no_route_or_fallback_is_never_zero_minutes(user, settings, monkeypatch, row):
    route_policy(user, settings)
    monkeypatch.setattr(routes, "provider_budget", lambda *_: None)
    monkeypatch.setattr(routes, "route_matrix", lambda *_: [row])
    result = routes.estimate(
        user, SimpleNamespace(latitude=30.0, longitude=31.0), route_args()
    )
    assert result["minutes"] is None and result["status"] == "unknown"


def test_manual_visual_review_needs_exact_safe_images_and_human_attestation(
    passport, settings
):
    settings.ADVANCED_HOUSING_PROVIDER_MODE = "manual"
    owner, _, _, _, _, _, asset = passport
    observations = add_observations(passport)
    job = analysis.create(
        owner,
        AssetItem.objects.get(id=asset["id"]),
        {"observation_ids": [str(row.id) for row in observations]},
    )
    assert job.provider == "manual_visual_review" and job.state == "ready_for_review"
    finding = job.suggestions.get()
    data = {
        "decision": "accepted_as_observation",
        "reason": "Synthetic human observation",
        "human_inspection_attested": True,
        "comparison_quality": "comparable",
        "identity_confirmed": True,
        "inspected_evidence_ids": [
            str(media.id) for row in observations for media in row.evidence.all()
        ],
    }
    with pytest.raises(ValidationError):
        analysis.review(owner, finding, {**data, "human_inspection_attested": False})
    with pytest.raises(ValidationError):
        analysis.review(owner, finding, {**data, "inspected_evidence_ids": []})
    with pytest.raises(ValidationError):
        analysis.review(owner, finding, {**data, "inspected_evidence_ids": [{}]})
    with pytest.raises(ValidationError):
        analysis.review(owner, finding, {**data, "comparison_quality": "low_light"})
    settings.ADVANCED_HOUSING_PROVIDER_MODE = "disabled"
    finding = analysis.review(owner, finding, data)
    assert (
        not finding.output["liability_determined"]
        and not finding.output["pixels_analyzed_by_model"]
    )
    with pytest.raises(RentalConflict):
        analysis.review(owner, finding, data)
    assert not LedgerTransaction.objects.exists()


def test_manual_warranty_is_one_internal_case_not_external_acceptance(
    passport, settings
):
    settings.ADVANCED_HOUSING_PROVIDER_MODE = "manual"
    owner, _, _, _, _, report, asset = passport
    row = investigations.warranty(
        owner,
        AssetItem.objects.get(id=asset["id"]),
        {
            "source_kind": "condition_report",
            "source_id": str(report.id),
            "source_revision": report.revision,
            "issuer": "Synthetic recorded issuer",
            "reference": "synthetic-reference",
            "starts_on": str(report.inspected_on),
            "ends_on_exclusive": str(report.inspected_on + timedelta(days=365)),
        },
    )
    result = investigations.claim(
        owner, row, {"reason": "Review the recorded warranty"}
    )
    assert result.service_case_id and RentalOperationalCase.objects.count() == 1
    assert (
        result.status == "manual_review_pending"
        and not result.provider_result["externally_submitted"]
        and not result.provider_result["acknowledged"]
    )
    with pytest.raises(RentalConflict):
        investigations.claim(owner, row, {"reason": "Do not duplicate"})
    assert (
        RentalOperationalCase.objects.count() == 1
        and not LedgerTransaction.objects.exists()
    )
