"""Recovery locks, negative authorization and original-command fencing."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event
from uuid import uuid4
import pytest
from django.db import close_old_connections
from core_apps.features.models import IdempotencyRecord
from core_apps.features.tests.test_company_role_contexts import (
    tenancy,
    cycle,
    company_setup,
    rental_participants,
    policy,
    client,
    command,
    API,
)


def resolve(actor, item, key, action="review", role="owner"):
    body = {"request_key": key, "action": action}
    if role:
        body["role"] = role
    return actor.post(
        API + f"company-tenancies/{item.id}/resolve-operation/", body, format="json"
    )


def review(actor, item, key):
    return actor.post(
        API + f"company-tenancies/{item.id}/review/",
        command(
            request_key=key,
            expected_revision=item.revision,
            role="owner",
            digest=item.terms_digest,
        ),
        format="json",
    )


@pytest.mark.django_db
@pytest.mark.parametrize("action,role", [("review", "owner"), ("handover", None)])
def test_absence_is_fenced_and_idempotent_without_business_mutation(
    tenancy, action, role
):
    c, item = tenancy
    actor, key, revision = client(c["owner"]), str(uuid4()), item.revision
    first = resolve(actor, item, key, action, role)
    assert first.status_code == 200, first.data
    assert first.data["status"] == "absent_final"
    assert resolve(actor, item, key, action, role).data == first.data
    item.refresh_from_db()
    item.lease.refresh_from_db()
    assert item.revision == revision and item.contract_reviews == {}
    assert not item.changes.exists() and not item.lease.invoices.exists()
    lookup = actor.get(API + f"rental-operations/{key}/", {"subject_id": str(item.id)})
    assert lookup.status_code == 200 and lookup.data["status"] == "absent_final"
    if action == "review":
        late = review(actor, item, key)
        assert late.status_code == 409
        assert late["X-App-Error-Code"] == "operation_closed_without_execution"


@pytest.mark.django_db
def test_confirmed_receipt_is_minimal_and_does_not_reexecute(tenancy):
    c, item = tenancy
    actor, key = client(c["owner"]), str(uuid4())
    response = review(actor, item, key)
    assert response.status_code == 200, response.data
    result = resolve(actor, item, key)
    assert result.status_code == 200 and result.data["status"] == "confirmed"
    assert "resource" not in result.data and "terms" not in str(result.data)
    assert result.data["operation_receipt"] == response.data["operation_receipt"]


@pytest.mark.django_db
@pytest.mark.parametrize("role", ["admin", "payer", "employee", "approver", None])
def test_other_roles_cannot_fence_signer_command(tenancy, role):
    c, item = tenancy
    key = str(uuid4())
    result = resolve(client(c["signer"], c["company"], role), item, key, role="signer")
    assert result.status_code in {403, 404}
    assert not IdempotencyRecord.objects.filter(request_key=key).exists()


@pytest.mark.django_db
def test_expired_draft_can_be_recovered_but_revoked_member_cannot(tenancy):
    c, item = tenancy
    item.lease.status = "expired"
    item.lease.save()
    actor = client(c["signer"], c["company"], "signer")
    assert resolve(actor, item, str(uuid4()), role="signer").status_code == 200
    item.signer_mandate.membership.is_active = False
    item.signer_mandate.membership.save()
    key = str(uuid4())
    assert resolve(actor, item, key, role="signer").status_code == 404
    assert not IdempotencyRecord.objects.filter(request_key=key).exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "action", ["sign", "submit_signature", "payment", "settlement", "terminate"]
)
def test_provider_and_other_commands_are_not_resolvable(tenancy, action):
    c, item = tenancy
    key = str(uuid4())
    assert resolve(client(c["owner"]), item, key, action, None).status_code == 400
    assert not IdempotencyRecord.objects.filter(request_key=key).exists()


@pytest.mark.django_db
def test_key_cannot_be_rebound_to_another_subject_or_action(tenancy):
    c, item = tenancy
    actor, key = client(c["owner"]), str(uuid4())
    assert resolve(actor, item, key).status_code == 200
    assert resolve(actor, item, key, "handover", None).status_code == 409
    row = IdempotencyRecord.objects.get(request_key=key)
    row.request_subject_id = uuid4()
    row.save()
    assert resolve(actor, item, key).status_code == 409


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("first_is_resolution", [True, False])
def test_resolution_serializes_with_delayed_original_command(
    tenancy, monkeypatch, first_is_resolution
):
    from core_apps.features.services.company import (
        tenancy_operation_recovery as recovery,
    )
    from core_apps.features.services.company import tenancy_contracts as contracts

    c, item = tenancy
    key, entered, release, second_started = str(uuid4()), Event(), Event(), Event()
    module, name = (
        (recovery, "audit") if first_is_resolution else (contracts, "validate_unsigned")
    )
    original = getattr(module, name)

    def pause(*args, **kwargs):
        entered.set()
        assert release.wait(10)
        return original(*args, **kwargs)

    monkeypatch.setattr(module, name, pause)

    def run(is_resolution, second=False):
        close_old_connections()
        try:
            if second:
                second_started.set()
            actor = client(c["owner"])
            return (
                resolve(actor, item, key) if is_resolution else review(actor, item, key)
            )
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(run, first_is_resolution)
        assert entered.wait(10)
        second = pool.submit(run, not first_is_resolution, True)
        try:
            assert second_started.wait(3)
            assert not second.done()
        finally:
            release.set()
        one, two = first.result(timeout=15), second.result(timeout=15)
    assert one.status_code == 200, one.data
    if first_is_resolution:
        assert two.status_code == 409, two.data
        item.refresh_from_db()
        assert item.contract_reviews == {}
    else:
        assert two.status_code == 200 and two.data["status"] == "confirmed", two.data
