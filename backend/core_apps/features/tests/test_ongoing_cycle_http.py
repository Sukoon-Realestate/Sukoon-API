"""Continue a paid tenancy into billing, agreed changes and a paid renewal."""

import json
import os
from datetime import date, datetime, timedelta, timezone as dt_timezone
from pathlib import Path

import pytest
from django.db import connection
from django.utils import timezone

from core_apps.features.models import Lease, OwnerPayable, RentalChange
from core_apps.features.tasks import process_rental_changes, run_rental_billing_cycle
from . import test_rental_phase2 as initial_cycle
from .cycle_http_sources import mutate
from .test_full_cycle_http import HttpActor
from .test_funded_settlement import command
from .test_rental_phase2 import rental_participants

API = "/api/v1/features/v1/"


def pay_invoice(actor, invoice):
    quote = mutate(
        actor,
        f"rent-invoices/{invoice.id}/quote/",
        command(invoice.revision, decision="quote"),
        201,
    )
    checkout = mutate(
        actor,
        f"rent-invoices/{invoice.id}/checkout/",
        command(
            invoice.revision,
            invoice_id=str(invoice.id),
            quote_id=quote["quote_id"],
        ),
        201,
    )
    descriptor = checkout["mock_completion"]
    captured = actor.post(
        descriptor["path"], command(descriptor["expected_revision"], event="captured")
    )
    assert captured.status_code == 200, captured.data
    settled = actor.post(
        descriptor["path"],
        command(captured.data["resource"]["revision"], event="settled"),
    )
    assert settled.status_code == 200, settled.data
    invoice.refresh_from_db()
    assert invoice.status == "paid"
    return invoice.owner_payables.get()


def sign_change(owner, tenant, lease, kind, terms, effective):
    item = mutate(
        owner,
        f"leases/{lease.id}/{kind}/",
        command(
            lease_revision=lease.revision,
            terms=terms,
            effective_on=str(effective),
            reason="Both participants agreed these exact terms",
            evidence_ids=[],
        ),
        201,
    )
    item = mutate(
        tenant,
        f"{kind}/{item['id']}/respond/",
        command(item["revision"], action="accept"),
    )
    submit_body = command(item["revision"], action="submit_for_signature")
    path = f"{kind}/{item['id']}/submit-for-signature/"
    item = mutate(owner, path, submit_body)
    assert mutate(owner, path, submit_body) == item
    sessions = []
    for actor in (owner, tenant):
        body = command(
            item["revision"],
            document_id=item["document_id"],
            document_hash=item["document_hash"],
        )
        path = f"{kind}/{item['id']}/signing-session/"
        sessions.append((actor, path, body, mutate(actor, path, body, 201)))
    for actor, _, _, session in sessions:
        descriptor = session["mock_completion"]
        signed = actor.post(
            descriptor["path"], command(descriptor["expected_revision"])
        )
        assert signed.status_code == 200, signed.data
    for actor, path, body, session in sessions:
        assert mutate(actor, path, body, 201) == session
    return RentalChange.objects.get(id=item["id"])


@pytest.mark.django_db(transaction=True)
def test_paid_tenancy_month_end_extension_amendment_and_renewal_over_http(
    rental_participants, live_server, monkeypatch
):
    if connection.vendor != "postgresql":
        pytest.skip("Connected HTTP/row-lock evidence requires PostgreSQL")
    clock = [datetime(2026, 1, 21, 12, tzinfo=dt_timezone.utc)]
    monkeypatch.setattr(timezone, "now", lambda: clock[0])
    owner, tenant, stranger, _, _ = rental_participants
    actors = {
        user.pk: HttpActor(live_server.url, user) for user in (owner, tenant, stranger)
    }
    monkeypatch.setattr(initial_cycle, "authenticated", lambda user: actors[user.pk])
    initial_cycle.run_interest_to_activation(
        rental_participants, artifact_name="django-ongoing-start-contract.json"
    )
    lease = Lease.objects.get()
    owner_api, tenant_api = actors[owner.pk], actors[tenant.pk]
    assert lease.start_date == date(2026, 1, 31)
    periods = list(lease.billing_periods.order_by("sequence"))
    assert [(item.start, item.end_exclusive) for item in periods] == [
        (date(2026, 1, 31), date(2026, 2, 28)),
        (date(2026, 2, 28), date(2026, 3, 3)),
    ]
    initial_invoice = lease.invoices.get()
    original_financials = (
        initial_invoice.revision,
        initial_invoice.receipt_id,
        initial_invoice.charges_minor,
    )
    clock[0] = datetime(2026, 2, 22, 12, tzinfo=dt_timezone.utc)
    assert run_rental_billing_cycle()["issued"] == 1
    assert run_rental_billing_cycle()["issued"] == 0
    recurring = lease.invoices.exclude(id=initial_invoice.id).get()
    original_due = recurring.due_at
    extension = mutate(
        tenant_api,
        f"leases/{lease.id}/payment-extension-requests/",
        command(
            invoice_id=str(recurring.id),
            lease_revision=lease.revision,
            reason="Agreed payment extension",
            requested_date="2026-03-02",
        ),
        201,
    )
    extension = mutate(
        owner_api,
        f"payment-extension-requests/{extension['id']}/respond/",
        command(extension["revision"], action="accept"),
    )
    assert extension["status"] == "applied"
    recurring.refresh_from_db()
    assert recurring.due_at == original_due and recurring.deferred_until > original_due
    recurring_payable = pay_invoice(tenant_api, recurring)
    assert recurring_payable.commission_minor == 0

    lease.refresh_from_db()
    amendment_terms = {**lease.terms, "termination_policy": {"notice_days": 20}}
    amendment = sign_change(
        owner_api, tenant_api, lease, "amendments", amendment_terms, date(2026, 2, 22)
    )
    assert process_rental_changes()["applied"] == 1
    assert process_rental_changes()["applied"] == 0
    lease.refresh_from_db()
    assert lease.terms == amendment_terms
    assert amendment.previous_terms["termination_policy"]["notice_days"] == 30
    initial_invoice.refresh_from_db()
    assert (
        initial_invoice.revision,
        initial_invoice.receipt_id,
        initial_invoice.charges_minor,
    ) == original_financials

    renewal_start, renewal_end = lease.end_date, lease.end_date + timedelta(days=31)
    terms = {
        **lease.terms,
        "starts_on": str(renewal_start),
        "ends_on_exclusive": str(renewal_end),
        "handover_on": str(renewal_start),
        "billing_anchor_day": renewal_start.day,
        "renewal_commission_rate_bps": 0,
    }
    renewal = sign_change(
        owner_api, tenant_api, lease, "renewals", terms, renewal_start
    )
    clock[0] = datetime(2026, 3, 3, 12, tzinfo=dt_timezone.utc)
    assert process_rental_changes()["applied"] == 1
    assert process_rental_changes()["applied"] == 0
    renewal.refresh_from_db()
    renewed = renewal.result_lease
    assert renewed.document_id == renewal.document_id
    assert renewed.document_hash == renewal.document_hash
    assert renewed.policy_version == terms["policy_version"]
    assert renewed.tenancy_root_id == lease.tenancy_root_id
    assert (
        renewed.offer_id == lease.offer_id
        and renewed.owner_id == lease.owner_id
        and renewed.tenant_id == lease.tenant_id
    )
    first_renewal_invoice = renewed.invoices.get()
    renewed_payable = pay_invoice(tenant_api, first_renewal_invoice)
    assert renewed_payable.commission_minor == 0
    assert renewed_payable.net_minor == renewed_payable.gross_minor
    assert (
        OwnerPayable.objects.filter(
            lease__tenancy_root_id=lease.tenancy_root_id, commission_minor__gt=0
        ).count()
        == 1
    )
    for actor in (owner_api, tenant_api):
        read = actor.get(API + f"leases/{renewed.id}/")
        assert read.status_code == 200 and read.data["terms"] == terms
    assert actors[stranger.pk].get(API + f"leases/{renewed.id}/").status_code == 404
    if output := os.environ.get("SOKOUN_PLANNING_ARTIFACT_DIR"):
        folder = Path(output)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "ongoing-http-cycle.json").write_text(
            json.dumps(
                {
                    "transport": "HTTP over loopback with JWT login",
                    "database": "isolated PostgreSQL",
                    "providers": "API mocks",
                    "clock_controlled": True,
                    "worker_calls": "Direct task calls on disposable test database; deployed beat not covered",
                    "covered": [
                        "month_end_billing",
                        "payment_extension",
                        "recurring_capture",
                        "signed_amendment",
                        "signed_renewal",
                        "renewal_capture",
                    ],
                    "renewal_commission_minor": renewed_payable.commission_minor,
                    "calls": [
                        call for actor in actors.values() for call in actor.calls
                    ],
                },
                indent=2,
            )
        )
