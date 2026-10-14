"""Loopback HTTP contract exercise; optional sanitized Flutter UI fixture."""

import json
import os
import uuid
from datetime import timedelta
from pathlib import Path
from urllib.request import Request, urlopen

import pytest
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken

from core_apps.features.tests.test_billing_subscriptions import buyer, plan
from core_apps.features.tests.test_rental_phase3 import phase3_lease
from core_apps.features.tests.test_rental_phase5 import phase5_lease
from core_apps.features.tests.test_rental_phase6 import phase6_lease
from core_apps.features.services.rental_phase3 import generate_billing_schedule
from core_apps.features.models import InvoiceLine, RentalChange, RentalHandover


@pytest.mark.django_db(transaction=True)
def test_local_http_invoice_cancellation_and_owner_consent(
    live_server, buyer, plan, settings
):
    settings.ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]
    buyer.is_verified = True
    buyer.save(update_fields=["is_verified"])
    token = str(AccessToken.for_user(buyer))
    root = live_server.url + "/api/v1/features/v1/"

    def call(route, payload=None):
        request = Request(
            root + route,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept-Language": "en",
            },
        )
        with urlopen(request, timeout=10) as response:
            result = json.load(response)
            assert set(result) == {"message", "data"}
            return result["data"]

    invoice = call(
        "billing/invoices/?projection=mobile_v1",
        {
            "purpose": "subscription",
            "workspace": "owner",
            "plan_id": str(plan.id),
            "plan_revision": plan.revision,
            "request_key": str(uuid.uuid4()),
        },
    )
    cancel_path = f"billing/invoices/{invoice['id']}/cancel/?projection=mobile_v1"
    command = {
        "expected_revision": invoice["revision"],
        "request_key": str(uuid.uuid4()),
    }
    cancelled = call(cancel_path, command)
    assert cancelled == call(cancel_path, command)
    assert cancelled["status"] == "cancelled" and cancelled["revision"] == 2
    assert "purchase" not in cancelled
    assert cancelled["source"]["kind"] == "subscription"
    assert cancelled["source"]["id"] == str(plan.id)
    path = "owner-payment-profile/"
    profile = call(path + "?projection=mobile_v1")
    key = str(uuid.uuid4())
    consent = {
        "expected_revision": profile["revision"],
        "request_key": key,
        "accepted_policy_versions": profile["required_policy_versions"],
    }
    session = call(path + "onboarding-session/", consent)
    assert session == call(path + "onboarding-session/", consent)
    assert session["operation_receipt"]["request_key"] == key
    pending = call(path + "?projection=mobile_v1")
    assert pending["status"] == "pending"
    assert "provider" not in pending and "structured_summary" not in pending
    assert pending["required_policy_versions"] == pending["accepted_policy_versions"]
    output = os.environ.get("SOKOUN_FIELD_CONTRACT_OUT")
    if output:
        Path(output).write_text(
            json.dumps({"profile": pending, "invoice": cancelled}, indent=2)
        )


@pytest.mark.django_db(transaction=True)
def test_local_http_rent_accounting_credit_and_deferral(
    live_server, phase3_lease, settings
):
    settings.ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]
    owner, tenant, lease = phase3_lease
    invoice = list(generate_billing_schedule(lease))[0].invoice
    invoice.charges_minor = invoice.amount_minor
    invoice.credits_minor = 2500
    invoice.applied_minor = 1000
    invoice.due_at = timezone.now() + timedelta(days=1)
    invoice.deferred_until = invoice.due_at + timedelta(days=3)
    invoice.save(
        update_fields=[
            "charges_minor",
            "credits_minor",
            "applied_minor",
            "due_at",
            "deferred_until",
        ]
    )
    InvoiceLine.objects.create(
        invoice=invoice,
        line_type="settlement_credit",
        description="Local test credit",
        amount_minor=-2500,
        currency=invoice.currency,
        exponent=invoice.exponent,
    )
    token = str(AccessToken.for_user(tenant))
    path = f"/api/v1/features/v1/rent-invoices/{invoice.id}/"
    with urlopen(
        Request(live_server.url + path, headers={"Authorization": f"Bearer {token}"}),
        timeout=10,
    ) as response:
        envelope = json.load(response)
    assert set(envelope) == {"message", "data"}
    value = envelope["data"]
    assert value["charges"]["amount_minor"] == invoice.charges_minor
    assert value["credits"]["amount_minor"] == 2500
    assert value["applied"]["amount_minor"] == 1000
    assert value["balance"]["amount_minor"] == invoice.amount_minor - 3500
    assert value["due_at"] != value["deferred_until"]
    assert (
        next(
            line
            for line in value["lines"]
            if line["description"] == "Local test credit"
        )["amount"]["amount_minor"]
        == -2500
    )
    output = os.environ.get("SOKOUN_FIELD_CONTRACT_OUT")
    if output:
        path = Path(output)
        payload = json.loads(path.read_text()) if path.exists() else {}
        payload["rent_invoice"] = value
        path.write_text(json.dumps(payload, indent=2))


def _local_json(live_server, user, route, payload=None):
    request = Request(
        live_server.url + "/api/v1/features/v1/" + route,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={
            "Authorization": f"Bearer {AccessToken.for_user(user)}",
            "Content-Type": "application/json",
        },
    )
    with urlopen(request, timeout=10) as response:
        envelope = json.load(response)
    assert set(envelope) == {"message", "data"}
    return envelope["data"]


def _save_fields(**values):
    output = os.environ.get("SOKOUN_FIELD_CONTRACT_OUT")
    if output:
        path = Path(output)
        existing = json.loads(path.read_text()) if path.exists() else {}
        path.write_text(json.dumps({**existing, **values}, indent=2))


@pytest.mark.django_db(transaction=True)
def test_local_http_maintenance_exact_cost_decision(
    live_server, phase5_lease, settings
):
    settings.ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]
    owner, tenant, lease = phase5_lease
    initial = _local_json(
        live_server,
        tenant,
        f"leases/{lease.id}/maintenance-requests/",
        {
            "title": "Local repair",
            "description": "Kitchen pipe",
            "category": "plumbing",
            "priority": "normal",
            "access_times": ["morning"],
            "evidence_ids": [],
            "request_key": str(uuid.uuid4()),
            "expected_revision": 0,
        },
    )["resource"]
    path = f"maintenance-requests/{initial['id']}/actions/"
    proposed = _local_json(
        live_server,
        owner,
        path,
        {
            "action": "propose_cost",
            "note": "Estimate reviewed",
            "cost": {"amount_minor": 2500, "currency": "EGP", "exponent": 2},
            "cost_payer": "tenant",
            "expected_revision": initial["revision"],
            "request_key": str(uuid.uuid4()),
        },
    )["resource"]
    proposed = _local_json(
        live_server, tenant, f"maintenance-requests/{initial['id']}/"
    )
    assert "approve_cost" in proposed["allowed_actions"]
    command = {
        "action": "approve_cost",
        "note": "Approved the current estimate",
        "cost_version": proposed["cost_version"],
        "expected_revision": proposed["revision"],
        "request_key": str(uuid.uuid4()),
    }
    approved = _local_json(live_server, tenant, path, command)
    assert approved == _local_json(live_server, tenant, path, command)
    assert approved["resource"]["approved_cost_version"] == proposed["cost_version"]
    _save_fields(maintenance_pending=proposed, maintenance=approved["resource"])


@pytest.mark.django_db(transaction=True)
def test_local_http_settlement_comments(live_server, phase6_lease, settings):
    settings.ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]
    owner, tenant, lease = phase6_lease
    path = f"leases/{lease.id}/final-settlement/"
    initial = _local_json(live_server, owner, path)
    proposal = _local_json(
        live_server,
        owner,
        path + "propose/",
        {
            "lines": [],
            "note": "No outstanding deductions",
            "expected_revision": initial["revision"],
            "request_key": str(uuid.uuid4()),
        },
    )["resource"]
    command = {
        "decision": "accept",
        "note": "Agreed after checking the statement",
        "expected_revision": proposal["revision"],
        "request_key": str(uuid.uuid4()),
    }
    accepted = _local_json(live_server, tenant, path + "respond/", command)
    assert accepted == _local_json(live_server, tenant, path + "respond/", command)
    value = _local_json(live_server, owner, path)
    assert len(value["notes"]) == 2
    _save_fields(settlement=value)


@pytest.mark.django_db(transaction=True)
def test_local_http_analytics_language(live_server, phase5_lease, settings):
    settings.ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]
    owner, _, lease = phase5_lease
    route = f"owner-analytics/{lease.property.id}/?period_days=30&lang="
    arabic = _local_json(live_server, owner, route + "ar")
    english = _local_json(live_server, owner, route + "en")
    assert arabic["metrics"][0]["label"] == "الزوار الفريدون"
    assert english["metrics"][0]["label"] == "Unique visitors"
    _save_fields(analytics_ar=arabic, analytics_en=english)


@pytest.mark.django_db(transaction=True)
def test_local_http_response_notes_reach_lease_timeline(
    live_server, phase5_lease, settings
):
    settings.ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]
    owner, tenant, lease = phase5_lease
    handover = RentalHandover.objects.create(
        lease=lease,
        kind="move_in",
        possession_on=lease.start_date,
        status="pending_approval",
        condition={},
        keys={},
        meters={},
        inventory=[],
    )
    change = RentalChange.objects.create(lease=lease, requester=owner, kind="amendment")
    for route, action, note in (
        (
            f"handovers/{handover.id}/respond/",
            "dispute",
            "Please correct the meter reading",
        ),
        (
            f"amendments/{change.id}/respond/",
            "request_changes",
            "Please correct the proposed dates",
        ),
    ):
        body = {
            "decision": action,
            "note": note,
            "expected_revision": 1,
            "request_key": str(uuid.uuid4()),
        }
        first = _local_json(live_server, tenant, route, body)
        assert first == _local_json(live_server, tenant, route, body)
    events = _local_json(live_server, owner, f"leases/{lease.id}/timeline/")
    assert isinstance(events, list) and len(events) == 2
    _save_fields(timeline=events, timeline_lease_id=str(lease.id))
