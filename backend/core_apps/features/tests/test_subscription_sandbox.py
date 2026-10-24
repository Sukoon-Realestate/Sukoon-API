"""Authenticated subscription sandbox; mocked transport never proves live capture."""

import uuid
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from core_apps.features.models import (
    AccountSubscription,
    CommerceFeature,
    LedgerTransaction,
    PaymobPayment,
    PaymentAttempt,
    PaymentQuote,
    PaymentReceipt,
    PlanBenefit,
    RentInvoice,
)
from core_apps.features.services import paymob_client
from core_apps.features.services.entitlements import decision
from core_apps.features.services.purchase_routing import routing_v1
from core_apps.features.services.paymob_payments import navigation, reconcile
from core_apps.features.tests import test_billing_subscriptions as billing_tests
from core_apps.features.tests import test_paymob_invoice_payments as paymob_tests
from core_apps.features.tests import test_rental_phase3 as rental_tests

ROOT, body, issue = billing_tests.ROOT, billing_tests.body, billing_tests.issue
buyer, client, plan = billing_tests.buyer, billing_tests.client, billing_tests.plan
paymob = paymob_tests.paymob
intention, snapshot = paymob_tests.intention, paymob_tests.snapshot
phase3_lease = rental_tests.phase3_lease

pytestmark = pytest.mark.django_db


@pytest.fixture
def sandbox(paymob, buyer):
    paymob.PAYMOB_INVOICE_CHECKOUT_ENABLED = False
    paymob.COMMERCE_SUBSCRIPTION_SANDBOX_ENABLED = True
    paymob.COMMERCE_SUBSCRIPTION_SANDBOX_USER_IDS = [str(buyer.id)]
    return paymob


def review_and_quote(client, plan):
    invoice = body(issue(client, plan)[0], 201)
    base = ROOT + f"billing/invoices/{invoice['id']}/"
    review = body(client.get(base, {"projection": "mobile_v1", "platform": "android"}))
    quote = body(
        client.post(
            base + "quote/?projection=mobile_v1&platform=android",
            {
                "expected_revision": invoice["revision"],
                "request_key": str(uuid.uuid4()),
            },
            format="json",
        ),
        201,
    )
    command = {
        "expected_revision": invoice["revision"],
        "quote_id": quote["id"],
        "request_key": str(uuid.uuid4()),
    }
    return review, quote, command, base


def reconcile_http(client, attempt):
    base = ROOT + f"payment-attempts/{attempt['id']}/"
    fresh = body(client.get(base))
    return body(
        client.post(
            base + "reconcile/",
            {"action": "reconcile", "expected_revision": fresh["revision"]},
            format="json",
        )
    )


def test_allowlisted_catalog_and_invoice_expose_explicit_sandbox(
    client, buyer, plan, sandbox
):
    assert not paymob_client.checkout_ready()
    for purpose in ("rent", "maintenance"):
        assert not routing_v1(purpose, "android", user=buyer)["enabled"]
    for endpoint in ("subscription-plans/", "subscriptions/current/"):
        catalog = body(client.get(ROOT + endpoint, {"projection": "mobile_v1"}))
        package = catalog["plans"][0]
        assert package["renewal_mode"] == "manual"
        for platform in ("android", "ios", "web"):
            route = package["purchase_routes"][platform]
            assert route["contract_version"] == 1
            assert route["product_type"] == "subscription" and route["message"] == ""
            assert route["route"] == "hosted_checkout" and route["enabled"]
            assert route["sandbox_only"] and route["external_checkout_allowed"]
            assert route["provider_environment"] == "sandbox"
    review, quote, command, base = review_and_quote(client, plan)
    assert "pay" in review["allowed_actions"]
    assert quote["purchase_route"] == review["purchase_route"]
    assert quote["provider_environment"] == "sandbox"
    assert quote["provider_mode"] == "hosted"
    assert not PaymentAttempt.objects.exists()


@pytest.mark.parametrize(
    "setting,value",
    [
        ("COMMERCE_SUBSCRIPTION_SANDBOX_USER_IDS", []),
        ("COMMERCE_SUBSCRIPTION_SANDBOX_USER_IDS", [str(uuid.uuid4())]),
        ("PAYMOB_SECRET_KEY", "egy_sk_live_forbidden"),
        ("PAYMOB_PUBLIC_KEY", "egy_pk_live_forbidden"),
        ("RENTAL_RUNTIME_ENVIRONMENT", "production"),
    ],
)
def test_unavailable_sandbox_never_falls_back_to_fake_provider(
    client,
    buyer,
    plan,
    sandbox,
    setting,
    value,
):
    setattr(sandbox, setting, value)
    assert not routing_v1("subscription", "android", plan=plan, user=buyer)["enabled"]
    invoice = body(issue(client, plan)[0], 201)
    assert "pay" not in invoice["allowed_actions"]
    response = client.post(
        ROOT + f"billing/invoices/{invoice['id']}/quote/?platform=android",
        {"expected_revision": 1, "request_key": str(uuid.uuid4())},
        format="json",
    )
    assert response.status_code == 409
    assert response["X-App-Error-Code"] == "purchase_route_unavailable"
    assert (
        not PaymentQuote.objects.exists() and not AccountSubscription.objects.exists()
    )


def test_disabled_switch_company_and_other_digital_products_remain_unavailable(
    buyer, plan, sandbox
):
    sandbox.COMMERCE_SUBSCRIPTION_SANDBOX_ENABLED = False
    assert not routing_v1("subscription", "android", plan=plan, user=buyer)["enabled"]
    sandbox.COMMERCE_SUBSCRIPTION_SANDBOX_ENABLED = True
    assert not routing_v1(
        "subscription", "android", plan=plan, user=buyer, organization=True
    )["enabled"]
    plan.audience = "organization"
    assert not routing_v1("subscription", "android", plan=plan, user=buyer)["enabled"]
    plan.audience = "personal"
    plan.active = False
    assert not routing_v1("subscription", "android", plan=plan, user=buyer)["enabled"]
    for purpose in ("advertising", "promotion"):
        assert not routing_v1(purpose, "android", user=buyer)["enabled"]


def test_verified_capture_activates_original_once_even_after_sale_switch_off(
    client,
    buyer,
    plan,
    sandbox,
):
    feature, _ = CommerceFeature.objects.update_or_create(
        code="priority_alerts",
        defaults={
            "workspace": "tenant",
            "available": True,
            "label_en": "Instant alerts",
            "label_ar": "تنبيهات فورية",
        },
    )
    PlanBenefit.objects.create(plan=plan, feature=feature, limit=5)
    review, quote, command, base = review_and_quote(client, plan)
    with patch(
        "core_apps.features.services.paymob_client.create_intention",
        side_effect=intention,
    ) as create:
        attempt = body(client.post(base + "checkout/", command, format="json"))
        replay = body(client.post(base + "checkout/", command, format="json"))
        assert replay["id"] == attempt["id"] and create.call_count == 1
        billing = create.call_args.args[1]
        assert billing["first_name"] == "Test" and billing["last_name"] == "Sandbox"
        assert billing["email"] == "sokoun-payment@example.test"
        assert billing["phone_number"] == "+201010101010"
        assert billing["email"] != buyer.email
    buyer.profile.refresh_from_db()
    assert not buyer.profile.phone_number
    assert attempt["provider_environment"] == "sandbox"
    assert attempt["checkout_session"]["provider_environment"] == "sandbox"
    assert attempt["status"] == "pending" and not attempt["retry_allowed"]
    assert (
        not AccountSubscription.objects.exists() and not PaymentReceipt.objects.exists()
    )
    assert not decision(buyer, "priority_alerts", "tenant")["allowed"]
    payment = PaymobPayment.objects.get()
    # Normal navigation/read traffic must not consume the dedicated inquiry
    # allowance before the user returns from the hosted page.
    for _ in range(8):
        assert client.get(base).status_code == 200
    sandbox.COMMERCE_SUBSCRIPTION_SANDBOX_ENABLED = False
    sandbox.COMMERCE_SUBSCRIPTION_SANDBOX_USER_IDS = []
    sandbox.PAYMOB_INVOICE_CHECKOUT_ENABLED = False
    with patch(
        "core_apps.features.services.paymob_client.inquiry",
        return_value=snapshot(payment),
    ):
        confirmed = reconcile_http(client, attempt)
        # Webhook/inquiry replay uses the same service, independently of the
        # user-facing reconciliation endpoint's deliberate throttle window.
        reconcile(payment)
    assert (
        confirmed["status"] == "captured"
        and confirmed["fulfillment_status"] == "fulfilled"
    )
    assert confirmed["provider_environment"] == "sandbox"
    assert (
        PaymentAttempt.objects.count()
        == PaymentReceipt.objects.count()
        == AccountSubscription.objects.count()
        == 1
    )
    assert LedgerTransaction.objects.filter(kind="hosted_purchase_capture").count() == 1
    subscription = AccountSubscription.objects.get()
    assert str(subscription.invoice.id) == review["id"] and not subscription.auto_renew
    entitlement = decision(buyer, "priority_alerts", "tenant")
    assert (
        entitlement["allowed"]
        and entitlement["source"] == "subscription"
        and entitlement["limit"] == 5
    )


def test_checkout_rechecks_allowlist_plan_and_quote_before_provider(
    client, buyer, plan, sandbox
):
    review, quote, command, base = review_and_quote(client, plan)
    with patch("core_apps.features.services.paymob_client.create_intention") as create:
        sandbox.COMMERCE_SUBSCRIPTION_SANDBOX_USER_IDS = []
        assert (
            client.post(base + "checkout/", command, format="json").status_code == 409
        )
        sandbox.COMMERCE_SUBSCRIPTION_SANDBOX_USER_IDS = [str(buyer.id)]
        plan.amount_minor += 1
        plan.save()
        assert (
            client.post(base + "checkout/", command, format="json").status_code == 409
        )
        plan.amount_minor -= 1
        plan.save()
        saved = PaymentQuote.objects.get(id=quote["id"])
        saved.purchase_route.pop("sandbox_only")
        saved.save()
        assert (
            client.post(base + "checkout/", command, format="json").status_code == 409
        )
        assert create.call_count == 0
    assert not PaymentAttempt.objects.exists()


def test_unknown_submission_recovers_without_new_intention(
    client, buyer, plan, sandbox
):
    review, quote, command, base = review_and_quote(client, plan)
    with patch(
        "core_apps.features.services.paymob_client.create_intention",
        side_effect=paymob_client.PaymobUnavailable(),
    ) as create:
        assert (
            client.post(base + "checkout/", command, format="json").status_code == 503
        )
        attempt = body(client.post(base + "checkout/", command, format="json"))
        assert attempt["checkout_session"]["checkout_url"] == ""
        assert create.call_count == 1
        assert (
            client.post(
                base + "checkout/",
                {**command, "request_key": str(uuid.uuid4())},
                format="json",
            ).status_code
            == 409
        )
    lookup = body(
        client.get(
            ROOT + "payment-attempts/",
            {
                "invoice_id": review["id"],
                "request_key": command["request_key"],
            },
        )
    )
    assert (
        lookup["results"][0]["id"] == attempt["id"] and not lookup["absence_confirmed"]
    )
    payment = PaymobPayment.objects.get()
    with patch(
        "core_apps.features.services.paymob_client.inquiry",
        return_value=snapshot(payment),
    ):
        assert reconcile_http(client, attempt)["fulfillment_status"] == "fulfilled"
    assert AccountSubscription.objects.count() == 1


@pytest.mark.parametrize(
    "origin",
    [
        "http://eg.checkout.paymob.com",
        "https://*.paymob.com",
        "https://eg.checkout.paymob.com/untrusted/path",
    ],
)
def test_checkout_navigation_rejects_insecure_or_wildcard_origins(paymob, origin):
    paymob.PAYMOB_CHECKOUT_EXTRA_ORIGINS = [origin]
    with pytest.raises(paymob_client.PaymobUnavailable):
        navigation(None)


def test_existing_checkout_recovers_canonical_redirect_without_new_intention(
    client, plan, sandbox
):
    review, quote, command, base = review_and_quote(client, plan)
    origins = ["https://accept.paymob.com", "https://eg.checkout.paymob.com"]
    with patch(
        "core_apps.features.services.paymob_client.create_intention",
        side_effect=intention,
    ) as create:
        original = body(client.post(base + "checkout/", command, format="json"))
        expected = original["checkout_session"]
        assert expected["navigation"]["allowed_origins"] == origins
        payment = PaymobPayment.objects.get()
        session = payment.attempt.checkout_session
        # Simulate a durable session issued before the canonical redirect fix.
        session.navigation["allowed_origins"] = ["https://accept.paymob.com"]
        session.save(update_fields=["navigation"])
        sandbox.COMMERCE_SUBSCRIPTION_SANDBOX_ENABLED = False
        sandbox.COMMERCE_SUBSCRIPTION_SANDBOX_USER_IDS = []
        # Newly configured extras must not silently extend an old session.
        sandbox.PAYMOB_CHECKOUT_EXTRA_ORIGINS = ["https://unrelated.example.test"]
        fresh = body(client.get(ROOT + f"payment-attempts/{original['id']}/"))
        lookup = body(
            client.get(
                ROOT + "payment-attempts/",
                {"invoice_id": review["id"], "request_key": command["request_key"]},
            )
        )["results"][0]
        replay = body(client.post(base + "checkout/", command, format="json"))
        for recovered in (fresh, lookup, replay):
            assert recovered["id"] == original["id"]
            assert recovered["checkout_session"] == expected
        assert create.call_count == 1
    session.refresh_from_db()
    assert session.navigation["allowed_origins"] == ["https://accept.paymob.com"]
    assert PaymentAttempt.objects.count() == PaymobPayment.objects.count() == 1
    assert not PaymentReceipt.objects.exists()
    assert not AccountSubscription.objects.exists()


def test_subscription_becoming_active_before_checkout_prevents_charge(
    client, buyer, plan, sandbox
):
    review, quote, command, base = review_and_quote(client, plan)
    invoice = RentInvoice.objects.get(id=review["id"])
    AccountSubscription.objects.create(
        user=buyer,
        plan=plan,
        invoice=invoice,
        workspace=plan.workspace,
        starts_at=timezone.now(),
        ends_at=timezone.now() + timedelta(days=30),
        plan_snapshot=invoice.purchase_snapshot,
    )
    with patch("core_apps.features.services.paymob_client.create_intention") as create:
        response = client.post(base + "checkout/", command, format="json")
        assert (
            response.status_code == 409
            and response["X-App-Error-Code"] == "subscription_active"
        )
        create.assert_not_called()


def test_subscription_cannot_be_submitted_as_rental_checkout(client, plan, sandbox):
    review, quote, command, base = review_and_quote(client, plan)
    sandbox.PAYMOB_INVOICE_CHECKOUT_ENABLED = True
    with patch("core_apps.features.services.paymob_client.create_intention") as create:
        response = client.post(
            ROOT + f"rent-invoices/{review['id']}/checkout/",
            {**command, "invoice_id": review["id"]},
            format="json",
        )
        assert response.status_code == 409
        assert response["X-App-Error-Code"] == "purchase_route_unavailable"
        create.assert_not_called()
    assert not PaymentAttempt.objects.exists()


def test_physical_checkout_still_requires_real_contact(phase3_lease, paymob):
    client, invoice, command = paymob_tests.rental_checkout(phase3_lease)
    tenant = phase3_lease[1]
    tenant.profile.phone_number = ""
    tenant.profile.save()
    with patch("core_apps.features.services.paymob_client.create_intention") as create:
        response = paymob_tests.post_checkout(client, invoice, command)
        assert response.status_code == 400
        assert response["X-App-Error-Code"] == "billing_details_required"
        create.assert_not_called()
    assert not PaymobPayment.objects.exists()


def test_synthetic_contact_requires_original_subscription_sandbox_quote(
    client, buyer, plan, sandbox
):
    from rest_framework.exceptions import ValidationError

    review, quote, command, base = review_and_quote(client, plan)
    invoice = RentInvoice.objects.get(id=review["id"])
    saved = PaymentQuote.objects.get(id=quote["id"])
    for field, value in (
        ("sandbox_only", False),
        ("enabled", False),
        ("provider_environment", "live"),
        ("external_checkout_allowed", False),
    ):
        original = saved.purchase_route[field]
        saved.purchase_route[field] = value
        with pytest.raises(ValidationError):
            paymob_client.billing_for_invoice(buyer, invoice, saved)
        saved.purchase_route[field] = original
    invoice.purpose = "maintenance"
    with pytest.raises(ValidationError):
        paymob_client.billing_for_invoice(buyer, invoice, saved)
