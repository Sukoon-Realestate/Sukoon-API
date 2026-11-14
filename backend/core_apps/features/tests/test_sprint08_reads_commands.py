"""Commerce commands without HTTP, bounded page reads and legacy parity."""

import ast
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.exceptions import NotFound

from core_apps.features.models import (
    InvoiceLine,
    PaymentAttempt,
    PaymentQuote,
    RentInvoice,
    SubscriptionPlan,
    RentalPayout,
    PayoutBatch,
    PayoutAuditEvent,
)
from core_apps.features.services.billing_reads import (
    invoice_read_queryset,
    prepare_invoice_page,
)
from core_apps.features.services.billing_projection import invoice_payload
from core_apps.features.services.rental_payment_commands import (
    quote_rent,
    checkout_rent,
)
from core_apps.features.tests import test_rental_phase3 as rental_fixtures

phase3_lease = rental_fixtures.phase3_lease

pytestmark = pytest.mark.django_db


def test_rental_quote_checkout_and_receipt_replay_without_request(phase3_lease):
    from core_apps.features.services.rental_phase3 import generate_billing_schedule
    from core_apps.features.models import PrivateAccessRevocation

    _, actor, lease = phase3_lease
    invoice = list(generate_billing_schedule(lease))[0].invoice
    quote_body = {"expected_revision": invoice.revision, "request_key": str(uuid4())}
    quote = quote_rent(actor, None, quote_body, "", invoice.id)
    assert quote.status == 201
    assert quote_rent(actor, None, quote_body, "", invoice.id).data == quote.data
    command = {
        "invoice_id": str(invoice.id),
        "quote_id": quote.data["resource"]["quote_id"],
        "expected_revision": invoice.revision,
        "request_key": str(uuid4()),
    }
    result = checkout_rent(actor, None, command, "", invoice.id)
    assert result.status == 201
    assert checkout_rent(actor, None, command, "", invoice.id).data == result.data
    assert PaymentAttempt.objects.filter(invoice=invoice).count() == 1
    PrivateAccessRevocation.objects.create(lease=lease, user=actor, reason="test")
    with pytest.raises(NotFound):
        quote_rent(
            actor, None, {**quote_body, "request_key": str(uuid4())}, "", invoice.id
        )


@pytest.mark.parametrize("size", [5, 40])
@pytest.mark.parametrize("platform", ["web", "ios", "android"])
def test_mixed_invoice_page_has_bounded_queries_and_identical_projection(
    size, platform, user
):
    plan = SubscriptionPlan.objects.create(
        name_en="Test", name_ar="اختبار", workspace="tenant", amount_minor=500
    )
    purposes = [
        "subscription",
        "advertising",
        "promotion",
        "maintenance",
        "deposit",
        "settlement",
        "adjustment",
    ]
    invoices = []
    for index in range(size):
        purpose = purposes[index % len(purposes)]
        invoice = RentInvoice.objects.create(
            payer=user,
            purpose=purpose,
            workspace="tenant",
            reference=str(uuid4()),
            business_reference=str(uuid4()),
            amount_minor=500,
            status="paid" if index % 2 else "due",
            due_date=timezone.localdate(),
            purchase_snapshot={"id": str(plan.id)} if purpose == "subscription" else {},
        )
        InvoiceLine.objects.create(
            invoice=invoice,
            line_type=purpose,
            description="test",
            amount_minor=500,
            source={"description_ar": "اختبار"},
        )
        quote = PaymentQuote.objects.create(
            invoice=invoice,
            request_key=uuid4(),
            invoice_revision=1,
            payer_amount_minor=500,
            policy_version="test",
            fingerprint="test",
            expires_at=timezone.now() + timedelta(minutes=5),
        )
        PaymentAttempt.objects.create(
            invoice=invoice,
            payer=user,
            quote=quote,
            request_key=uuid4(),
            invoice_revision=1,
            policy_version="test",
            quote_fingerprint="test",
            amount_minor=500,
            payment_status="captured" if index % 2 else "failed",
            provider_attempt_id="mock-test",
        )
        invoices.append(invoice)
    expected = [
        invoice_payload(item, user, "ar", platform=platform) for item in invoices
    ]
    with CaptureQueriesContext(connection) as queries:
        page = prepare_invoice_page(
            invoice_read_queryset(
                RentInvoice.objects.filter(pk__in=[item.pk for item in invoices])
            ).order_by("pk")
        )
    assert len(queries) <= 7
    with CaptureQueriesContext(connection) as projection_queries:
        actual = {
            str(item.id): invoice_payload(item, user, "ar", platform=platform)
            for item in page
        }
    assert len(projection_queries) == 0
    assert actual == {str(item.id): value for item, value in zip(invoices, expected)}


@pytest.mark.parametrize("size", [5, 40])
def test_compact_payouts_do_not_load_long_audit_history(size, phase3_lease):
    from core_apps.features.services.financial_lists import (
        financial_list,
        financial_summary,
    )

    owner, _, lease = phase3_lease
    for _ in range(size):
        batch = PayoutBatch.objects.create(approved_by=owner, request_key=uuid4())
        payout = RentalPayout.objects.create(
            batch=batch, owner=owner, lease=lease, amount_minor=100
        )
        PayoutAuditEvent.objects.bulk_create(
            [
                PayoutAuditEvent(payout=payout, actor=owner, action="approved")
                for _ in range(40)
            ]
        )
    with CaptureQueriesContext(connection) as queries:
        page = list(financial_list(owner, "payouts", workspace="owner")[:20])
        values = [financial_summary(item, "payouts") for item in page]
    assert len(queries) == 1
    assert len(values) == min(size, 20)
    assert all("history" not in item for item in values)


def test_money_domain_has_no_view_request_or_renderer_imports():
    root = Path(__file__).resolve().parents[1] / "services"
    files = [
        "money_access",
        "money_projection",
        "rental_payment_commands",
        "payout_commands",
        "refund_commands",
        "settlement_commands",
        "settlement_projection",
        "payment_events",
        "payable_eligibility",
        "payout_authority",
        "billing_reads",
        "financial_lists",
        "rental_events",
        "signing_completion",
        "change_signing_completion",
        "rental_provider_events",
        "operation_receipts",
        "promotion_commands",
    ]
    for name in files:
        tree = ast.parse((root / f"{name}.py").read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert not any(
                    token in (node.module or "")
                    for token in [
                        "views",
                        "renderers",
                        "rest_framework.response",
                        "features.http",
                    ]
                ), (name, node.module)
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                assert node.value.id != "request", (name, node.attr)


@pytest.mark.parametrize("size", [5, 40])
@pytest.mark.parametrize("kind", ["refunds", "disputes"])
def test_compact_refund_dispute_histories_are_not_loaded(size, kind, phase3_lease):
    from core_apps.features.models import RefundRequest, RentalDispute, RentalAuditEvent
    from core_apps.features.services.financial_lists import (
        financial_list,
        financial_summary,
    )

    owner, tenant, lease = phase3_lease
    invoice = RentInvoice.objects.create(
        lease=lease,
        payer=tenant,
        purpose="rent",
        reference=str(uuid4()),
        due_date=timezone.localdate(),
        amount_minor=10000,
    )
    quote = PaymentQuote.objects.create(
        invoice=invoice,
        request_key=uuid4(),
        invoice_revision=1,
        payer_amount_minor=10000,
        policy_version="test",
        fingerprint="test",
        expires_at=timezone.now() + timedelta(minutes=5),
    )
    attempt = PaymentAttempt.objects.create(
        invoice=invoice,
        payer=tenant,
        quote=quote,
        request_key=uuid4(),
        invoice_revision=1,
        policy_version="test",
        quote_fingerprint="test",
        amount_minor=10000,
        payment_status="captured",
    )
    for _ in range(size):
        if kind == "refunds":
            item = RefundRequest.objects.create(
                lease=lease,
                payment_attempt=attempt,
                requester=tenant,
                amount_minor=1,
                refundable_balance_snapshot_minor=10000,
                request_key=uuid4(),
                reason="test",
            )
            RentalAuditEvent.objects.bulk_create(
                [
                    RentalAuditEvent(
                        actor=tenant,
                        subject_kind="refundrequest",
                        subject_id=item.id,
                        subject_revision=number + 1,
                        action="refund_requested",
                    )
                    for number in range(40)
                ]
            )
        else:
            RentalDispute.objects.create(
                lease=lease,
                opened_by=tenant,
                subject_kind="invoice",
                subject_id=invoice.id,
                reason="test",
                responses=[{"note": "historical test response"} for _ in range(40)],
            )
    with CaptureQueriesContext(connection) as queries:
        page = list(financial_list(owner, kind, workspace="owner")[:20])
        result = [financial_summary(item, kind) for item in page]
    assert len(queries) == 1
    assert len(result) == min(size, 20)
    assert all("history" not in item and "responses" not in item for item in result)
    if kind == "disputes":
        assert all("responses" in item.get_deferred_fields() for item in page)
    else:
        assert all(item["payment_attempt_id"] == str(attempt.id) for item in result)


@pytest.mark.mvp_deferred
def test_compact_collection_paginates_without_duplicates_and_keeps_legacy_shape(
    phase3_lease,
):
    from core_apps.features.tests.test_rental_phase3 import client_for

    owner, _, lease = phase3_lease
    for _ in range(25):
        batch = PayoutBatch.objects.create(approved_by=owner, request_key=uuid4())
        RentalPayout.objects.create(
            batch=batch, owner=owner, lease=lease, amount_minor=100
        )
    api = client_for(owner)
    url = "/api/v1/features/v1/payouts/"
    first = api.get(url, {"workspace": "owner", "projection": "compact_v1"})
    assert first.status_code == 200
    data = first.data
    assert len(data["results"]) == 20 and data["count"] == 25 and data["next"]
    second = api.get(data["next"])
    assert second.status_code == 200 and len(second.data["results"]) == 5
    assert {row["id"] for row in data["results"]}.isdisjoint(
        row["id"] for row in second.data["results"]
    )
    legacy = api.get(url, {"workspace": "owner"})
    assert legacy.status_code == 200 and len(legacy.data["results"]) == 25
    assert legacy.data["next"] is None
