"""Payment rejection and owner-list work do not issue a query per advertisement."""

from datetime import timedelta
from uuid import uuid4

import pytest
from django.urls import reverse
from django.utils import timezone

from tools.qa.performance import measured

from core_apps.advertising.models import Advertisement, AdvertisementMedia, AdvertisementOperation

pytestmark = [pytest.mark.django_db, pytest.mark.mvp_deferred]


def ads(owner, size):
    rows = []
    for _ in range(size):
        op = AdvertisementOperation.objects.create(owner=owner, operation_id=str(uuid4()), state="found")
        row = Advertisement.objects.create(
            owner=owner,
            operation=op,
            title="Synthetic",
            plan_snapshot={},
            status="active",
            starts_at=timezone.now() - timedelta(days=1),
            ends_at=timezone.now() + timedelta(days=1),
        )
        AdvertisementMedia.objects.create(
            advertisement=row, banner="synthetic.png", size_bytes=10, sha256="0" * 64, content_type="image/png"
        )
        rows.append(row)
    return rows


@pytest.mark.parametrize("size", [1, 10, 100])
def test_payment_rejection_page_is_set_based(size, user, api_client):
    ads(user, size)
    response, report = measured(
        "advertising-rejection", size, lambda: api_client.get(reverse("advertising:tenant-home"))
    )
    assert response.status_code == 200
    assert response.data["data"]["results"] == []
    assert report["queries"] <= 1
    assert report["storage_exists_calls"] == 0
    assert report["http_calls"] == 0


@pytest.mark.parametrize("size", [1, 10, 100])
def test_owner_page_batches_invoice_links_and_excludes_other_owners(size, user, another_user, auth_client):
    owned = ads(user, size)
    ads(another_user, 2)
    response, report = measured(
        "advertising-owner",
        size,
        lambda: auth_client.get(reverse("advertising:owner-advertisement-list"), {"page_size": 100}),
    )
    assert response.status_code == 200
    assert response.data["data"]["count"] == size
    assert {row["id"] for row in response.data["data"]["results"]} == {str(row.id) for row in owned}
    assert all(row["billing_invoices"] == [] for row in response.data["data"]["results"])
    assert report["queries"] <= 3


@pytest.mark.parametrize("proof", ["current", "foreign_payer", "uncaptured", "unfulfilled", "unpaid", "wrong_subject"])
def test_prepared_fulfillment_preserves_every_proof_requirement(proof, user, another_user):
    from core_apps.advertising.selectors import with_fulfillment
    from core_apps.features.models import RentInvoice, PaymentQuote, PaymentAttempt, PaymentFulfillment

    ad = ads(user, 1)[0]
    invoice = RentInvoice.objects.create(
        purpose="advertising",
        payer=another_user if proof == "foreign_payer" else user,
        purchase_snapshot={"subject_id": str(uuid4() if proof == "wrong_subject" else ad.id)},
        reference=str(uuid4()),
        business_reference=str(uuid4()),
        due_date=timezone.localdate(),
        amount_minor=100,
        status="due" if proof == "unpaid" else "paid",
    )
    quote = PaymentQuote.objects.create(
        invoice=invoice,
        request_key=uuid4(),
        invoice_revision=1,
        payer_amount_minor=100,
        policy_version="test",
        fingerprint="test",
        expires_at=timezone.now() + timedelta(minutes=1),
    )
    attempt = PaymentAttempt.objects.create(
        invoice=invoice,
        payer=user,
        quote=quote,
        request_key=uuid4(),
        invoice_revision=1,
        policy_version="test",
        quote_fingerprint="test",
        amount_minor=100,
        payment_status="authorized" if proof == "uncaptured" else "captured",
    )
    PaymentFulfillment.objects.create(
        invoice=invoice, attempt=attempt, status="pending" if proof == "unfulfilled" else "fulfilled"
    )
    assert with_fulfillment(Advertisement.objects.all()).get(pk=ad.pk).prepared_fulfillment == (proof == "current")
