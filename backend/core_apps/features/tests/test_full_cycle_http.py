"""JWT login and real HTTP transport across the funded owner/tenant cycle."""

import json
import os
from datetime import datetime, timedelta, timezone as dt_timezone
from pathlib import Path

import pytest
import requests
from django.db import connection
from django.utils import timezone

from core_apps.common.contract_testing import api_json
from core_apps.admin_api.models import StaffProfile
from core_apps.features.models import (
    Lease,
    OwnerPayable,
    RefundRequest,
    RentalInventoryDayLock,
)
from core_apps.features.tasks import process_rental_changes, process_rental_closure
from core_apps.users.models import User
from . import test_rental_phase2 as initial_cycle
from .test_funded_settlement import command
from .test_rental_phase2 import rental_participants
from .cycle_http_sources import group_entry, housing_request_entry, marketplace_entry

API = "/api/v1/features/v1/"


class HttpActor:
    def __init__(self, base_url, user):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.trust_env = False
        login = self.session.post(
            base_url + "/api/v1/auth/login/",
            json={"email": user.email, "password": "pass"},
            timeout=10,
        )
        assert login.status_code == 200
        # The fixture advances Django's business clock without advancing JWT's
        # wall clock; these synthetic sessions cover the whole simulated lease.
        from core_apps.users.models import AuthSession

        AuthSession.objects.filter(user=user).update(
            expires_at=timezone.now() + timedelta(days=60)
        )
        payload = login.json()
        token = payload.get("access") or payload.get("data", {}).get("access")
        assert token
        self.session.headers["Authorization"] = f"Bearer {token}"
        self.session.cookies.clear()
        self.calls = []

    def call(self, method, path, data=None, **kwargs):
        response = self.session.request(
            method,
            self.base_url + path,
            params=data if method == "GET" else None,
            json=data if method != "GET" else None,
            timeout=10,
        )
        payload = api_json(response)
        response.data = payload["data"]
        self.calls.append(
            {"method": method, "path": path, "status": response.status_code}
        )
        return response

    def get(self, path, data=None, **kwargs):
        return self.call("GET", path, data, **kwargs)

    def post(self, path, data=None, **kwargs):
        return self.call("POST", path, data, **kwargs)

    def put(self, path, data=None, **kwargs):
        return self.call("PUT", path, data, **kwargs)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "source", ["direct", "marketplace", "group", "housing_request"]
)
def test_complete_funded_cycle_over_http(
    rental_participants, live_server, monkeypatch, source
):
    if connection.vendor != "postgresql":
        pytest.skip(
            "Full HTTP cycle uses isolated PostgreSQL and real transaction locks"
        )
    owner, tenant, stranger, _, _ = rental_participants
    actors = {
        user.pk: HttpActor(live_server.url, user) for user in (owner, tenant, stranger)
    }
    monkeypatch.setattr(initial_cycle, "authenticated", lambda user: actors[user.pk])
    prop = rental_participants[3]
    prop.rental_inventory["offers"][0]["terms"].update(
        rental_period=1,
        suitable_for="all",
        description="Configured shared accommodation",
        smoking_allowed=False,
        rules=[],
    )
    prop.save(update_fields=["rental_inventory"])
    interest = None
    if source == "marketplace":
        marketplace_entry(actors, rental_participants)
    elif source == "group":
        interest = group_entry(actors, rental_participants)
    elif source == "housing_request":
        interest = housing_request_entry(actors, rental_participants)
    # Runs actual onboarding, interest, proposal, invitation, lease review, mock
    # signatures, combined payment, settlement, move-in and maintenance over HTTP.
    initial_cycle.run_interest_to_activation(
        rental_participants, existing_interest=interest
    )
    lease = Lease.objects.get()
    owner_api, tenant_api = actors[owner.pk], actors[tenant.pk]
    ending_day = lease.start_date + timedelta(days=20)
    from core_apps.features.services.termination_notice import policy

    termination = owner_api.post(
        API + f"leases/{lease.id}/termination-requests/",
        command(
            lease_revision=lease.revision,
            effective_on=str(ending_day),
            reason="Mutually agreed early end",
            evidence_ids=[],
            termination_mode="contract_notice",
            notice_basis_digest=policy(lease)["basis_digest"],
        ),
    )
    assert termination.status_code == 201, termination.data
    change = termination.data["resource"]
    response = tenant_api.post(
        API + f"termination-requests/{change['id']}/respond/",
        command(change["revision"], action="accept", termination_notice_digest=change["termination_notice"]["digest"]),
    )
    assert response.status_code == 200, response.data
    lease.refresh_from_db()
    assert (
        lease.status == "termination_pending" and lease.occupancy_status == "occupied"
    )
    future_now = datetime.combine(
        ending_day, datetime.min.time(), tzinfo=dt_timezone.utc
    ) + timedelta(hours=12)
    # This business-clock fixture advances twenty days. Explicitly retain the
    # synthetic HTTP sessions for this scenario; expiry is separately tested.
    from core_apps.users.models import AuthSession

    AuthSession.objects.update(expires_at=future_now + timedelta(hours=1))
    monkeypatch.setattr(timezone, "now", lambda: future_now)
    assert process_rental_changes()["applied"] == 1
    lease.refresh_from_db()
    assert lease.status == "ended" and lease.occupancy_status == "move_out_pending"
    assert RentalInventoryDayLock.objects.filter(lease=lease).exists()
    returned = owner_api.post(
        API + f"leases/{lease.id}/handovers/",
        command(
            kind="move_out",
            possession_on=str(ending_day),
            condition={"summary": "One damaged key"},
            keys={"count": 1},
            meters={},
            inventory=[],
            evidence_ids=[],
        ),
    )
    assert returned.status_code == 201, returned.data
    handover = returned.data["resource"]
    for actor in (owner_api, tenant_api):
        result = actor.post(
            API + f"handovers/{handover['id']}/respond/",
            command(handover["revision"], decision="accept"),
        )
        assert result.status_code == 200, result.data
        handover = result.data["resource"]
    lease.refresh_from_db()
    assert lease.occupancy_status == "returned"
    assert not RentalInventoryDayLock.objects.filter(lease=lease).exists()
    assert lease.financial_closure_status == "open"
    base = API + f"leases/{lease.id}/final-settlement/"
    initial = owner_api.get(base).data
    proposal = owner_api.post(
        base + "propose/",
        command(
            initial["revision"],
            lines=[
                {
                    "type": "deposit_deduction",
                    "description": "Agreed replacement key",
                    "amount": {
                        "amount_minor": 200_000,
                        "currency": "EGP",
                        "exponent": 2,
                    },
                    "evidence_ids": [],
                }
            ],
        ),
    )
    assert proposal.status_code == 200, proposal.data
    item = proposal.data["resource"]
    body = command(item["revision"], action="accept")
    result = tenant_api.post(base + "respond/", body)
    assert result.status_code == 200, result.data
    assert tenant_api.post(base + "respond/", body).data == result.data
    assert process_rental_closure()["refunds"] == 1
    assert process_rental_closure()["refunds"] == 0
    assert RefundRequest.objects.get().amount_minor == 800_000
    operator = User.objects.create_user(
        email="http-payout@example.test", password="pass", is_verified=True
    )
    StaffProfile.objects.create(
        user=operator, role_name=StaffProfile.RoleName.PAYOUT_OPERATOR
    )
    operations = HttpActor(live_server.url, operator)
    body = command(
        payable_ids=[str(x) for x in lease.owner_payables.values_list("id", flat=True)]
    )
    payout = operations.post(API + "operations/payouts/execute/", body)
    assert payout.status_code == 201, payout.data
    assert (
        operations.post(API + "operations/payouts/execute/", body).data == payout.data
    )
    paid = operations.post(
        API + f"operations/payouts/{payout.data['resource']['id']}/reconcile/",
        command(payout.data["resource"]["revision"]),
    )
    assert paid.status_code == 200, paid.data
    process_rental_closure()
    lease.refresh_from_db()
    assert (
        lease.status == "ended"
        and lease.occupancy_status == "returned"
        and lease.financial_closure_status == "closed"
    )
    assert lease.owner_payables.filter(payout_status="succeeded").count() == 2
    for actor in (owner_api, tenant_api):
        final = actor.get(API + f"leases/{lease.id}/")
        assert final.status_code == 200
        assert final.data["financial_closure_status"] == "closed"
    assert actors[stranger.pk].get(API + f"leases/{lease.id}/").status_code == 404
    for entry in lease.ledger_transactions.all():
        assert sum(
            x.amount_minor for x in entry.entries.filter(direction="debit")
        ) == sum(x.amount_minor for x in entry.entries.filter(direction="credit"))
    if directory := os.environ.get("SOKOUN_PLANNING_ARTIFACT_DIR"):
        target = Path(directory)
        target.mkdir(parents=True, exist_ok=True)
        (
            target
            / (
                "full-http-cycle.json"
                if source == "direct"
                else f"full-http-cycle-{source}.json"
            )
        ).write_text(
            json.dumps(
                {
                    "transport": "HTTP over loopback with JWT login",
                    "database": "isolated PostgreSQL",
                    "providers": "API mocks",
                    "entry_cycle": source,
                    "clock_advanced_for_termination": True,
                    "final_status": lease.status,
                    "occupancy_status": lease.occupancy_status,
                    "financial_closure_status": lease.financial_closure_status,
                    "calls": [
                        call
                        for actor in [*actors.values(), operations]
                        for call in actor.calls
                    ],
                },
                indent=2,
            )
        )
