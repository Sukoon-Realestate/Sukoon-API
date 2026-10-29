"""Durable statement work; isolated DB tests never certify a deployed worker."""

import hashlib
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone as utc_timezone
from threading import Event
from urllib.parse import urlsplit
from unittest.mock import patch

import pytest
from django.db import connection, connections, transaction
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from core_apps.features.models import (
    IdempotencyRecord,
    LedgerTransaction,
    PrivateAccessRevocation,
    RentalDocument,
)
from core_apps.features.services import rental_statement_delivery as delivery
from core_apps.features.tasks_parts.rental_statement_delivery import (
    generate_requested_rental_statements,
)
from core_apps.users.models import AuthSession
from .test_rental_phase6 import phase6_lease, client_for

pytestmark = pytest.mark.django_db
API = "/api/v1/features/v1/"


@pytest.fixture(autouse=True)
def expose_unexpected_exceptions(settings):
    settings.REST_FRAMEWORK = {
        **settings.REST_FRAMEWORK,
        "EXCEPTION_HANDLER": "rest_framework.views.exception_handler",
    }


def request_statement(tenant, lease, **overrides):
    body = {
        "lease_id": str(lease.id),
        "expected_revision": lease.revision,
        "starts_on": None,
        "ends_on_exclusive": None,
        "request_key": str(uuid.uuid4()),
        **overrides,
    }
    response = client_for(tenant).post(API + "rental-statements/", body, format="json")
    assert response.status_code == 201, response.data
    return RentalDocument.objects.get(id=response.data["resource"]["id"]), body, response


def artifact(document):
    document.refresh_from_db()
    return (
        document.status,
        document.revision,
        bytes(document.private_content or b""),
        document.sha256,
        document.storage_key,
        document.generation_requested_at,
    )


def test_normal_request_and_original_replay_keep_one_durable_work_item(phase6_lease):
    _, tenant, lease = phase6_lease
    with patch("kombu.Producer.publish", side_effect=AssertionError("No request-time broker IO")):
        document, body, original = request_statement(tenant, lease)
        marker = document.generation_requested_at
        assert marker is not None and document.status == "queued" and document.revision == 1
        replay = client_for(tenant).post(API + "rental-statements/", body, format="json")
    assert replay.status_code == 201 and replay.data == original.data
    assert RentalDocument.objects.count() == 1
    receipt = IdempotencyRecord.objects.get(operation=f"statement.create.{lease.id}")
    assert receipt.result_subject_id == document.id and receipt.recovery_status == "confirmed"
    assert receipt.request_subject_id == lease.id
    assert document.generation_requested_at == marker
    assert generate_requested_rental_statements.run() == {
        "selected": 1,
        "generated": 1,
        "retry_pending": 0,
    }
    frozen = artifact(document)
    # Receipt replay remains the original response, not rewritten ready history.
    replay = client_for(tenant).post(API + "rental-statements/", body, format="json")
    assert replay.data == original.data
    assert generate_requested_rental_statements.run()["selected"] == 0
    assert artifact(document) == frozen


def test_statement_receipt_failure_rolls_back_document_and_marker(phase6_lease):
    _, tenant, lease = phase6_lease
    with patch(
        "core_apps.features.rental_phase6_views_parts.lease_reviews.remember_mutation",
        side_effect=RuntimeError("receipt failure"),
    ):
        with pytest.raises(RuntimeError, match="receipt failure"):
            request_statement(tenant, lease)
    assert not RentalDocument.objects.exists()
    assert not IdempotencyRecord.objects.filter(operation=f"statement.create.{lease.id}").exists()
    assert delivery.generate_requested()["selected"] == 0


def test_outer_transaction_rollback_leaves_no_work(phase6_lease):
    _, tenant, lease = phase6_lease
    with transaction.atomic():
        document, _, _ = request_statement(tenant, lease)
        assert document.generation_requested_at
        transaction.set_rollback(True)
    assert not RentalDocument.objects.exists()
    assert delivery.generate_requested()["selected"] == 0


def test_historical_statement_replay_does_not_mark_or_backfill(phase6_lease):
    _, tenant, lease = phase6_lease
    document, body, original = request_statement(tenant, lease)
    # Represent a pre-migration queued row with its already-confirmed receipt.
    RentalDocument.objects.filter(pk=document.pk).update(generation_requested_at=None)
    replay = client_for(tenant).post(API + "rental-statements/", body, format="json")
    assert replay.data == original.data
    document.refresh_from_db()
    assert document.generation_requested_at is None
    assert delivery.generate_requested()["selected"] == 0


def test_only_marked_queued_statements_are_selected(phase6_lease):
    _, tenant, lease = phase6_lease
    protected = []
    for kind in ("contract", "change", "receipt", "settlement"):
        protected.append(
            RentalDocument.objects.create(
                lease=lease,
                document_type=kind,
                title=kind,
                generation_requested_at=timezone.now(),
            )
        )
    for status, marker in (("queued", None), ("ready", timezone.now()), ("failed", timezone.now())):
        protected.append(
            RentalDocument.objects.create(
                lease=lease,
                document_type="statement",
                title="Existing",
                status=status,
                generation_requested_at=marker,
                private_content=b"existing",
                sha256="a" * 64,
            )
        )
    before = {d.id: artifact(d) for d in protected}
    requested, _, _ = request_statement(tenant, lease)
    assert delivery.generate_requested(limit=5) == {
        "selected": 1,
        "generated": 1,
        "retry_pending": 0,
    }
    assert artifact(requested)[0] == "ready"
    assert {d.id: artifact(d) for d in protected} == before


def test_bounded_selection_and_first_ready_bytes_never_regenerate(phase6_lease):
    _, tenant, lease = phase6_lease
    documents = [request_statement(tenant, lease)[0] for _ in range(3)]
    first = min(documents, key=lambda d: (d.updated_at, d.pk))
    assert delivery.generate_requested(limit=1)["generated"] == 1
    frozen = artifact(first)
    assert frozen[0] == "ready" and frozen[1] == 2
    assert hashlib.sha256(frozen[2]).hexdigest() == frozen[3]
    assert RentalDocument.objects.filter(status="queued").count() == 2
    LedgerTransaction.objects.create(lease=lease, reference="later-ledger-row", kind="test")
    assert delivery.generate_requested(limit=2)["generated"] == 2
    assert artifact(first) == frozen
    assert delivery.generate_requested(limit=5)["selected"] == 0


@pytest.mark.parametrize("limit", [0, -1, 6, True, "1", None])
def test_invalid_or_unbounded_batch_is_rejected(limit):
    with pytest.raises(ValueError):
        delivery.generate_requested(limit=limit)


def test_partial_generation_failure_rolls_back_bytes_and_retries_fairly(
    phase6_lease, monkeypatch, caplog
):
    _, tenant, lease = phase6_lease
    first, _, _ = request_statement(tenant, lease)
    second, _, _ = request_statement(tenant, lease)
    real_generate = delivery.generate

    def partial_failure(document):
        document.private_content = b"private-body"
        document.status = "ready"
        document.revision = 99
        document.save()
        raise RuntimeError("private-body private-actor@example.test")

    monkeypatch.setattr(delivery, "generate", partial_failure)
    assert delivery.generate_requested(limit=1) == {
        "selected": 1,
        "generated": 0,
        "retry_pending": 1,
    }
    first.refresh_from_db()
    assert first.status == "queued" and first.revision == 1
    assert not first.private_content and not first.sha256
    assert first.failure_code == "statement_generation_retry_pending"
    assert first.generation_requested_at is not None
    assert "private-body" not in caplog.text and "private-actor" not in caplog.text
    monkeypatch.setattr(delivery, "generate", real_generate)
    assert delivery.generate_requested(limit=1)["generated"] == 1
    assert artifact(second)[0] == "ready" and artifact(first)[0] == "queued"
    assert delivery.generate_requested(limit=1)["generated"] == 1
    first.refresh_from_db()
    assert first.status == "ready" and first.failure_code == "" and first.revision == 2


def test_scheduler_or_broker_pause_does_not_lose_committed_request(phase6_lease):
    _, tenant, lease = phase6_lease
    with patch("kombu.Producer.publish", side_effect=OSError("broker unavailable")) as publisher:
        document, _, _ = request_statement(tenant, lease)
        assert document.status == "queued" and document.generation_requested_at
        publisher.assert_not_called()
    # No scheduler messages were sent while paused. A later normal tick drains
    # the durable row without replaying the command or consuming another proof.
    assert generate_requested_rental_statements.run()["generated"] == 1
    assert artifact(document)[0] == "ready"


def test_saved_period_filters_and_generation_time_are_preserved(phase6_lease):
    _, tenant, lease = phase6_lease
    for name, instant in (
        ("before", datetime(2026, 10, 29, 20, 59, tzinfo=utc_timezone.utc)),
        ("inside", datetime(2026, 10, 30, 10, tzinfo=utc_timezone.utc)),
        ("end", datetime(2026, 10, 30, 22, tzinfo=utc_timezone.utc)),
    ):
        LedgerTransaction.objects.create(
            lease=lease, reference=name, kind="test", occurred_at=instant
        )
    document, _, _ = request_statement(
        tenant, lease, starts_on="2026-10-30", ends_on_exclusive="2026-10-31"
    )
    with timezone.override("Africa/Cairo"):
        assert delivery.generate_requested()["generated"] == 1
    payload = json.loads(artifact(document)[2])
    assert payload["starts_on"] == "2026-10-30" and payload["ends_on_exclusive"] == "2026-10-31"
    assert [row["reference"] for row in payload["ledger"]] == ["inside"]
    assert payload["generated_at"]


@pytest.mark.parametrize("revocation", ["private", "logout", "epoch", "inactive"])
def test_generation_does_not_grant_access_after_revocation(phase6_lease, revocation):
    _, tenant, lease = phase6_lease
    document, _, _ = request_statement(tenant, lease)
    assert delivery.generate_requested()["generated"] == 1
    session = AuthSession.objects.create(
        user=tenant,
        security_epoch=tenant.security_epoch,
        expires_at=timezone.now() + timedelta(hours=1),
    )
    client = APIClient()
    client.force_authenticate(tenant, token={"session_id": str(session.id)})
    link = client.get(reverse("rental-document-download", args=[document.id]))
    assert link.status_code == 200
    url = urlsplit(link.data["url"])
    path = url.path + "?" + url.query
    assert APIClient().get(path).content == artifact(document)[2]
    if revocation == "private":
        PrivateAccessRevocation.objects.create(user=tenant, lease=lease, reason="revoked")
    elif revocation == "logout":
        session.revoked_at = timezone.now()
        session.save(update_fields=["revoked_at"])
    elif revocation == "epoch":
        tenant.security_epoch += 1
        tenant.save(update_fields=["security_epoch"])
    else:
        tenant.is_active = False
        tenant.save(update_fields=["is_active"])
    assert APIClient().get(path).status_code == 404


@pytest.mark.django_db(transaction=True)
def test_concurrent_workers_skip_locked_and_do_not_regenerate(phase6_lease, monkeypatch):
    if connection.vendor != "postgresql":
        pytest.skip("Controlled row locks require PostgreSQL")
    _, tenant, lease = phase6_lease
    first, _, _ = request_statement(tenant, lease)
    second, _, _ = request_statement(tenant, lease)
    locked, release = Event(), Event()
    real_generate = delivery.generate
    calls = []

    def held_generate(document):
        calls.append(document.id)
        if document.id == first.id:
            locked.set()
            assert release.wait(10)
        return real_generate(document)

    monkeypatch.setattr(delivery, "generate", held_generate)

    def run():
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET lock_timeout = '5s'")
            return delivery.generate_requested()
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        worker = pool.submit(run)
        try:
            assert locked.wait(10)
            other = pool.submit(run).result(timeout=10)
            assert other["generated"] == 1
            assert artifact(second)[0] == "ready"
            assert delivery.generate_requested()["selected"] == 0
        finally:
            release.set()
        assert worker.result(timeout=10)["generated"] == 1
    assert sorted(calls) == sorted([first.id, second.id])
    frozen = [artifact(first), artifact(second)]
    assert delivery.generate_requested(limit=5)["selected"] == 0
    assert [artifact(first), artifact(second)] == frozen


@pytest.mark.django_db(transaction=True)
def test_forward_migration_preserves_historical_documents_unmarked(phase6_lease):
    if connection.vendor != "postgresql":
        pytest.skip("Forward schema proof uses isolated PostgreSQL schema")
    from django.db.migrations.loader import MigrationLoader

    _, tenant, lease = phase6_lease
    loader = MigrationLoader(None)
    before = loader.project_state([("features", "0093_rentalchange_termination_notice_snapshot")])
    migration = loader.get_migration("features", "0094_rentaldocument_generation_requested_at")
    assert loader.graph.leaf_nodes("features") == [
        ("features", "0094_rentaldocument_generation_requested_at")
    ]
    old_model = before.apps.get_model("features", "RentalDocument")
    schema = "statement_migration_" + uuid.uuid4().hex
    quoted = connection.ops.quote_name(schema)
    with connection.cursor() as cursor:
        cursor.execute("SHOW search_path")
        original = cursor.fetchone()[0]
        cursor.execute(f"CREATE SCHEMA {quoted}")
        cursor.execute(f"SET search_path TO {quoted}, public")
    try:
        # Only this table is historical; its existing parents stay in the
        # disposable test database's public schema. Never downgrade that schema.
        with connection.schema_editor() as editor:
            editor.create_model(old_model)
        for kind in ("statement", "contract", "receipt", "change", "settlement"):
            for status in ("queued", "ready", "failed"):
                old_model.objects.create(
                    lease_id=lease.pk,
                    requested_by_id=tenant.pk,
                    document_type=kind,
                    title="Historical",
                    status=status,
                    revision=7,
                    private_content=b"saved-history",
                    sha256="b" * 64,
                    storage_key="historical-storage",
                )
        fields = [field.attname for field in old_model._meta.fields]

        def rows(model):
            return list(model.objects.order_by("pk").values(*fields))

        original_rows = rows(old_model)
        with connection.schema_editor() as editor:
            after = migration.apply(before, editor)
        new_model = after.apps.get_model("features", "RentalDocument")
        assert rows(new_model) == original_rows
        assert new_model.objects.count() == 15
        assert not new_model.objects.exclude(generation_requested_at=None).exists()
        ordinary = new_model.objects.create(
            lease_id=lease.pk, title="Unmarked", document_type="statement"
        )
        assert ordinary.generation_requested_at is None
    finally:
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('search_path', %s, false)", [original])
            cursor.execute(f"DROP SCHEMA {quoted} CASCADE")


# Reuse the existing authorized company fixture; provider events remain synthetic.
from .test_company_tenancy import (
    active_agreement,
    signed_agreement,
    agreement,
    cycle,
    company_setup,
    rental_participants,
    policy,
    authenticated,
)


def test_company_payer_revoked_before_generation_cannot_download(active_agreement):
    from core_apps.features.models import CompanyMembership

    participants, tenancy = active_agreement
    lease = tenancy.lease
    api = authenticated(participants["payer"])
    response = api.post(
        API + "rental-statements/",
        {
            "lease_id": str(lease.id),
            "expected_revision": lease.revision,
            "request_key": str(uuid.uuid4()),
            "starts_on": None,
            "ends_on_exclusive": None,
        },
        format="json",
    )
    assert response.status_code == 201, response.data
    document = RentalDocument.objects.get(id=response.data["resource"]["id"])
    assert document.generation_requested_at is not None
    CompanyMembership.objects.filter(
        company=participants["company"], user=participants["payer"]
    ).update(is_active=False)
    assert delivery.generate_requested()["generated"] == 1
    payload = json.loads(artifact(document)[2])
    assert payload["renter"]["company_id"] == str(participants["company"].id)
    assert payload["renter"]["employees_are_debtors"] is False
    path = reverse("rental-document-download", args=[document.id])
    assert api.get(path).status_code == 404
    assert authenticated(participants["employee"]).get(path).status_code == 404


from .test_business_policies import policy_admin
from .test_business_policy_private_export import first_party


def test_receipt_failure_rolls_back_real_action_proof_consumption(
    policy_admin,
    phase6_lease,
    first_party,
    monkeypatch,
):
    from core_apps.common.contract_testing import api_json
    from core_apps.features.services import business_policies
    from core_apps.users.models import SensitiveAuthorization
    from core_apps.users.services import assurance
    from core_apps.users.services.sessions import issue_refresh
    from .test_business_policies import body

    _, tenant, lease = phase6_lease
    tenant.is_email_verified = True
    tenant.save(update_fields=["is_email_verified"])
    business_policies.publish(policy_admin, body("D26"))
    monkeypatch.setattr(assurance, "generate_otp", lambda: "739251")
    api = APIClient()
    api.force_authenticate(tenant, token=issue_refresh(tenant).access_token)
    command = {
        "lease_id": str(lease.id),
        "expected_revision": lease.revision,
        "starts_on": None,
        "ends_on_exclusive": None,
        "request_key": str(uuid.uuid4()),
    }
    challenge = api.post(
        "/api/v1/auth/security/challenges/",
        {
            "action": "private.export",
            "resource_id": str(lease.id),
            "resource_revision": lease.revision,
            "payload": {
                "lease_id": str(lease.id),
                "lease_revision": lease.revision,
                "starts_on": None,
                "ends_on_exclusive": None,
                "request_key": command["request_key"],
            },
        },
        format="json",
    )
    assert challenge.status_code == 201
    identity = api_json(challenge)["data"]["id"]
    verified = api.post(
        f"/api/v1/auth/security/challenges/{identity}/verify/",
        {"assertion": "739251"},
        format="json",
    )
    assert verified.status_code == 200
    proof = api_json(verified)["data"]["proof"]
    with patch(
        "core_apps.features.rental_phase6_views_parts.lease_reviews.remember_mutation",
        side_effect=RuntimeError("receipt failure"),
    ):
        with pytest.raises(RuntimeError, match="receipt failure"):
            api.post(
                API + "rental-statements/",
                command,
                format="json",
                HTTP_X_SOKOUN_AUTHORIZATION=proof,
            )
    assert SensitiveAuthorization.objects.get(id=identity).consumed_at is None
    assert not RentalDocument.objects.exists()
    assert not IdempotencyRecord.objects.filter(operation=f"statement.create.{lease.id}").exists()
    response = api.post(
        API + "rental-statements/", command, format="json", HTTP_X_SOKOUN_AUTHORIZATION=proof
    )
    assert response.status_code == 201
    assert SensitiveAuthorization.objects.get(id=identity).consumed_at is not None
    assert RentalDocument.objects.get().generation_requested_at is not None
    assert delivery.generate_requested()["generated"] == 1
