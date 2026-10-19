"""Historical payment discovery does not depend on a local request key."""

import uuid
import pytest
from rest_framework.test import APIClient
from core_apps.features.models import (
    CompanyMembership,
    PaymentAttempt,
    PrivateAccessRevocation,
)
from core_apps.features.tests.test_chargeback_resolution import disputed
from core_apps.features.tests.test_rental_phase3 import phase3_lease, client_for
from core_apps.features.tests.test_company_tenancy import (
    cycle,
    company_setup,
    rental_participants,
    policy,
    agreement,
    signed_agreement,
    active_agreement,
    authenticated,
    person,
    expose_unexpected_exceptions,
)

API = "/api/v1/features/v1/rent-invoices/"


@pytest.mark.django_db
def test_terminal_history_is_readable_without_provider_or_recovery_key(
    disputed, settings
):
    attempt = disputed.payment_attempt
    invoice = attempt.invoice
    settings.RENTAL_PROVIDER_BACKEND = "disabled"
    before = (invoice.revision, invoice.applied_minor, invoice.payment_attempts.count())
    for user in [attempt.payer, invoice.lease.owner]:
        result = client_for(user).get(API + f"{invoice.id}/payments/")
        assert result.status_code == 200, result.data
        row = result.data["results"][0]
        assert row["payment_attempt_id"] == str(attempt.id)
        assert row["payment_status"] == "chargedback"
        assert row["chargeback"]["id"] == str(disputed.id)
        assert row["chargeback"]["resolved"] is False
        assert "hosted_url" not in row and "active_session" not in row
    invoice.refresh_from_db()
    assert (
        invoice.revision,
        invoice.applied_minor,
        invoice.payment_attempts.count(),
    ) == before


@pytest.mark.django_db
def test_history_pages_remain_invoice_scoped_and_stably_ordered(disputed):
    original = disputed.payment_attempt
    for _ in range(3):
        PaymentAttempt.objects.create(
            invoice=original.invoice,
            payer=original.payer,
            quote=original.quote,
            request_key=uuid.uuid4(),
            invoice_revision=original.invoice_revision,
            amount_minor=original.amount_minor,
            currency="EGP",
            payment_status="failed",
        )
    client = client_for(original.payer)
    path = API + f"{original.invoice.id}/payments/"
    first = client.get(path, {"page_size": 2, "invoice_id": str(uuid.uuid4())})
    second = client.get(path, {"page_size": 2, "page": 2})
    assert first.status_code == second.status_code == 200
    rows = first.data["results"] + second.data["results"]
    assert first.data["count"] == 4 and first.data["total_pages"] == 2
    assert len({row["payment_attempt_id"] for row in rows}) == 4
    assert all(row["invoice_id"] == str(original.invoice.id) for row in rows)
    assert rows[-1]["payment_attempt_id"] == str(original.id)
    assert client.get(path, {"page": 3}).status_code == 404


@pytest.mark.django_db
@pytest.mark.parametrize("role", ["owner", "coordinator", "signer", "payer"])
def test_current_commercial_actor_reads_company_history(active_agreement, role):
    actors, tenancy = active_agreement
    invoice = tenancy.lease.invoices.get()
    result = authenticated(actors[role]).get(API + f"{invoice.id}/payments/")
    assert result.status_code == 200, result.data
    assert result.data["count"] == 1
    assert result.data["results"][0]["payment_status"] == "captured"


@pytest.mark.django_db
@pytest.mark.parametrize("role", ["employee", "colleague", "approver"])
def test_company_membership_without_commercial_access_cannot_read_history(
    active_agreement, role
):
    actors, tenancy = active_agreement
    invoice = tenancy.lease.invoices.get()
    result = authenticated(actors[role]).get(API + f"{invoice.id}/payments/")
    assert result.status_code == 404


@pytest.mark.django_db
def test_removed_coordinator_and_revoked_private_access_lose_history(active_agreement):
    actors, tenancy = active_agreement
    invoice = tenancy.lease.invoices.get()
    path = API + f"{invoice.id}/payments/"
    client = authenticated(actors["coordinator"])
    assert client.get(path).status_code == 200
    CompanyMembership.objects.filter(
        company=actors["company"], user=actors["coordinator"]
    ).update(is_active=False)
    assert client.get(path).status_code == 404
    PrivateAccessRevocation.objects.create(
        lease=tenancy.lease, user=actors["payer"], reason="Synthetic privacy revocation"
    )
    assert authenticated(actors["payer"]).get(path).status_code == 404
    assert authenticated(person("history-outsider")).get(path).status_code == 404
    assert APIClient().get(path).status_code in {401, 403}


@pytest.mark.django_db
def test_signed_unpaid_company_invoice_has_successful_empty_history(signed_agreement):
    actors, tenancy = signed_agreement
    invoice = tenancy.lease.invoices.get()
    result = authenticated(actors["payer"]).get(API + f"{invoice.id}/payments/")
    assert result.status_code == 200, result.data
    assert result.data["count"] == 0 and result.data["results"] == []
