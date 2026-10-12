"""Cancellation has one revision; old receipts and concurrent retries stay stable."""

import copy
import uuid
from datetime import timedelta

import pytest
from django.db import connection
from django.utils import timezone

from core_apps.features.models import IdempotencyRecord, Lease, TenancyInvitation
from .test_cycle_concurrency import parallel_calls
from .test_rental_phase2 import authenticated, rental_participants

API = "/api/v1/features/v1/"


@pytest.fixture
def draft(rental_participants):  # noqa: F811 - shared pytest fixture
    owner, tenant, _, prop, _ = rental_participants
    start = timezone.localdate() + timedelta(days=3)
    lease = Lease.objects.create(
        property=prop,
        owner=owner,
        tenant=tenant,
        template_id="eg-residential-v1",
        template_version="1",
        start_date=start,
        end_date=start + timedelta(days=30),
        rent_amount_minor=1_000_000,
        legacy_read_only=False,
    )
    return owner, lease


def cancellation_body(structured):
    body = {"request_key": str(uuid.uuid4())}
    if structured:
        body.update(expected_revision=1, decision="cancel_draft", note="")
    else:
        body["revision"] = 1
    return body


@pytest.mark.django_db
@pytest.mark.parametrize("structured", [False, True])
def test_pre_fix_revision_three_receipt_remains_immutable(draft, structured):
    owner, lease = draft
    client = authenticated(owner)
    body = cancellation_body(structured)
    path = API + f"leases/{lease.id}/"
    cancelled = client.post(path + "cancel/", body, format="json")
    assert cancelled.status_code == 200
    lease.refresh_from_db()
    assert lease.revision == 2

    # Represent a cancellation completed before this fix. Never rewrite its
    # version or response during replay, even though new cancellations use +1.
    historical_receipt = copy.deepcopy(cancelled.data)
    if structured:
        historical_receipt["resource"]["revision"] = 3
        historical_receipt["operation_receipt"]["revision"] = 3
    else:
        historical_receipt["revision"] = 3
    record = IdempotencyRecord.objects.get(operation="lease.cancel")
    record.response_data = historical_receipt
    record.result_revision = 3
    record.save(update_fields=["response_data", "result_revision"])
    Lease.objects.filter(pk=lease.pk).update(revision=3)

    for language in ("en", "ar"):
        replay = client.post(
            path + "cancel/", body, format="json", HTTP_ACCEPT_LANGUAGE=language
        )
        assert replay.status_code == 200
        assert replay.data == historical_receipt
        assert client.get(path).data["revision"] == 3
    changed_body = {**body, "expected_revision" if structured else "revision": 3}
    assert client.post(path + "cancel/", changed_body, format="json").status_code == 409
    assert (
        client.post(
            path + "cancel/",
            {**body, "request_key": str(uuid.uuid4())},
            format="json",
        ).status_code
        == 409
    )
    lease.refresh_from_db()
    record.refresh_from_db()
    assert lease.revision == record.result_revision == 3
    assert record.response_data == historical_receipt
    assert IdempotencyRecord.objects.filter(operation="lease.cancel").count() == 1


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("structured", [False, True])
@pytest.mark.parametrize("same_key", [False, True])
def test_concurrent_cancellations_increment_once(draft, structured, same_key):
    if connection.vendor != "postgresql":
        pytest.skip("Cancellation races require PostgreSQL row locks")
    owner, lease = draft
    if not structured:
        lease.legacy_read_only = True
        lease.save(update_fields=["legacy_read_only"])
        TenancyInvitation.objects.create(
            property=lease.property,
            owner=owner,
            tenant=lease.tenant,
            initiated_by=owner,
            status=TenancyInvitation.Status.ACCEPTED,
            lease=lease,
            expires_at=timezone.now() + timedelta(days=7),
        )
    body = cancellation_body(structured)
    bodies = [body, dict(body)]
    if not same_key:
        bodies[1]["request_key"] = str(uuid.uuid4())
    responses = parallel_calls(
        lambda index: authenticated(owner).post(
            API + f"leases/{lease.id}/cancel/", bodies[index], format="json"
        )
    )
    assert sorted(response.status_code for response in responses) == (
        [200, 200] if same_key else [200, 409]
    )
    if same_key:
        assert responses[0].data == responses[1].data
    receipt = next(
        response.data for response in responses if response.status_code == 200
    )
    resource = receipt["resource"] if structured else receipt
    assert resource["revision"] == 2
    lease.refresh_from_db()
    assert lease.revision == 2
    assert lease.status == "cancelled"
    assert lease.financial_closure_status == "closed"
    record = IdempotencyRecord.objects.get(operation="lease.cancel")
    assert record.result_revision == 2
    assert record.response_data == receipt
