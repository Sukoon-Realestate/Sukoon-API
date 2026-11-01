from datetime import timedelta
import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from core_apps.features.tests.test_reputation import actors, stay
from core_apps.features.models import (
    OwnerRentalAchievement,
    OwnerMilestone,
    RentInvoice,
)
from core_apps.features.services.owner_achievements import level, summary, acknowledge
from core_apps.features.services.reputation.public_summary import payment_reliability


@pytest.mark.parametrize(
    "count,tier",
    [
        (0, "starter"),
        (1, "starter"),
        (2, "bronze"),
        (5, "bronze"),
        (6, "silver"),
        (15, "silver"),
        (16, "gold"),
        (30, "gold"),
        (31, "diamond"),
    ],
)
def test_level_boundaries(count, tier):
    assert level(count) == tier


@pytest.mark.django_db
def test_achievement_once_per_tenancy_and_acknowledgment(actors):
    owner = actors[0]
    first = stay(actors)
    first.activated_at = timezone.now()
    first.save()
    first.save()
    renewal = stay(actors, root=first.tenancy_root_id)
    renewal.activated_at = timezone.now()
    renewal.save()
    assert summary(owner)["successful_rentals"] == 1
    second = stay(actors)
    second.activated_at = timezone.now()
    second.save()
    assert summary(owner)["tier"] == "bronze"
    event = summary(owner)["pending_event"]["id"]
    acknowledge(owner, event)
    acknowledge(owner, event)
    assert summary(owner)["pending_event"] is None
    OwnerRentalAchievement.objects.filter(lease=second).update(revoked=True)
    assert summary(owner)["tier"] == "starter"


@pytest.mark.django_db
def test_public_profile_omits_account_and_hidden_properties(actors):
    owner, *_, prop = actors
    client = APIClient()
    response = client.get(f"/api/v1/properties/owners/{owner.id}/profile/")
    assert response.status_code == 200
    assert owner.email.encode() not in response.content
    assert b"account_details" not in response.content
    prop.status = "pending"
    prop.save()
    response = client.get(f"/api/v1/properties/owners/{owner.id}/profile/")
    assert response.status_code == 200
    # DRF data is the public projection before the renderer wraps it.
    assert response.data["listing_count"] == 0


@pytest.mark.django_db
def test_payment_summary_deferral_and_insufficient_sample(actors):
    lease = stay(actors)
    now = timezone.now()
    for number in range(3):
        RentInvoice.objects.create(
            lease=lease,
            reference=f"reputation-{number}",
            due_date=now.date(),
            due_at=now - timedelta(days=2),
            amount_minor=1000,
            status="due",
            deferred_until=now + timedelta(days=1) if number == 0 else None,
        )
    result = payment_reliability("person_tenant", actors[1].id, now=now)
    assert result["sample_count"] == 2
    assert result["on_time_percentage"] is None
    assert result["late_count"] is None


@pytest.mark.django_db
def test_company_invoices_never_affect_employee_reputation(actors):
    from core_apps.features.models import Company

    lease = stay(actors)
    company = Company.objects.create(
        name="Test Company",
        registration_number="test",
        contact_email="test@example.test",
    )
    lease.renter_company = company
    lease.tenant = None
    lease.save()
    now = timezone.now()
    for number in range(3):
        RentInvoice.objects.create(
            lease=lease,
            reference=f"company-reputation-{number}",
            due_date=now.date(),
            due_at=now - timedelta(days=2),
            amount_minor=1000,
            status="due",
        )
    personal = payment_reliability("person_tenant", actors[1].id, now=now)
    organization = payment_reliability("organization_renter", company.id, now=now)
    assert personal["sample_count"] == 0
    assert organization["sample_count"] == 3
    assert organization["on_time_percentage"] == 0


@pytest.mark.django_db
def test_disputed_invoice_is_excluded_but_unrelated_support_case_is_not(actors):
    from core_apps.features.models import RentalDispute, RentalOperationalCase

    lease = stay(actors)
    now = timezone.now()
    invoices = [
        RentInvoice.objects.create(
            lease=lease,
            reference=f"dispute-reputation-{number}",
            due_date=now.date(),
            due_at=now - timedelta(days=2),
            amount_minor=1000,
            status="due",
        )
        for number in range(4)
    ]
    RentalDispute.objects.create(
        lease=lease,
        opened_by=actors[1],
        subject_kind="invoice",
        subject_id=invoices[0].id,
        reason="Test disputed amount",
    )
    RentalOperationalCase.objects.create(
        lease=lease,
        source_key="test-unrelated",
        kind="maintenance",
        next_action="Inspect",
        due_at=now,
        reason="Test maintenance",
    )
    result = payment_reliability("person_tenant", actors[1].id, now=now)
    assert result["sample_count"] == 3
    assert result["excluded_count"] == 1
    assert result["overdue_unpaid_count"] == 3


@pytest.mark.django_db
def test_old_due_date_with_recent_agreed_deferral_uses_effective_date(actors):
    lease = stay(actors)
    now = timezone.now()
    RentInvoice.objects.create(
        lease=lease,
        reference="deferred-old",
        due_date=(now - timedelta(days=500)).date(),
        due_at=now - timedelta(days=500),
        deferred_until=now - timedelta(days=1),
        amount_minor=1000,
        status="due",
    )
    assert (
        payment_reliability("person_tenant", actors[1].id, now=now)["sample_count"] == 1
    )


@pytest.mark.django_db
def test_public_summary_rejects_missing_or_inactive_subject(actors):
    import uuid

    client = APIClient()
    base = "/api/v1/features/v1/reviews/subjects/person_tenant/"
    assert client.get(f"{base}{actors[1].id}/public-summary/").status_code == 200
    assert client.get(f"{base}{uuid.uuid4()}/public-summary/").status_code == 404
    tenant = actors[1]
    tenant.is_active = False
    tenant.save()
    assert client.get(f"{base}{tenant.id}/public-summary/").status_code == 404


@pytest.mark.django_db
def test_milestone_acknowledgment_cannot_cross_accounts(actors):
    from django.http import Http404

    milestone = OwnerMilestone.objects.create(
        owner=actors[0], tier="bronze", threshold=2
    )
    with pytest.raises(Http404):
        acknowledge(actors[1], milestone.id)
    milestone.refresh_from_db()
    assert milestone.acknowledged_at is None


@pytest.mark.django_db
def test_payment_percentage_uses_confirmed_full_payment_and_masks_small_samples(actors):
    import uuid
    from core_apps.features.models import (
        PaymentQuote,
        PaymentAttempt,
        InvoicePaymentAllocation,
    )

    lease = stay(actors)
    now = timezone.now()
    due = now - timedelta(days=2)
    for number in range(3):
        invoice = RentInvoice.objects.create(
            lease=lease,
            reference=f"paid-reputation-{number}",
            due_date=due.date(),
            due_at=due,
            amount_minor=1000,
            status="paid",
        )
        quote = PaymentQuote.objects.create(
            invoice=invoice,
            request_key=uuid.uuid4(),
            invoice_revision=1,
            payer_amount_minor=1000,
            policy_version="test",
            fingerprint="a" * 64,
            expires_at=now,
        )
        attempt = PaymentAttempt.objects.create(
            invoice=invoice,
            quote=quote,
            payer=actors[1],
            request_key=uuid.uuid4(),
            invoice_revision=1,
            policy_version="test",
            quote_fingerprint="a" * 64,
            amount_minor=1000,
            payment_status="captured",
            confirmed_at=(
                due + timedelta(hours=1) if number == 2 else due - timedelta(hours=1)
            ),
        )
        InvoicePaymentAllocation.objects.create(
            invoice=invoice, payment_attempt=attempt, amount_minor=1000
        )
    result = payment_reliability("person_tenant", actors[1].id, now=now)
    assert result["sample_count"] == 3
    assert result["on_time_percentage"] == 66.7
    assert result["late_count"] == 1
    assert result["overdue_unpaid_count"] == 0
