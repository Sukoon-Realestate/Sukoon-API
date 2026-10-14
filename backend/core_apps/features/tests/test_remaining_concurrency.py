"""PostgreSQL races exercise duplicate operations and last-member consent."""

import pytest
from django.db import connection

from core_apps.features.models import LedgerTransaction, RefundRequest, RentInvoice
from core_apps.features.planning_models import HousingGroup
from core_apps.features.tasks import process_rental_closure
from .test_current_cycle_contract import awaiting_signatures
from .test_cycle_concurrency import parallel_calls
from .test_funded_settlement import command, funded_exit, propose
from .test_planning_cycles import configured_planning_offer, create_group, post
from .test_rental_phase2 import authenticated, rental_participants

API = "/api/v1/features/v1/"


@pytest.fixture(autouse=True)
def postgres_only():
    if connection.vendor != "postgresql":
        pytest.skip("These races require PostgreSQL row locks")


@pytest.mark.django_db(transaction=True)
def test_duplicate_partial_refund_reserves_capture_once(funded_exit):
    _, tenant, _, lease, attempt = funded_exit
    body = command(
        lease_id=str(lease.id),
        payment_attempt_id=str(attempt.id),
        amount={"amount_minor": 500_000},
        allocations={"rent": 200_000, "deposit": 300_000},
    )
    responses = parallel_calls(
        lambda _: authenticated(tenant).post(
            API + "refund-requests/", body, format="json"
        )
    )
    assert [x.status_code for x in responses] == [201, 201]
    assert responses[0].data == responses[1].data
    assert RefundRequest.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_competing_partial_refunds_cannot_oversubscribe_component(funded_exit):
    _, tenant, _, lease, attempt = funded_exit
    bodies = [
        command(
            lease_id=str(lease.id),
            payment_attempt_id=str(attempt.id),
            amount={"amount_minor": 800_000},
            allocations={"rent": 0, "deposit": 800_000},
        )
        for _ in range(2)
    ]
    responses = parallel_calls(
        lambda i: authenticated(tenant).post(
            API + "refund-requests/", bodies[i], format="json"
        )
    )
    assert sorted(x.status_code for x in responses) == [201, 409]
    assert RefundRequest.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_duplicate_funded_settlement_acceptance_posts_once(funded_exit):
    owner, tenant, _, lease, _ = funded_exit
    item = propose(
        owner,
        lease,
        [{"type": "deposit_deduction", "amount": {"amount_minor": 200_000}}],
    )
    body = command(item["revision"], action="accept")
    path = API + f"leases/{lease.id}/final-settlement/respond/"
    responses = parallel_calls(
        lambda _: authenticated(tenant).post(path, body, format="json")
    )
    assert [x.status_code for x in responses] == [200, 200]
    assert responses[0].data == responses[1].data
    assert RentInvoice.objects.filter(invoice_type="adjustment").count() == 1
    assert RefundRequest.objects.count() == 1
    parallel_calls(lambda _: process_rental_closure())
    assert LedgerTransaction.objects.filter(kind="refund").count() == 1


@pytest.mark.django_db(transaction=True)
def test_competing_group_joins_cannot_overfill(rental_participants):
    owner, tenant, member, prop, _ = rental_participants
    group = create_group(tenant, prop)
    invitation = post(
        tenant,
        f"housing-groups/{group['id']}/invitations/",
        command(group_id=group["id"], group_revision=group["revision"]),
        201,
    ).data["resource"]
    actors = [owner, member]
    bodies = [
        command(
            group["revision"],
            group_id=group["id"],
            group_revision=group["revision"],
            token=invitation["link"].split("#")[1],
        )
        for _ in actors
    ]
    responses = parallel_calls(
        lambda i: authenticated(actors[i]).post(
            API + "group-invitations/join/", bodies[i], format="json"
        )
    )
    assert sorted(x.status_code for x in responses) == [200, 409]
    assert HousingGroup.objects.get().memberships.filter(status="active").count() == 2
