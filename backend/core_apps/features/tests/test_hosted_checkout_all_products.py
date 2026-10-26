"""HTTP and provider-boundary checks for the shared Sandbox purchase route."""

import base64
import json
import uuid
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from core_apps.features.models import (
    AccountSubscription,
    PaymobPayment,
    PaymentAttempt,
    PaymentReceipt,
    PaymentFulfillment,
)
from core_apps.features.services.paymob_payments import reconcile
from core_apps.features.services.purchase_routing import routing_v1
from core_apps.features.services.payment_resume import resume
from core_apps.features.services import paymob_client
from core_apps.features.tests.test_billing_subscriptions import (
    buyer,
    client,
    plan,
    body,
    issue,
    ROOT,
)
from core_apps.features.tests.test_paymob_invoice_payments import (
    paymob,
    intention,
    snapshot,
)
from core_apps.features.tests.test_subscription_sandbox import review_and_quote

pytestmark = pytest.mark.django_db


@pytest.fixture
def hosted(paymob):
    paymob.COMMERCE_HOSTED_SANDBOX_ENABLED = True
    paymob.COMMERCE_SUBSCRIPTION_SANDBOX_ENABLED = False
    paymob.COMMERCE_SUBSCRIPTION_SANDBOX_USER_IDS = []
    return paymob


def checkout(client, plan):
    invoice, quote, command, base = review_and_quote(client, plan)
    with patch(
        "core_apps.features.services.paymob_client.create_intention",
        side_effect=intention,
    ):
        response = body(
            client.post(
                base + "checkout/?projection=mobile_v1&platform=android",
                command,
                format="json",
            )
        )
    return PaymobPayment.objects.get(attempt__id=response["id"])


@pytest.mark.parametrize(
    "purpose",
    [
        "subscription",
        "advertising",
        "promotion",
        "rent",
        "deposit",
        "maintenance",
        "settlement",
        "adjustment",
    ],
)
@pytest.mark.parametrize("platform", ["ios", "android"])
def test_all_products_expose_hosted_route_without_allowlist(
    buyer, plan, hosted, purpose, platform
):
    route = routing_v1(purpose, platform, user=buyer, plan=plan)
    assert route["enabled"] and route["route"] == "hosted_checkout"
    assert route["sandbox_only"] and route["provider_environment"] == "sandbox"


def test_production_runtime_cannot_enable_sandbox(buyer, plan, hosted):
    hosted.RENTAL_RUNTIME_ENVIRONMENT = "production"
    assert not paymob_client.checkout_ready()
    assert not routing_v1("subscription", "android", user=buyer, plan=plan)["enabled"]


def test_hosted_worker_is_registered_and_explicitly_admitted(settings, monkeypatch):
    from config.background import configure

    monkeypatch.setenv("SOKOUN_GENERAL_BACKGROUND_ENABLED", "true")
    monkeypatch.setenv("SOKOUN_BACKGROUND_SCHEDULES", "reconcile-hosted-checkout")
    scope = {"CELERY_BEAT_SCHEDULE": settings.BACKGROUND_SCHEDULE_CATALOG}
    configure(scope)
    entry = scope["CELERY_BEAT_SCHEDULE"]["reconcile-hosted-checkout"]
    assert entry["task"] in scope["GENERAL_BACKGROUND_ALLOWED_TASKS"]
    assert entry["options"]["queue"] == "sokoun-general"


def test_capture_survives_delivery_failure_and_worker_fulfills_once(
    client, buyer, plan, hosted
):
    payment = checkout(client, plan)
    with patch(
        "core_apps.features.services.paymob_client.inquiry",
        return_value=snapshot(payment),
    ), patch(
        "core_apps.features.services.billing_settlement.fulfill_purchase",
        side_effect=RuntimeError("delivery temporarily down"),
    ):
        reconcile(payment)
        reconcile(payment)
    payment.attempt.refresh_from_db()
    assert payment.attempt.payment_status == "captured"
    assert PaymentReceipt.objects.count() == 1
    assert not AccountSubscription.objects.exists()
    assert PaymentFulfillment.objects.get().status == "pending"
    call_command("reconcile_paymob_payments", limit=1)
    call_command("reconcile_paymob_payments", limit=1)
    assert PaymentReceipt.objects.count() == AccountSubscription.objects.count() == 1
    assert PaymentFulfillment.objects.get().status == "fulfilled"


@pytest.mark.parametrize("change_before_quote", [True, False])
def test_hosted_subscription_keeps_issued_price_and_duration(
    client, buyer, plan, hosted, change_before_quote
):
    original_amount, original_months = plan.amount_minor, plan.period_months
    invoice = body(issue(client, plan)[0], 201)
    base = ROOT + f"billing/invoices/{invoice['id']}/"

    def update_catalog():
        plan.amount_minor += 7654
        plan.period_months = 12
        plan.revision += 1
        plan.save()

    if change_before_quote:
        update_catalog()
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
    if not change_before_quote:
        update_catalog()
    review = body(client.get(base, {"projection": "mobile_v1", "platform": "android"}))
    assert review["purchase_route"]["enabled"]
    assert review["total_minor"] == original_amount
    command = {
        "expected_revision": invoice["revision"],
        "quote_id": quote["id"],
        "request_key": str(uuid.uuid4()),
    }
    with patch(
        "core_apps.features.services.paymob_client.create_intention",
        side_effect=intention,
    ) as provider:
        response = body(
            client.post(
                base + "checkout/?projection=mobile_v1&platform=android",
                command,
                format="json",
            )
        )
        replay = body(
            client.post(
                base + "checkout/?projection=mobile_v1&platform=android",
                command,
                format="json",
            )
        )
    assert response["id"] == replay["id"] and provider.call_count == 1
    payment = PaymobPayment.objects.get(attempt__id=response["id"])
    assert payment.attempt.amount_minor == original_amount
    with patch(
        "core_apps.features.services.paymob_client.inquiry",
        return_value=snapshot(payment),
    ):
        reconcile(payment)
        reconcile(payment)
    subscription = AccountSubscription.objects.get(invoice__id=invoice["id"])
    assert subscription.plan_snapshot["amount_minor"] == original_amount
    assert subscription.plan_snapshot["period_months"] == original_months
    assert PaymentReceipt.objects.count() == 1


def test_no_card_submission_remains_pending_without_generic_provider_error(
    client, plan, hosted
):
    payment = checkout(client, plan)
    with patch(
        "core_apps.features.services.paymob_client.inquiry",
        side_effect=paymob_client.PaymobUnavailable,
    ), patch(
        "core_apps.features.services.paymob_client.order_transactions", return_value=[]
    ):
        assert reconcile(payment).payment_status == "pending"
        call_command("reconcile_paymob_payments", limit=1)
    payment.refresh_from_db()
    assert payment.reconciled_at is not None
    assert not PaymentReceipt.objects.exists()


def renewal(payment, redirect):
    claims = {
        "redirection_url": redirect,
        "order_id": int(payment.order_id),
        "amount_cents": payment.attempt.amount_minor,
        "currency": payment.attempt.currency,
        "integration_id": int(payment.integration_id),
        "exp": int((timezone.now() + timedelta(minutes=15)).timestamp()),
    }
    token = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
    return {
        **intention(payment, {}, redirect),
        "confirmed": False,
        "status": "intended",
        "payment_methods": [
            {
                "integration_id": int(payment.integration_id),
                "live": False,
                "currency": payment.attempt.currency,
            }
        ],
        "payment_keys": [
            {
                "key": base64.b64encode(
                    ("header." + token + ".signature").encode()
                ).decode(),
                "redirection_url": redirect,
            }
        ],
    }


def test_expired_session_resumes_same_intention_and_same_receipt(
    client, buyer, plan, hosted
):
    payment = checkout(client, plan)
    session = payment.attempt.checkout_session
    session.expires_at = timezone.now() - timedelta(minutes=1)
    session.save()
    key = str(uuid.uuid4())
    with patch(
        "core_apps.features.services.paymob_client.order_transactions", return_value=[]
    ), patch(
        "core_apps.features.services.paymob_client.renew_intention", side_effect=renewal
    ) as renew, patch(
        "core_apps.features.services.paymob_client.create_intention"
    ) as create:
        for _ in range(2):
            response = body(
                client.post(
                    ROOT + f"payment-attempts/{payment.attempt.id}/resume/",
                    {"request_key": key},
                    format="json",
                )
            )
            assert response["checkout_session"]["session_id"] == str(session.id)
        assert renew.call_count == 1 and create.call_count == 0
    assert PaymentAttempt.objects.count() == 1
    assert not PaymentReceipt.objects.exists()


def test_crashed_renewal_is_read_before_any_further_provider_update(
    client, buyer, plan, hosted
):
    from core_apps.features.models import IdempotencyRecord

    payment = checkout(client, plan)
    session = payment.attempt.checkout_session
    session.expires_at = timezone.now() - timedelta(minutes=1)
    session.save()

    class WorkerStopped(BaseException):
        pass

    with patch.object(
        paymob_client, "order_transactions", return_value=[]
    ), patch.object(paymob_client, "renew_intention", side_effect=WorkerStopped):
        with pytest.raises(WorkerStopped):
            resume(buyer, payment.attempt, uuid.uuid4())
    payment.refresh_from_db()
    assert payment.status == "renewing"
    claim_id = payment.renewal_request_id
    with patch.object(paymob_client, "order_transactions") as lookup, patch.object(
        paymob_client, "renew_intention"
    ) as renew:
        resume(buyer, payment.attempt, uuid.uuid4())
    lookup.assert_not_called()
    renew.assert_not_called()
    PaymobPayment.objects.filter(pk=payment.pk).update(
        renewal_claimed_at=timezone.now() - timedelta(minutes=3)
    )
    from urllib.parse import urlencode

    redirect = (
        session.navigation["return_url"]
        + "?"
        + urlencode(
            {
                "state": session.return_state,
                "payment_attempt_id": str(payment.attempt.id),
            }
        )
    )
    with patch.object(
        paymob_client, "order_transactions", return_value=[]
    ), patch.object(
        paymob_client,
        "retrieve_intention",
        side_effect=lambda value: renewal(value, redirect),
    ) as retrieve, patch.object(
        paymob_client, "renew_intention"
    ) as renew, patch.object(
        paymob_client, "create_intention"
    ) as create:
        recovered = resume(buyer, payment.attempt, uuid.uuid4())
    assert recovered.checkout_session.expires_at > timezone.now()
    retrieve.assert_called_once()
    renew.assert_not_called()
    create.assert_not_called()
    assert IdempotencyRecord.objects.get(id=claim_id).recovery_status == "confirmed"
    assert PaymentAttempt.objects.count() == 1
    assert not PaymentReceipt.objects.exists()


def test_late_renewal_result_cannot_overwrite_a_newer_claim(
    client, buyer, plan, hosted
):
    from django.db import transaction
    from core_apps.features.services.payment_resume import _start_renewal, _save_session

    payment = checkout(client, plan)
    session = payment.attempt.checkout_session
    expiry_before = session.expires_at
    with transaction.atomic():
        old = _start_renewal(
            buyer, payment.attempt, session, payment, str(uuid.uuid4())
        )
        newer = _start_renewal(
            buyer, payment.attempt, session, payment, str(uuid.uuid4())
        )
    assert old.id != newer.id
    assert not _save_session(
        payment,
        session,
        {"client_secret": "synthetic-secret"},
        timezone.now() + timedelta(minutes=5),
        "renewing",
        old.id,
    )
    session.refresh_from_db()
    payment.refresh_from_db()
    assert session.expires_at == expiry_before
    assert payment.status == "renewing" and payment.renewal_request_id == newer.id


def test_retired_renewal_worker_cannot_send_after_reading_the_order(
    client, buyer, plan, hosted
):
    from django.db import transaction
    from core_apps.features.services.payment_resume import _start_renewal, _renew

    payment = checkout(client, plan)
    session = payment.attempt.checkout_session
    with transaction.atomic():
        old = _start_renewal(
            buyer, payment.attempt, session, payment, str(uuid.uuid4())
        )

    def lookup(_):
        PaymobPayment.objects.filter(pk=payment.pk).update(status="renewal_unknown")
        return []

    with patch.object(
        paymob_client, "order_transactions", side_effect=lookup
    ), patch.object(paymob_client, "renew_intention") as renew:
        _renew(payment, payment.attempt, session, "https://bound.example.test/", old)
    renew.assert_not_called()


def test_resume_rejects_unbound_provider_return_and_never_replays_unknown_put(
    client, buyer, plan, hosted
):
    payment = checkout(client, plan)
    session = payment.attempt.checkout_session
    session.expires_at = timezone.now() - timedelta(minutes=1)
    session.save()
    with patch(
        "core_apps.features.services.paymob_client.order_transactions", return_value=[]
    ), patch(
        "core_apps.features.services.paymob_client.renew_intention",
        side_effect=lambda payment, redirect: renewal(payment, "https://wrong.test/"),
    ) as renew:
        with pytest.raises(paymob_client.PaymobUnavailable):
            resume(buyer, payment.attempt, uuid.uuid4())
        with patch(
            "core_apps.features.services.paymob_client.retrieve_intention",
            side_effect=paymob_client.PaymobUnavailable,
        ):
            with pytest.raises(paymob_client.PaymobUnavailable):
                resume(buyer, payment.attempt, uuid.uuid4())
        assert renew.call_count == 1
    payment.refresh_from_db()
    assert payment.status == "renewal_unknown"


@pytest.mark.parametrize("invalid", [None, "redirect", "order", "live", "expired"])
def test_unknown_renewal_recovers_only_verified_read_only_provider_shape(
    client, buyer, plan, hosted, invalid
):
    payment = checkout(client, plan)
    session = payment.attempt.checkout_session
    session.expires_at = timezone.now() - timedelta(minutes=1)
    session.save()
    payment.status = "renewal_unknown"
    payment.save()
    from urllib.parse import urlencode

    redirect = (
        session.navigation["return_url"]
        + "?"
        + urlencode(
            {
                "state": session.return_state,
                "payment_attempt_id": str(payment.attempt.id),
            }
        )
    )
    response = renewal(payment, redirect)
    response["order_id"] = response.pop("intention_order_id")
    response["redirection_url"] = redirect
    response["paid"] = False
    response["payment_keys"] = {
        "live": False,
        "card": response["payment_keys"][0]["key"],
        "redirection_url": session.navigation["return_url"],
    }
    if invalid == "redirect":
        response["redirection_url"] = "https://wrong.test/"
    elif invalid == "order":
        response["order_id"] = 999
    elif invalid == "live":
        response["payment_methods"][0]["live"] = True
    elif invalid == "expired":
        pieces = base64.b64decode(response["payment_keys"]["card"]).decode().split(".")
        claims = json.loads(
            base64.urlsafe_b64decode(pieces[1] + "=" * (-len(pieces[1]) % 4))
        )
        claims["exp"] = int((timezone.now() - timedelta(minutes=1)).timestamp())
        pieces[1] = (
            base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
        )
        response["payment_keys"]["card"] = base64.b64encode(
            ".".join(pieces).encode()
        ).decode()
    with patch(
        "core_apps.features.services.paymob_client.retrieve_intention",
        return_value=response,
    ) as retrieve, patch(
        "core_apps.features.services.paymob_client.order_transactions", return_value=[]
    ), patch(
        "core_apps.features.services.paymob_client.renew_intention", side_effect=renewal
    ) as renew, patch(
        "core_apps.features.services.paymob_client.create_intention"
    ) as create:
        if invalid and invalid != "expired":
            with pytest.raises(paymob_client.PaymobUnavailable):
                resume(buyer, payment.attempt, uuid.uuid4())
            payment.refresh_from_db()
            assert payment.status == "renewal_unknown"
        else:
            resumed = resume(buyer, payment.attempt, uuid.uuid4())
            assert resumed.checkout_session.expires_at > timezone.now()
            assert resumed.paymob_payment.status == "ready"
        assert retrieve.call_count == 1
        assert renew.call_count == (1 if invalid == "expired" else 0)
        create.assert_not_called()
    assert PaymentAttempt.objects.count() == 1
    assert PaymentReceipt.objects.count() == 0


from core_apps.features.tests.test_rental_phase5 import phase5_lease
from core_apps.advertising.tests.test_advertising_api import pending_ad, isolated_media


def pay_invoice(client, invoice):
    base = ROOT + f"billing/invoices/{invoice['id']}/"
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
    with patch(
        "core_apps.features.services.paymob_client.create_intention",
        side_effect=intention,
    ):
        response = body(
            client.post(
                base + "checkout/?projection=mobile_v1&platform=android",
                {
                    "expected_revision": invoice["revision"],
                    "quote_id": quote["id"],
                    "request_key": str(uuid.uuid4()),
                },
                format="json",
            )
        )
    payment = PaymobPayment.objects.get(attempt__id=response["id"])
    with patch(
        "core_apps.features.services.paymob_client.inquiry",
        return_value=snapshot(payment),
    ):
        reconcile(payment)
        reconcile(payment)
    return payment


def test_banner_capture_activates_public_placement_without_mock_payment(
    client, buyer, hosted
):
    from django.urls import reverse
    from core_apps.advertising.models import MockAdvertisementPayment
    from core_apps.advertising.services import is_publicly_eligible
    from core_apps.advertising.models import AdvertisingPlan
    from importlib import import_module

    # Transaction tests flush migration seed rows. Reuse the existing catalog
    # fixture explicitly so this test is independent of database/test order.
    seeded = next(
        row
        for row in import_module(
            "core_apps.advertising.migrations.0002_seed_advertising_plans"
        ).PLANS
        if row["id"] == "weekly"
    )
    AdvertisingPlan.objects.get_or_create(
        id=seeded["id"],
        defaults={
            **{key: value for key, value in seeded.items() if key != "id"},
            "currency": "EGP",
            "exponent": 2,
            "revision": "1",
            "active": True,
        },
    )
    ad, _, _ = pending_ad(client)
    invoice = body(
        client.post(
            ROOT + "billing/invoices/",
            {
                "purpose": "advertising",
                "workspace": "owner",
                "advertisement_id": str(ad.id),
                "request_key": str(uuid.uuid4()),
            },
            format="json",
        ),
        201,
    )
    pay_invoice(client, invoice)
    ad.refresh_from_db()
    assert ad.status == "active" and is_publicly_eligible(ad)
    assert not MockAdvertisementPayment.objects.filter(advertisement=ad).exists()
    response = client.get(reverse("advertising:tenant-home"))
    assert response.status_code == 200
    assert str(ad.id) in [item["id"] for item in response.json()["data"]["results"]]
    assert (
        PaymentReceipt.objects.count()
        == PaymentFulfillment.objects.filter(status="fulfilled").count()
        == 1
    )


def test_promotion_capture_activates_original_campaign(phase5_lease, hosted):
    from core_apps.features.catalog_models import PromotionOption
    from core_apps.features.models import BoostCampaign
    from core_apps.features.tests.test_rental_phase5 import client_for

    owner, _, lease = phase5_lease
    client = client_for(owner)
    option = PromotionOption.objects.create(
        id="hosted-promo",
        title_en="Boost",
        title_ar="ترويج",
        duration_days=7,
        amount_minor=100,
    )
    campaign = body(
        client.post(
            ROOT + "boost-campaigns/",
            {
                "property_id": str(lease.property.id),
                "option_id": option.id,
                "option_revision": option.revision,
                "request_key": str(uuid.uuid4()),
            },
            format="json",
        ),
        201,
    )
    invoice = body(
        client.get(ROOT + f"billing/invoices/{campaign['billing_invoices'][0]['id']}/")
    )
    pay_invoice(client, invoice)
    item = BoostCampaign.objects.get(id=campaign["id"])
    assert item.status == "active" and item.ends_at - item.starts_at == timedelta(
        days=7
    )
    assert PaymentReceipt.objects.count() == 1


@pytest.mark.parametrize("personal_active", [False, True])
def test_company_subscription_belongs_to_company_and_requires_current_mandate(
    client, buyer, plan, hosted, personal_active
):
    from core_apps.features.models import Company, CompanyMembership, CompanyMandate

    buyer.is_verified = True
    buyer.save()
    company = Company.objects.create(
        name="Sandbox", registration_number="sandbox", contact_email="org@example.test"
    )
    member = CompanyMembership.objects.create(
        company=company, user=buyer, is_admin=True, can_execute_payments=True
    )
    reviewer = get_user_model().objects.create_user(
        email="review@example.test", password="test"
    )
    operator = get_user_model().objects.create_user(
        email="operator@example.test", password="test"
    )
    CompanyMandate.objects.create(
        company=company,
        membership=member,
        kind="pay",
        state="approved",
        membership_revision=member.revision,
        valid_from=timezone.now() - timedelta(days=1),
        valid_until=timezone.now() + timedelta(days=7),
        limit_minor=100000,
        evidence_reference="synthetic",
        reason="QA",
        proposed_by=buyer,
        reviewed_by=reviewer,
        execution_reviewed_by=operator,
        execution_reference="synthetic",
        execution_verified_until=timezone.now() + timedelta(days=7),
    )
    if personal_active:
        from core_apps.features.models import RentInvoice

        original = RentInvoice.objects.create(
            purpose="subscription",
            payer=buyer,
            workspace="tenant",
            reference="PERSONAL-PAID",
            business_reference="subscription:personal-existing",
            due_date=timezone.localdate(),
            amount_minor=100,
            status="paid",
        )
        AccountSubscription.objects.create(
            user=buyer,
            plan=plan,
            invoice=original,
            workspace="tenant",
            starts_at=timezone.now() - timedelta(days=1),
            ends_at=timezone.now() + timedelta(days=10),
            plan_snapshot={},
        )
    plan.audience = "organization"
    plan.save()
    invoice = body(
        client.post(
            ROOT + "billing/invoices/",
            {
                "purpose": "subscription",
                "workspace": "tenant",
                "organization_id": str(company.id),
                "plan_id": str(plan.id),
                "plan_revision": plan.revision,
                "request_key": str(uuid.uuid4()),
            },
            format="json",
        ),
        201,
    )
    pay_invoice(client, invoice)
    assert (
        AccountSubscription.objects.get(organization=company).organization_id
        == company.pk
    )
    assert PaymentFulfillment.objects.get().status == "fulfilled"
    member.can_execute_payments = False
    member.save()
    response = client.post(
        ROOT + f"payment-attempts/{PaymentAttempt.objects.get().id}/resume/",
        {"request_key": str(uuid.uuid4())},
        format="json",
    )
    assert response.status_code == 403
