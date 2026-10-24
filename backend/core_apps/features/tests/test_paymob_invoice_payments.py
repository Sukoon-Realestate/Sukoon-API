import io
import uuid
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from core_apps.features.models import (
    CheckoutSession,
    IdempotencyRecord,
    LedgerTransaction,
    PaymobPayment,
    PaymentAttempt,
    PaymentReceipt,
    RentInvoice,
    MaintenanceRequest,
)
from core_apps.features.services import paymob_client
from core_apps.features.services.paymob_payments import reconcile
from core_apps.features.services.rental_phase3 import generate_billing_schedule
from core_apps.features.tests.test_rental_phase3 import phase3_lease, client_for
from core_apps.features.tests.test_rental_phase5 import phase5_lease
from core_apps.common.test_paymob_callbacks import TRANSACTION, SECRET, send

ROOT = "/api/v1/features/v1/"
pytestmark = pytest.mark.django_db


@pytest.fixture
def paymob(settings):
    settings.PAYMOB_INVOICE_CHECKOUT_ENABLED = True
    settings.PAYMOB_ALLOW_TRANSACTIONAL_TESTS = True
    settings.PAYMOB_API_KEY = "test-api-key"
    settings.PAYMOB_SECRET_KEY = "egy_sk_test_synthetic"
    settings.PAYMOB_PUBLIC_KEY = "egy_pk_test_synthetic"
    settings.PAYMOB_HMAC_SECRET = SECRET
    settings.PAYMOB_INTEGRATION_ID = "5991528"
    settings.PAYMOB_WEBHOOK_URL = (
        "https://api.sukoon.rent/api/v1/payments/paymob/webhook/"
    )
    settings.PAYMOB_RETURN_URL = (
        "https://api.sukoon.rent/api/v1/payments/paymob/return/"
    )
    return settings


def intention(payment, billing, return_url):
    # The transport must see a durable original identity and authoritative money.
    assert PaymobPayment.objects.filter(pk=payment.pk).exists()
    assert payment.attempt.payment_status == "pending"
    return {
        "id": "pi_test_synthetic",
        "intention_order_id": 456,
        "special_reference": payment.reference,
        "client_secret": "synthetic-secret",
        "intention_detail": {"amount": payment.attempt.amount_minor, "currency": "EGP"},
    }


def snapshot(payment, **changes):
    return {
        **TRANSACTION,
        "amount_cents": payment.attempt.amount_minor,
        "is_live": False,
        "order": {"id": 456, "merchant_order_id": payment.reference},
        **changes,
    }


def rental_checkout(phase3_lease):
    owner, tenant, lease = phase3_lease
    tenant.profile.phone_number = "+201010101010"
    tenant.profile.save()
    generate_billing_schedule(lease)
    invoice = lease.invoices.get()
    client = client_for(tenant)
    quoted = client.post(
        ROOT + f"rent-invoices/{invoice.id}/quote/",
        {"expected_revision": invoice.revision, "request_key": str(uuid.uuid4())},
        format="json",
    )
    assert quoted.status_code == 201, quoted.content
    quote = quoted.json()["data"]["resource"]
    command = {
        "invoice_id": str(invoice.id),
        "quote_id": quote["quote_id"],
        "expected_revision": invoice.revision,
        "request_key": str(uuid.uuid4()),
    }
    return client, invoice, command


def post_checkout(client, invoice, command):
    return client.post(
        ROOT + f"rent-invoices/{invoice.id}/checkout/", command, format="json"
    )


def test_checkout_is_pending_and_verification_captures_original_once(
    phase3_lease, paymob
):
    client, invoice, command = rental_checkout(phase3_lease)
    with patch(
        "core_apps.features.services.paymob_client.create_intention",
        side_effect=intention,
    ) as create:
        response = post_checkout(client, invoice, command)
        assert response.status_code == 201, response.content
        resource = response.json()["data"]["resource"]
        assert resource["provider_mode"] == "hosted" and resource["status"] == "pending"
        assert resource["navigation"]["return_state"]
        assert post_checkout(client, invoice, command).status_code == 201
        assert create.call_count == 1
    assert not PaymentReceipt.objects.exists()
    payment = PaymobPayment.objects.get()
    paymob.PAYMOB_INVOICE_CHECKOUT_ENABLED = False
    with patch(
        "core_apps.features.services.paymob_client.inquiry",
        return_value=snapshot(payment),
    ):
        for _ in range(2):
            reconcile(payment)
    invoice.refresh_from_db()
    assert (
        invoice.status == "paid"
        and invoice.applied_minor == payment.attempt.amount_minor
    )
    assert PaymentAttempt.objects.count() == PaymentReceipt.objects.count() == 1
    assert LedgerTransaction.objects.filter(kind="payment_captured").count() == 1
    assert not payment.attempt.invoice.lease.owner_payables.filter(
        payout_status="succeeded"
    ).exists()


def test_timeout_retains_original_and_never_resubmits_charge(phase3_lease, paymob):
    client, invoice, command = rental_checkout(phase3_lease)
    with patch(
        "core_apps.features.services.paymob_client.create_intention",
        side_effect=paymob_client.PaymobUnavailable(),
    ) as create:
        assert post_checkout(client, invoice, command).status_code == 503
        response = post_checkout(client, invoice, command)
        assert response.status_code == 201
        assert create.call_count == 1
    payment = PaymobPayment.objects.get()
    assert (
        payment.status == "outcome_unknown"
        and payment.attempt.payment_status == "pending"
    )
    other = {**command, "request_key": str(uuid.uuid4())}
    assert post_checkout(client, invoice, other).status_code == 409
    with patch(
        "core_apps.features.services.paymob_client.inquiry",
        return_value=snapshot(payment),
    ):
        call_command("reconcile_paymob_payments", stdout=io.StringIO())
    assert PaymentReceipt.objects.count() == 1
    lookup = client.get(
        ROOT + "payment-attempts/",
        {"invoice_id": str(invoice.id), "request_key": command["request_key"]},
    ).json()["data"]
    assert len(lookup["results"]) == 1 and not lookup["absence_confirmed"]


@pytest.mark.parametrize(
    "change",
    [
        {"amount_cents": 1},
        {"currency": "USD"},
        {"is_live": True},
        {"integration_id": 1},
        {"order": {"id": 987, "merchant_order_id": "wrong"}},
    ],
)
def test_provider_mismatch_never_pays_invoice(phase3_lease, paymob, change):
    client, invoice, command = rental_checkout(phase3_lease)
    with patch(
        "core_apps.features.services.paymob_client.create_intention",
        side_effect=intention,
    ):
        assert post_checkout(client, invoice, command).status_code == 201
    payment = PaymobPayment.objects.get()
    with patch(
        "core_apps.features.services.paymob_client.inquiry",
        return_value=snapshot(payment, **change),
    ):
        with pytest.raises(Exception) as error:
            reconcile(payment)
    assert error.value.get_codes() == "provider_payment_mismatch"
    assert not PaymentReceipt.objects.exists()
    invoice.refresh_from_db()
    assert invoice.applied_minor == 0
    payment.refresh_from_db()
    assert payment.status == "review"


def test_authorization_decline_and_pending_do_not_capture_or_allow_retry(
    phase3_lease, paymob
):
    client, invoice, command = rental_checkout(phase3_lease)
    with patch(
        "core_apps.features.services.paymob_client.create_intention",
        side_effect=intention,
    ):
        post_checkout(client, invoice, command)
    payment = PaymobPayment.objects.get()
    for values in [{"pending": True}, {"success": False}, {"is_auth": True}]:
        with patch(
            "core_apps.features.services.paymob_client.inquiry",
            return_value=snapshot(payment, **values),
        ):
            reconcile(payment)
        assert not PaymentReceipt.objects.exists()
    assert PaymentAttempt.objects.get().payment_status == "authorized"
    assert (
        post_checkout(
            client, invoice, {**command, "request_key": str(uuid.uuid4())}
        ).status_code
        == 409
    )


def test_signed_callback_queries_provider_and_browser_return_never_pays(
    phase3_lease, paymob
):
    from django.test import Client

    client, invoice, command = rental_checkout(phase3_lease)
    with patch(
        "core_apps.features.services.paymob_client.create_intention",
        side_effect=intention,
    ):
        post_checkout(client, invoice, command)
    payment = PaymobPayment.objects.get()
    with patch(
        "core_apps.features.services.paymob_client.inquiry",
        return_value=snapshot(payment),
    ) as query:
        obj = {**TRANSACTION, "amount_cents": payment.attempt.amount_minor}
        assert send(Client(), obj).status_code == 200
        assert send(Client(), obj).status_code == 200
        assert query.call_count == 2
    assert PaymentReceipt.objects.count() == 1


def test_digital_products_and_live_configuration_cannot_use_paymob(paymob):
    from core_apps.features.services.purchase_routing import routing_v1

    for purpose in ("subscription", "advertising", "promotion"):
        assert not routing_v1(purpose, "ios")["enabled"]
    paymob.PAYMOB_SECRET_KEY = "egy_sk_live_forbidden"
    assert not paymob_client.checkout_ready()
    paymob.PAYMOB_SECRET_KEY = "egy_sk_test_synthetic"
    paymob.RENTAL_RUNTIME_ENVIRONMENT = "production"
    assert not paymob_client.checkout_ready()


def test_maintenance_uses_hosted_checkout_and_service_liability(phase5_lease, paymob):
    from django.db import transaction
    from core_apps.features.services.billing_sources import maintenance_invoice

    owner, tenant, lease = phase5_lease
    tenant.profile.phone_number = "+201010101010"
    tenant.profile.save()
    item = MaintenanceRequest.objects.create(
        lease=lease,
        reporter=tenant,
        title="Repair",
        description="Repair",
        category="plumbing",
        priority="normal",
        cost_payer="tenant",
        proposed_cost_minor=2500,
        cost_version=1,
        approved_cost_version=1,
    )
    with transaction.atomic():
        invoice = maintenance_invoice(item, tenant)
    client = client_for(tenant)
    quote = client.post(
        ROOT + f"billing/invoices/{invoice.id}/quote/?platform=android",
        {"expected_revision": 1, "request_key": str(uuid.uuid4())},
        format="json",
    )
    assert quote.status_code == 201, quote.content
    command = {
        "expected_revision": 1,
        "quote_id": quote.json()["data"]["id"],
        "request_key": str(uuid.uuid4()),
    }
    with patch(
        "core_apps.features.services.paymob_client.create_intention",
        side_effect=intention,
    ):
        response = client.post(
            ROOT + f"billing/invoices/{invoice.id}/checkout/", command, format="json"
        )
    assert response.status_code == 200, response.content
    assert response.json()["data"]["checkout_session"]["provider_mode"] == "hosted"
    payment = PaymobPayment.objects.get()
    with patch(
        "core_apps.features.services.paymob_client.inquiry",
        return_value=snapshot(payment),
    ):
        reconcile(payment)
    assert LedgerTransaction.objects.filter(
        kind="hosted_purchase_capture", entries__account="service_funds_liability"
    ).exists()
    assert not LedgerTransaction.objects.filter(
        entries__account="purchase_revenue"
    ).exists()


def captured_payment(phase3_lease):
    client, invoice, command = rental_checkout(phase3_lease)
    with patch(
        "core_apps.features.services.paymob_client.create_intention",
        side_effect=intention,
    ):
        assert post_checkout(client, invoice, command).status_code == 201
    payment = PaymobPayment.objects.get()
    with patch(
        "core_apps.features.services.paymob_client.inquiry",
        return_value=snapshot(payment),
    ):
        reconcile(payment)
    payment.refresh_from_db()
    return payment


def approved_refund(payment):
    from core_apps.features.models import RefundRequest
    from core_apps.features.services.refunds import execute_refund

    refund = RefundRequest.objects.create(
        lease=payment.attempt.invoice.lease,
        payment_attempt=payment.attempt,
        requester=payment.attempt.payer,
        approved_by=payment.attempt.invoice.lease.owner,
        request_key=uuid.uuid4(),
        amount_minor=10000,
        refundable_balance_snapshot_minor=payment.attempt.amount_minor,
        status="approved",
        reason="Synthetic approved refund",
        allocations={"rent": 10000, "deposit": 0},
    )
    execute_refund(refund)
    refund.refresh_from_db()
    assert refund.status == "processing"
    return refund


def refund_proof(payment, **changes):
    return {
        **snapshot(payment),
        "id": 999,
        "is_refund": True,
        "parent_transaction": 123,
        "amount_cents": 10000,
        **changes,
    }


@pytest.mark.django_db(transaction=True)
def test_refund_is_dispatched_once_then_confirmed_before_accounting(
    phase3_lease, paymob
):
    from core_apps.features.models import PaymobRefund
    from core_apps.features.services.paymob_refunds import process

    paymob.PAYMOB_REFUNDS_ENABLED = True
    payment = captured_payment(phase3_lease)
    refund = approved_refund(payment)
    operation = PaymobRefund.objects.get(refund=refund)
    with patch(
        "core_apps.features.services.paymob_client.inquiry",
        side_effect=[snapshot(payment, refunded_amount_cents=0), refund_proof(payment)],
    ), patch(
        "core_apps.features.services.paymob_client.submit_refund",
        return_value={"id": 999},
    ) as submit:
        process(operation)
        process(operation)
        assert submit.call_count == 1
    refund.refresh_from_db()
    assert refund.status == "succeeded" and refund.provider_refund_id == "999"
    assert LedgerTransaction.objects.filter(kind="refund").count() == 1
    assert payment.attempt.invoice.payment_attempts.count() == 1
    with patch(
        "core_apps.features.services.paymob_client.inquiry",
        return_value=snapshot(
            payment, is_refunded=True, refunded_amount_cents=10000, is_settled=True
        ),
    ):
        reconcile(payment)
    payment.refresh_from_db()
    assert payment.status == "captured" and not payment.failure_code
    payment.attempt.refresh_from_db()
    assert payment.attempt.settlement_status == "settled"


@pytest.mark.django_db(transaction=True)
def test_unknown_refund_never_resubmits_and_can_recover_verified_original(
    phase3_lease, paymob
):
    from core_apps.features.models import PaymobRefund
    from core_apps.features.services.paymob_refunds import process

    paymob.PAYMOB_REFUNDS_ENABLED = True
    payment = captured_payment(phase3_lease)
    refund = approved_refund(payment)
    operation = PaymobRefund.objects.get(refund=refund)
    with patch(
        "core_apps.features.services.paymob_client.inquiry",
        return_value=snapshot(payment, refunded_amount_cents=0),
    ), patch(
        "core_apps.features.services.paymob_client.submit_refund",
        side_effect=paymob_client.PaymobUnavailable(),
    ) as submit:
        with pytest.raises(paymob_client.PaymobUnavailable):
            process(operation)
        process(operation)
        assert submit.call_count == 1
    refund.refresh_from_db()
    assert (
        refund.status == "processing"
        and not LedgerTransaction.objects.filter(kind="refund").exists()
    )
    with patch(
        "core_apps.features.services.paymob_client.inquiry",
        return_value=refund_proof(payment),
    ):
        call_command(
            "process_paymob_refunds",
            refund_id=str(refund.id),
            provider_transaction_id="999",
            stdout=io.StringIO(),
        )
    refund.refresh_from_db()
    assert refund.status == "succeeded"


@pytest.mark.django_db(transaction=True)
def test_refund_mismatch_cannot_finalize_money(phase3_lease, paymob):
    from core_apps.features.models import PaymobRefund
    from core_apps.features.services.paymob_refunds import process

    paymob.PAYMOB_REFUNDS_ENABLED = True
    payment = captured_payment(phase3_lease)
    refund = approved_refund(payment)
    operation = PaymobRefund.objects.get(refund=refund)
    with patch(
        "core_apps.features.services.paymob_client.inquiry",
        side_effect=[
            snapshot(payment, refunded_amount_cents=0),
            refund_proof(payment, parent_transaction=777),
        ],
    ), patch(
        "core_apps.features.services.paymob_client.submit_refund",
        return_value={"id": 999},
    ):
        with pytest.raises(Exception) as error:
            process(operation)
    assert error.value.get_codes() == "provider_payment_mismatch"
    refund.refresh_from_db()
    assert (
        refund.status == "processing"
        and not LedgerTransaction.objects.filter(kind="refund").exists()
    )


def test_mock_event_cannot_confirm_paymob_attempt(phase3_lease, paymob):
    from core_apps.features.rental_phase3_views_parts.owner_payables import (
        apply_fake_payment_event,
    )
    from core_apps.features.services.rental_phase2 import RentalConflict

    client, invoice, command = rental_checkout(phase3_lease)
    with patch(
        "core_apps.features.services.paymob_client.create_intention",
        side_effect=intention,
    ):
        post_checkout(client, invoice, command)
    with pytest.raises(RentalConflict) as error:
        apply_fake_payment_event(
            {
                "payment_attempt_id": str(PaymentAttempt.objects.get().id),
                "type": "payment.captured",
                "event_id": "forbidden-mock",
            }
        )
    assert error.value.get_codes() == "invalid_payment_domain"
    assert not PaymentReceipt.objects.exists()


@pytest.mark.django_db(transaction=True)
def test_two_devices_submit_only_one_paymob_intention(phase3_lease, paymob):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from django.db import connection, close_old_connections
    from django.contrib.auth import get_user_model

    if connection.vendor != "postgresql":
        pytest.skip("Requires real row locks.")
    paymob.PAYMOB_ALLOW_TRANSACTIONAL_TESTS = False
    client, invoice, command = rental_checkout(phase3_lease)
    tenant_id = phase3_lease[1].pk
    barrier = Barrier(2)

    def submit(_):
        close_old_connections()
        try:
            local = client_for(get_user_model().objects.get(pk=tenant_id))
            barrier.wait(timeout=10)
            return post_checkout(
                local, invoice, {**command, "request_key": str(uuid.uuid4())}
            ).status_code
        finally:
            close_old_connections()

    def committed_intention(payment, billing, redirect):
        assert not connection.in_atomic_block
        return intention(payment, billing, redirect)

    with patch(
        "core_apps.features.services.paymob_client.create_intention",
        side_effect=committed_intention,
    ) as create:
        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses = list(pool.map(submit, range(2)))
        assert sorted(statuses) == [201, 409]
        assert create.call_count == 1
    assert PaymobPayment.objects.count() == PaymentAttempt.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_two_workers_submit_only_one_provider_refund(phase3_lease, paymob):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from django.db import connection, close_old_connections
    from core_apps.features.models import PaymobRefund
    from core_apps.features.services.paymob_refunds import process

    if connection.vendor != "postgresql":
        pytest.skip("Requires real row locks.")
    paymob.PAYMOB_REFUNDS_ENABLED = True
    payment = captured_payment(phase3_lease)
    refund = approved_refund(payment)
    identity = PaymobRefund.objects.get(refund=refund).pk
    barrier = Barrier(2)

    def run(_):
        close_old_connections()
        try:
            item = PaymobRefund.objects.get(pk=identity)
            barrier.wait(timeout=10)
            process(item)
        finally:
            close_old_connections()

    def inquiry(_, transaction_id=None):
        return (
            refund_proof(payment)
            if str(transaction_id) == "999"
            else snapshot(payment, refunded_amount_cents=0)
        )

    with patch(
        "core_apps.features.services.paymob_client.inquiry", side_effect=inquiry
    ), patch(
        "core_apps.features.services.paymob_client.submit_refund",
        return_value={"id": 999},
    ) as submit:
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(run, range(2)))
        assert submit.call_count == 1
    refund.refresh_from_db()
    assert (
        refund.status == "succeeded"
        and LedgerTransaction.objects.filter(kind="refund").count() == 1
    )


def test_bound_browser_return_is_display_only_and_wrong_state_is_rejected(
    phase3_lease, paymob
):
    from django.test import Client
    from django.urls import reverse
    from core_apps.common.test_paymob_callbacks import query

    client, invoice, command = rental_checkout(phase3_lease)
    with patch(
        "core_apps.features.services.paymob_client.create_intention",
        side_effect=intention,
    ):
        post_checkout(client, invoice, command)
    attempt = PaymentAttempt.objects.get()
    params = {
        **query({**TRANSACTION, "amount_cents": attempt.amount_minor}),
        "state": attempt.checkout_session.return_state,
        "payment_attempt_id": str(attempt.id),
    }
    assert Client().get(reverse("paymob-return"), params).status_code == 200
    assert not PaymentReceipt.objects.exists()
    assert (
        Client().get(reverse("paymob-return"), {**params, "state": "wrong"}).status_code
        == 403
    )
    assert not PaymentReceipt.objects.exists()


def test_missing_contact_details_never_creates_an_external_attempt(
    phase3_lease, paymob
):
    client, invoice, command = rental_checkout(phase3_lease)
    tenant = phase3_lease[1]
    tenant.profile.phone_number = ""
    tenant.profile.save()
    with patch("core_apps.features.services.paymob_client.create_intention") as create:
        response = post_checkout(client, invoice, command)
    assert response.status_code == 400
    assert not create.called and not PaymobPayment.objects.exists()


def test_mock_payout_cannot_distribute_paymob_funds(phase3_lease, paymob):
    from core_apps.features.models import PayoutBatch, RentalPayout
    from core_apps.features.services.rental_lifecycle.provider_instructions import (
        execute_local_instruction,
    )
    from core_apps.features.services.rental_phase2 import RentalConflict

    payment = captured_payment(phase3_lease)
    payable = payment.attempt.invoice.owner_payables.get()
    batch = PayoutBatch.objects.create(
        approved_by=phase3_lease[0], request_key=uuid.uuid4()
    )
    payout = RentalPayout.objects.create(
        batch=batch,
        owner=phase3_lease[0],
        lease=phase3_lease[2],
        amount_minor=payable.net_minor,
    )
    payout.payables.add(payable)
    with pytest.raises(RentalConflict) as error:
        execute_local_instruction(
            kind="payout",
            subject=payout,
            request_key=uuid.uuid4(),
            payload={"amount_minor": payable.net_minor, "currency": "EGP"},
        )
    assert error.value.get_codes() == "provider_execution_required"
    payout.refresh_from_db()
    assert payout.status != "paid"
