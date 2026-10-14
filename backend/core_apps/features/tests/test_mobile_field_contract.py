"""Field audit regressions: real DRF validation, services and rendered envelopes."""

import uuid

import pytest
from rest_framework.test import APIClient

from core_apps.features.models import (
    IdempotencyRecord,
    OwnerPaymentProfile,
    RentInvoice,
)
from core_apps.features.tests.test_billing_subscriptions import (
    buyer,
    client,
    plan,
    body,
    issue,
    ROOT,
)
from core_apps.features.tests.test_rental_phase2 import (
    rental_participants,
    authenticated,
)

pytestmark = pytest.mark.django_db


def test_cancellation_identity_exact_replay_and_unauthorized_account(
    client, buyer, plan
):
    invoice = body(issue(client, plan)[0], 201)
    path = ROOT + f"billing/invoices/{invoice['id']}/cancel/"
    key = str(uuid.uuid4())
    command = {"request_key": key, "expected_revision": invoice["revision"]}
    for malformed in (
        {"requestrequestKey": key, "expected_revision": 1},
        {"request_key": None, "expected_revision": 1},
        {"request_key": "", "expected_revision": 1},
        {"expected_revision": 1},
    ):
        response = client.post(path, malformed, format="json")
        assert response.status_code == 400
        assert set(response.json()) == {"message", "data"}
        assert response.json()["data"] is None
    invoice_model = RentInvoice.objects.get(id=invoice["id"])
    assert invoice_model.status == "due" and invoice_model.revision == 1
    first = client.post(path + "?projection=mobile_v1", command, format="json")
    replay = client.post(path + "?projection=mobile_v1", command, format="json")
    assert first.status_code == replay.status_code == 200
    assert first.json() == replay.json()
    assert first.json()["data"]["revision"] == 2
    assert first.json()["data"]["status"] == "cancelled"
    assert (
        IdempotencyRecord.objects.filter(
            operation=f"billing.cancel.{invoice['id']}"
        ).count()
        == 1
    )
    assert (
        client.post(
            path, {**command, "expected_revision": 2}, format="json"
        ).status_code
        == 409
    )
    other = type(buyer).objects.create_user(
        email="field-other@example.com", password="pass"
    )
    stranger = authenticated(other)
    assert stranger.post(path, command, format="json").status_code == 404
    assert APIClient().post(path, command, format="json").status_code == 401


def test_mobile_invoice_projection_preserves_money_pagination_and_legacy(client, plan):
    invoice = body(issue(client, plan)[0], 201)
    path = ROOT + f"billing/invoices/{invoice['id']}/"
    legacy = client.get(path).json()["data"]
    mobile = client.get(path, {"projection": "mobile_v1"}).json()["data"]
    assert set(legacy) - set(mobile) == {"purchase"}
    assert mobile == {k: v for k, v in legacy.items() if k not in {"purchase"}}
    assert mobile["lines"] == legacy["lines"]
    response = client.get(
        ROOT + "billing/invoices/", {"workspace": "owner", "projection": "mobile_v1"}
    )
    assert set(response.json()) == {"message", "data"}
    assert response.json()["data"] == [mobile]
    assert response["X-Total-Count"] == "1"
    assert (
        RentInvoice.objects.get(id=invoice["id"]).purchase_snapshot
        == legacy["purchase"]
    )


@pytest.mark.parametrize(
    "purpose,extra",
    [
        ("subscription", {"advertisement_id": str(uuid.uuid4())}),
        ("advertising", {"plan_id": str(uuid.uuid4())}),
        ("advertising", {"plan_revision": 1}),
    ],
)
def test_purchase_variants_reject_irrelevant_source_fields(
    client, plan, purpose, extra
):
    payload = {
        "purpose": purpose,
        "workspace": "owner",
        "request_key": str(uuid.uuid4()),
    }
    payload.update(
        {"plan_id": str(plan.id), "plan_revision": plan.revision}
        if purpose == "subscription"
        else {"advertisement_id": str(uuid.uuid4())}
    )
    result = client.post(
        ROOT + "billing/invoices/?projection=mobile_v1",
        {**payload, **extra},
        format="json",
    )
    assert result.status_code == 400 and result.json()["data"] is None
    assert not RentInvoice.objects.exists()


def test_owner_mobile_projection_and_consent_history(rental_participants):
    owner, tenant, stranger, _, _ = rental_participants
    client = authenticated(owner)
    path = ROOT + "owner-payment-profile/"
    legacy = client.get(path).json()["data"]
    profile = OwnerPaymentProfile.objects.get(id=legacy["id"])
    profile.accepted_policy_versions = ["historical-policy-v0"]
    profile.save(update_fields=["accepted_policy_versions"])
    legacy = client.get(path).json()["data"]
    mobile = client.get(path, {"projection": "mobile_v1"}).json()["data"]
    assert set(legacy) - set(mobile) == {"provider", "structured_summary"}
    assert mobile == {
        k: v for k, v in legacy.items() if k not in {"provider", "structured_summary"}
    }
    assert mobile["requirements"] == ["beneficiary", "identity_verification"]
    assert mobile["status"] == "not_started"
    command = {
        "expected_revision": mobile["revision"],
        "request_key": str(uuid.uuid4()),
        "accepted_policy_versions": mobile["required_policy_versions"],
    }
    for value in (None, [], ["unapproved-policy"]):
        denied = client.post(
            path + "onboarding-session/",
            {**command, "accepted_policy_versions": value},
            format="json",
        )
        assert denied.status_code == 400 and denied.json()["data"] is None
    first = client.post(path + "onboarding-session/", command, format="json")
    replay = client.post(path + "onboarding-session/", command, format="json")
    assert first.status_code == replay.status_code == 201
    assert first.json() == replay.json()
    profile.refresh_from_db()
    assert profile.status == "pending"  # A consent/session is not provider completion.
    assert profile.accepted_policy_versions == [
        "historical-policy-v0",
        *mobile["required_policy_versions"],
    ]
    stale = {**command, "request_key": str(uuid.uuid4())}
    assert (
        client.post(path + "onboarding-session/", stale, format="json").status_code
        == 409
    )
    for account in (tenant, stranger):
        assert authenticated(account).get(path).json()["data"]["id"] != str(profile.id)
    assert APIClient().get(path).status_code == 401


def test_legacy_purchase_validation_retained_until_clients_opt_in(client, plan):
    payload = {
        "purpose": "subscription",
        "workspace": "owner",
        "plan_id": str(plan.id),
        "plan_revision": plan.revision,
        "request_key": str(uuid.uuid4()),
        "advertisement_id": str(uuid.uuid4()),
    }
    legacy = client.post(ROOT + "billing/invoices/", payload, format="json")
    assert legacy.status_code == 201
    assert (
        client.post(ROOT + "billing/invoices/", payload, format="json").status_code
        == 200
    )
    strict = client.post(
        ROOT + "billing/invoices/?projection=mobile_v1", payload, format="json"
    )
    assert strict.status_code == 400 and strict.json()["data"] is None
    assert RentInvoice.objects.count() == 1


def test_participant_payout_contract_is_read_only(client):
    response = client.get(ROOT + "payouts/", {"workspace": "owner"})
    assert response.status_code == 200 and response.json()["data"] == []
    assert client.post(ROOT + "payouts/", {}, format="json").status_code == 405
    assert (
        client.post(
            ROOT + f"payouts/{uuid.uuid4()}/respond/", {}, format="json"
        ).status_code
        == 404
    )
    denied = client.post(ROOT + "operations/payouts/execute/", {}, format="json")
    assert denied.status_code == 403 and denied.json()["data"] is None
