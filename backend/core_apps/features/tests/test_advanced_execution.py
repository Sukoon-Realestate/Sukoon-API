from uuid import uuid4
import pytest
from django.test import override_settings
from core_apps.features.models import (
    Lease,
    OwnerPaymentProfile,
    PaymentAttempt,
    RentalProviderInstruction,
    RentalInventoryDayLock,
)
from core_apps.features.advanced_execution_models import AdvancedExecution
from .test_advanced_tenders import (
    enabled,
    post,
    command,
    published,
    bid_for,
    package_for,
    API,
)
from . import test_advanced_tenders as test_advanced_tenders_fixtures
from .test_rental_phase2 import rental_participants, authenticated

scenario = test_advanced_tenders_fixtures.scenario

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def execution_enabled():
    with override_settings(
        ADVANCED_HOUSING_PROVIDER_MODE="mock",
        ADVANCED_HOUSING_ENABLED_SERVICES=[
            "collective_tender_planning",
            "collective_tender_execution",
            "conditional_group_execution",
        ],
    ):
        yield


def ready(s, mode="independent_participants", *, two=False, prepare=True):
    tender = published(s)
    if two:
        from .test_advanced_tender_construction import two_unit_bid

        bid = two_unit_bid(s, tender)
    else:
        bid = post(
            s[0], f"housing-tenders/{tender['id']}/bids/", bid_for(s, tender), 201
        )["resource"]
    assignments = package_for(s, tender, bid)
    if two:
        assignments["allocations"].append(
            {"participant_id": str(s[2].id), "line_id": bid["lines"][1]["id"]}
        )
    package = post(
        s[1],
        f"housing-tenders/{tender['id']}/package-runs/",
        assignments,
        201,
    )["resource"]
    for person in [s[1], *([s[2]] if two else [])]:
        package = post(
            person,
            f"housing-packages/{package['id']}/consents/",
            command(
                package["revision"],
                digest=package["digest"],
                decision="accept",
                independent_ack=True,
            ),
        )["resource"]
    result = post(
        s[1],
        f"housing-packages/{package['id']}/prepare/",
        command(package["revision"], digest=package["digest"], execution_mode=mode),
    )["resource"]
    for actor in [s[0], s[1], *([s[2]] if two else [])]:
        result = act(
            actor,
            result,
            "consents",
            decision="accept",
            policy_version=result["policy_version"],
        )
    OwnerPaymentProfile.objects.update_or_create(
        owner=s[0],
        defaults={
            "status": "ready",
            "payout_ready": True,
            "accepted_policy_versions": ["rental-policy-v1"],
            "provider": "fake",
            "provider_account_id": "test-owner",
        },
    )
    return act(s[1], result, "prepare") if prepare else result


def act(actor, plan, action, expected=200, **kwargs):
    if action == "advance":
        leg = next(
            (item for item in plan["legs"] if item["id"] == kwargs.get("leg_id")), {}
        )
        kwargs = {
            "document_hash": leg.get("document_hash"),
            "invoice_id": leg.get("invoice_id"),
            "invoice_revision": leg.get("invoice_revision"),
            "amount_minor": leg.get("first_invoice_minor"),
            **kwargs,
        }
    return post(
        actor,
        f"advanced-executions/{plan['id']}/{action}/",
        command(plan["revision"], digest=plan["digest"], **kwargs),
        expected,
    ).get("resource")


def refresh(actor, plan):
    r = authenticated(actor).get(API + f"advanced-executions/{plan['id']}/")
    assert r.status_code == 200, r.data
    return r.data


def sign_both(s, plan):
    plan = act(
        s[0],
        plan,
        "advance",
        leg_id=plan["legs"][0]["id"],
        step="sign",
        mock_outcome="confirmed",
    )
    return act(
        s[1],
        plan,
        "advance",
        leg_id=plan["legs"][0]["id"],
        step="sign",
        mock_outcome="confirmed",
    )


def test_exact_handoff_and_mock_capture_uses_canonical_ledger(scenario):
    plan = ready(scenario)
    assert plan["provider_mode"] == "mock" and plan["simulated"]
    lease = Lease.objects.get(id=plan["legs"][0]["lease_id"])
    assert lease.tenant == scenario[1] and lease.rent_amount_minor == 1000000
    assert RentalInventoryDayLock.objects.filter(lease=lease).exists()
    assert not lease.signing_sessions.exists()
    plan = sign_both(scenario, plan)
    assert plan["legs"][0]["lease_status"] == "signed"
    plan = act(
        scenario[1],
        plan,
        "advance",
        leg_id=plan["legs"][0]["id"],
        step="pay",
        mock_outcome="confirmed",
    )
    assert plan["state"] == "completed"
    attempt = PaymentAttempt.objects.get(invoice__lease=lease)
    assert attempt.payment_status == "captured" and attempt.invoice.status == "paid"
    lease.refresh_from_db()
    assert lease.status == "active" and lease.occupancy_status == "not_started"


def test_unknown_after_capture_reconciles_original_instruction_without_repay(scenario):
    plan = sign_both(scenario, ready(scenario))
    key = str(uuid4())
    body = {
        "request_key": key,
        "expected_revision": plan["revision"],
        "digest": plan["digest"],
        "leg_id": plan["legs"][0]["id"],
        "step": "pay",
        "mock_outcome": "unknown_after",
        "document_hash": plan["legs"][0]["document_hash"],
        "invoice_id": plan["legs"][0]["invoice_id"],
        "invoice_revision": plan["legs"][0]["invoice_revision"],
        "amount_minor": plan["legs"][0]["first_invoice_minor"],
    }
    route = f"advanced-executions/{plan['id']}/advance/"
    result = post(scenario[1], route, body)
    assert post(scenario[1], route, body) == result
    plan = result["resource"]
    assert plan["state"] == "unknown" and PaymentAttempt.objects.count() == 1
    assert RentalProviderInstruction.objects.filter(status="unknown").count() == 1
    act(scenario[1], plan, "advance", 409, leg_id=plan["legs"][0]["id"], step="pay")
    plan = act(scenario[1], plan, "reconcile")
    assert plan["state"] == "completed" and PaymentAttempt.objects.count() == 1
    assert not RentalProviderInstruction.objects.filter(status="unknown").exists()


def test_proxy_signing_and_stale_execution_consent_rejected(scenario):
    plan = ready(scenario)
    act(scenario[2], plan, "advance", 404, leg_id=plan["legs"][0]["id"], step="sign")
    assert not Lease.objects.get(
        id=plan["legs"][0]["lease_id"]
    ).signing_sessions.exists()
    stale = {**plan, "revision": plan["revision"] - 1}
    act(scenario[1], stale, "advance", 409, leg_id=plan["legs"][0]["id"], step="sign")


def test_unsigned_withdraw_releases_only_own_hold_and_preserves_history(scenario):
    plan = ready(scenario)
    plan = act(scenario[1], plan, "withdraw", leg_id=plan["legs"][0]["id"])
    assert plan["state"] == "manual_resolution"
    lease = Lease.objects.get(id=plan["legs"][0]["lease_id"])
    assert lease.status == "cancelled" and not lease.inventory_day_locks.exists()
    assert plan["steps"]
    with override_settings(ADVANCED_HOUSING_PROVIDER_MODE="disabled"):
        old = refresh(scenario[1], plan)
        assert old["allowed_actions"] == [] and old["legs"][0]["lease_id"] == str(
            lease.id
        )


def test_unknown_before_signature_is_not_failure_until_reconciled(scenario):
    plan = ready(scenario)
    plan = act(
        scenario[0],
        plan,
        "advance",
        leg_id=plan["legs"][0]["id"],
        step="sign",
        mock_outcome="unknown_before",
    )
    assert plan["state"] == "unknown"
    act(scenario[1], plan, "withdraw", 409, leg_id=plan["legs"][0]["id"])
    plan = act(scenario[0], plan, "reconcile")
    assert RentalProviderInstruction.objects.filter(
        status="failed", failure_code="mock_not_applied"
    ).exists()
    assert not Lease.objects.get(
        id=plan["legs"][0]["lease_id"]
    ).signing_sessions.exists()
    plan = act(
        scenario[0],
        plan,
        "advance",
        leg_id=plan["legs"][0]["id"],
        step="sign",
        mock_outcome="confirmed",
    )
    assert (
        Lease.objects.get(id=plan["legs"][0]["lease_id"]).signing_sessions.count() == 1
    )


def test_inbox_and_receipt_recovery_are_actor_scoped_when_disabled(scenario):
    plan = ready(scenario)
    for actor in [scenario[0], scenario[1]]:
        response = authenticated(actor).get(API + "advanced-executions/")
        assert (
            response.status_code == 200
            and response.data["results"][0]["id"] == plan["id"]
        )
    assert (
        authenticated(scenario[2]).get(API + "advanced-executions/").data["results"]
        == []
    )
    body = command(plan["revision"], digest=plan["digest"])
    result = post(scenario[1], f"advanced-executions/{plan['id']}/reconcile/", body)
    lookup = authenticated(scenario[1]).get(
        API + f"rental-operations/{body['request_key']}/", {"subject_id": plan["id"]}
    )
    assert (
        lookup.status_code == 200
        and lookup.data["operation_receipt"] == result["operation_receipt"]
    )
    with override_settings(
        ADVANCED_HOUSING_PROVIDER_MODE="disabled", ADVANCED_HOUSING_ENABLED_SERVICES=[]
    ):
        response = authenticated(scenario[0]).get(API + "advanced-executions/")
        assert (
            response.status_code == 200
            and response.data["results"][0]["allowed_actions"] == []
        )
        act(scenario[0], result["resource"], "prepare", 403)


def test_document_and_invoice_review_are_exact_before_provider_instruction(scenario):
    plan = ready(scenario)
    leg = plan["legs"][0]["id"]
    act(
        scenario[0],
        plan,
        "advance",
        409,
        leg_id=leg,
        step="sign",
        document_hash="outdated",
    )
    assert not RentalProviderInstruction.objects.exists()
    plan = sign_both(scenario, plan)
    act(scenario[1], plan, "advance", 409, leg_id=leg, step="pay", amount_minor=1)
    assert not PaymentAttempt.objects.exists()


def test_conditional_signing_and_uncertain_payment_thresholds(scenario):
    plan = ready(scenario, "conditional_package", two=True)
    first = next(
        x["id"]
        for x in AdvancedExecution.objects.get(id=plan["id"]).legs.values(
            "id", "specification"
        )
        if x["specification"]["tenant_id"] == str(scenario[1].id)
    )
    first = str(first)
    second = next(x["id"] for x in plan["legs"] if x["id"] != first)
    for actor in [scenario[0], scenario[1]]:
        plan = act(actor, refresh(actor, plan), "advance", leg_id=first, step="sign")
    act(scenario[1], plan, "advance", 409, leg_id=first, step="pay")
    for actor in [scenario[0], scenario[2]]:
        plan = act(actor, refresh(actor, plan), "advance", leg_id=second, step="sign")
    plan = act(
        scenario[1],
        refresh(scenario[1], plan),
        "advance",
        leg_id=first,
        step="pay",
        mock_outcome="unknown_after",
    )
    act(
        scenario[2],
        refresh(scenario[2], plan),
        "advance",
        409,
        leg_id=second,
        step="pay",
    )
    plan = act(scenario[1], plan, "reconcile")
    plan = act(
        scenario[2], refresh(scenario[2], plan), "advance", leg_id=second, step="pay"
    )
    assert plan["state"] == "completed" and PaymentAttempt.objects.count() == 2


def test_partial_independent_completion_preserves_discount_and_requires_every_resolution(
    scenario,
):
    plan = ready(scenario, two=True)
    model = AdvancedExecution.objects.get(id=plan["id"])
    first = str(
        next(
            x.id
            for x in model.legs.all()
            if x.specification["tenant_id"] == str(scenario[1].id)
        )
    )
    second = next(x["id"] for x in plan["legs"] if x["id"] != first)
    for actor in [scenario[0], scenario[1]]:
        plan = act(actor, refresh(actor, plan), "advance", leg_id=first, step="sign")
    plan = act(scenario[1], plan, "advance", leg_id=first, step="pay")
    plan = act(scenario[2], refresh(scenario[2], plan), "withdraw", leg_id=second)
    assert plan["state"] == "partial"
    confirmed = model.legs.get(id=first).lease
    assert confirmed.status == "active" and confirmed.rent_amount_minor == 800000
    for actor in [scenario[0], scenario[1], scenario[2]]:
        plan = act(
            actor,
            refresh(actor, plan),
            "resolve",
            policy_version=plan["policy_version"],
            resolution="preserve_confirmed",
        )
    assert plan["state"] == "closed_partial"
    confirmed.refresh_from_db()
    assert confirmed.status == "active" and confirmed.rent_amount_minor == 800000


def test_signed_withdrawal_keeps_obligation_and_support_case_through_reconcile(
    scenario,
):
    plan = sign_both(scenario, ready(scenario))
    lease_id = plan["legs"][0]["lease_id"]
    plan = act(scenario[1], plan, "withdraw", leg_id=plan["legs"][0]["id"])
    assert plan["state"] == "manual_resolution" and plan["case_id"]
    plan = act(scenario[1], plan, "reconcile")
    assert plan["state"] == "manual_resolution"
    act(
        scenario[1],
        plan,
        "resolve",
        409,
        policy_version=plan["policy_version"],
        resolution="preserve_confirmed",
    )
    assert Lease.objects.get(id=lease_id).status == "signed"
