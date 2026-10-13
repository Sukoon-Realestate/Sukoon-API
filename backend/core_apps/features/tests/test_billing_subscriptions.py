import uuid
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from core_apps.features.models import (
    AccountSubscription,
    LedgerTransaction,
    PaymentAttempt,
    PaymentReceipt,
    RentInvoice,
    SubscriptionPlan,
)

ROOT = "/api/v1/features/v1/"
pytestmark = pytest.mark.django_db


@pytest.fixture
def buyer():
    return get_user_model().objects.create_user(
        email="billing-local@example.test",
        password="local-test-only",
        first_name="Local",
        last_name="Buyer",
    )


@pytest.fixture
def client(buyer):
    client = APIClient()
    client.force_authenticate(buyer)
    return client


@pytest.fixture
def plan():
    return SubscriptionPlan.objects.create(
        name_en="Local test plan",
        name_ar="خطة اختبار محلية",
        workspace="both",
        period_months=1,
        amount_minor=12500,
    )


def body(response, expected=200):
    assert response.status_code == expected, response.content
    data = response.json()
    assert set(data) == {"message", "data"}
    assert data["message"].strip()
    return data["data"]


def issue(client, plan, workspace="tenant", key=None):
    request = {
        "purpose": "subscription",
        "workspace": workspace,
        "plan_id": str(plan.id),
        "plan_revision": plan.revision,
        "request_key": key or str(uuid.uuid4()),
    }
    return client.post(ROOT + "billing/invoices/", request, format="json"), request


def pay(client, invoice):
    quote = body(
        client.post(
            ROOT + f"billing/invoices/{invoice['id']}/quote/",
            {
                "expected_revision": invoice["revision"],
                "request_key": str(uuid.uuid4()),
            },
            format="json",
        ),
        201,
    )
    request = {
        "quote_id": quote["id"],
        "expected_revision": invoice["revision"],
        "request_key": str(uuid.uuid4()),
    }
    response = client.post(
        ROOT + f"billing/invoices/{invoice['id']}/checkout/", request, format="json"
    )
    return response, request


@pytest.mark.parametrize("workspace", ["tenant", "owner"])
def test_invoice_review_then_mock_payment_activates_once(
    client, buyer, plan, workspace
):
    assert (
        body(client.get(ROOT + "subscriptions/current/", {"workspace": workspace}))[
            "subscription"
        ]
        is None
    )
    response, request = issue(client, plan, workspace)
    invoice = body(response, 201)
    assert invoice["status"] == "due" and invoice["paid_minor"] == 0
    assert (
        not PaymentAttempt.objects.exists() and not AccountSubscription.objects.exists()
    )
    assert (
        body(client.post(ROOT + "billing/invoices/", request, format="json"))["id"]
        == invoice["id"]
    )
    # Server prices change only future invoices, never this issued snapshot.
    plan.amount_minor = 20000
    plan.revision += 1
    plan.save()
    assert (
        body(client.get(ROOT + f"billing/invoices/{invoice['id']}/"))["total_minor"]
        == 12500
    )
    paid, request = pay(client, invoice)
    attempt = body(paid)
    assert (
        attempt["status"] == "captured"
        and attempt["receipt_id"]
        and attempt["provider_mode"] == "mock"
    )
    assert (
        body(
            client.post(
                ROOT + f"billing/invoices/{invoice['id']}/checkout/",
                request,
                format="json",
            )
        )["id"]
        == attempt["id"]
    )
    for role in ("tenant", "owner"):
        current = body(client.get(ROOT + "subscriptions/current/", {"workspace": role}))
        assert (
            current["is_subscriped"] is True
            and current["subscription"]["status"] == "active"
        )
    assert (
        PaymentAttempt.objects.count()
        == PaymentReceipt.objects.count()
        == AccountSubscription.objects.count()
        == 1
    )
    assert LedgerTransaction.objects.filter(kind="mock_purchase_capture").count() == 1
    invoices = client.get(ROOT + "billing/invoices/", {"workspace": workspace})
    assert body(invoices)[0]["status"] == "paid" and invoices["X-Total-Count"] == "1"


def test_wrong_account_and_price_tampering_do_not_pay(client, buyer, plan):
    response, request = issue(client, plan)
    invoice = body(response, 201)
    other = APIClient()
    other.force_authenticate(
        get_user_model().objects.create_user(
            email="stranger@example.test", password="local-test-only"
        )
    )
    assert body(other.get(ROOT + f"billing/invoices/{invoice['id']}/"), 404) is None
    altered = {**request, "request_key": str(uuid.uuid4()), "amount_minor": 1}
    assert (
        body(client.post(ROOT + "billing/invoices/", altered, format="json"), 400)
        is None
    )
    assert not PaymentAttempt.objects.exists()


def test_stale_disabled_plan_and_conflicting_key(client, plan):
    response, request = issue(client, plan)
    assert response.status_code == 201
    changed = {**request, "workspace": "owner"}
    response = client.post(ROOT + "billing/invoices/", changed, format="json")
    assert (
        body(response, 409) is None
        and response["X-App-Error-Code"] == "idempotency_conflict"
    )
    plan.active = False
    plan.save()
    paid, _ = pay_disabled(
        client,
        body(
            response=client.get(
                ROOT + f"billing/invoices/{RentInvoice.objects.get().id}/"
            )
        ),
    )
    assert body(paid, 409) is None


def pay_disabled(client, invoice):
    return (
        client.post(
            ROOT + f"billing/invoices/{invoice['id']}/quote/",
            {
                "expected_revision": invoice["revision"],
                "request_key": str(uuid.uuid4()),
            },
            format="json",
        ),
        None,
    )


def test_production_mock_is_refused(client, plan, settings):
    invoice = body(issue(client, plan)[0], 201)
    settings.RENTAL_RUNTIME_ENVIRONMENT = "production"
    response, _ = pay_disabled(client, invoice)
    assert body(response, 403) is None
    assert not PaymentAttempt.objects.exists()


def test_lost_response_recovers_same_attempt_and_expiry_is_truthful(
    client, plan, buyer
):
    invoice = body(issue(client, plan)[0], 201)
    response, request = pay(client, invoice)
    # Simulate losing the committed response: a new session only knows the
    # persisted invoice and request key, and performs authorized readback.
    restored = APIClient()
    restored.force_authenticate(buyer)
    lookup = body(
        restored.get(
            ROOT + "payment-attempts/",
            {"invoice_id": invoice["id"], "request_key": request["request_key"]},
        )
    )
    assert lookup["results"][0]["id"] == body(response)["id"]
    assert lookup["absence_confirmed"] is False
    subscription = AccountSubscription.objects.get()
    subscription.starts_at = timezone.now() - timedelta(days=60)
    subscription.ends_at = timezone.now() - timedelta(days=1)
    subscription.save()
    current = body(client.get(ROOT + "subscriptions/current/"))
    assert (
        current["subscription"]["status"] == "expired"
        and current["is_subscriped"] is True
    )


def test_payment_failure_rolls_back_invoice_entitlement_and_ledger(client, plan):
    invoice = body(issue(client, plan)[0], 201)
    with patch(
        "core_apps.features.services.billing_settlement.PaymentReceipt.objects.create",
        side_effect=RuntimeError("injected"),
    ):
        response, request = pay(client, invoice)
    assert body(response, 500) is None
    assert (
        not PaymentAttempt.objects.exists() and not AccountSubscription.objects.exists()
    )
    assert not LedgerTransaction.objects.exists()
    assert RentInvoice.objects.get().status == "due"
