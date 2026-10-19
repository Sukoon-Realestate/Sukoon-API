"""Opt-in, real independent-cluster drill. Never points at an external provider."""

import os
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pytest
from django.db import transaction, close_old_connections
from core_apps.common.recovery import dispatch, RecoveryRequired
from core_apps.common.recovery_postgres import PostgresRecoveryJournal
from core_apps.features.models import RentalProviderInstruction

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def independent(settings, tmp_path):
    dsn = os.environ.get("SOKOUN_TEST_JOURNAL_DSN")
    if not dsn:
        pytest.skip("Independent PostgreSQL drill cluster not supplied")
    settings.RECOVERY_JOURNAL_DSN = dsn
    settings.RECOVERY_JOURNAL_ADAPTER = (
        "core_apps.common.recovery_postgres.PostgresRecoveryJournal"
    )
    settings.RECOVERY_TEST_BYPASS = False
    settings.RECOVERY_ENVIRONMENT = "isolated-independent-drill"
    settings.RECOVERY_CONTROL_FILE = str(tmp_path / "control.json")
    Path(settings.RECOVERY_CONTROL_FILE).write_text(
        json.dumps(
            {
                "environment": settings.RECOVERY_ENVIRONMENT,
                "generation": "local-drill-g1",
                "security_epoch": "local-drill-e1",
                "mode": "open",
                "scopes": ["provider_outbound"],
                "approval_reference": "synthetic-drill-only",
                "coverage_reference": "local-test",
            }
        )
    )
    return PostgresRecoveryJournal()


def instruction():
    return RentalProviderInstruction.objects.create(
        reference="independent-drill:" + str(uuid.uuid4()),
        kind="payout",
        provider="synthetic",
        subject_id=uuid.uuid4(),
        subject_revision=1,
        request_fingerprint="b" * 64,
    )


def test_primary_rollback_does_not_erase_durable_external_fact(independent):
    calls = []
    with pytest.raises(RuntimeError):
        with transaction.atomic():
            item = instruction()
            identity = item.pk
            dispatch(item, {}, lambda: calls.append("synthetic-ack") or "synthetic-ack")
            raise RuntimeError(
                "Simulate primary transaction loss after provider acknowledgment"
            )
    assert not RentalProviderInstruction.objects.filter(pk=identity).exists()
    assert [
        r["status"]
        for r in independent.lookup(
            "isolated-independent-drill:synthetic:" + item.reference
        )
    ] == ["prepared", "confirmed"]
    with pytest.raises(RecoveryRequired):
        dispatch(item, {}, lambda: calls.append("unsafe-replay"))
    assert calls == ["synthetic-ack"]


def test_concurrent_dispatch_has_one_original_transport(independent):
    item = instruction()
    calls = []

    def attempt():
        close_old_connections()
        try:
            return dispatch(item, {}, lambda: calls.append("sent") or "synthetic-once")
        except RecoveryRequired:
            return "reconcile"
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: attempt(), range(2)))
    assert sorted(results) == ["reconcile", "synthetic-once"] and calls == ["sent"]


def test_unknown_outcome_survives_reconnection_and_never_resends(independent):
    item = instruction()
    calls = []

    def lost():
        calls.append("sent")
        raise TimeoutError("Synthetic response lost")

    with pytest.raises(TimeoutError):
        dispatch(item, {}, lost)
    with pytest.raises(RecoveryRequired):
        dispatch(item, {}, lost)
    assert calls == ["sent"]
    assert PostgresRecoveryJournal().health()["unresolved_operations"] >= 1


def test_primary_cluster_and_privileged_role_are_rejected(independent, settings):
    settings.RECOVERY_JOURNAL_DSN = (
        "dbname=sokoun_recovery_drill user=aait host=127.0.0.1 port=55486"
    )
    with pytest.raises(RecoveryRequired):
        PostgresRecoveryJournal().health()
    # The primary DB deliberately has no journal schema. There is no fallback
    # to a table in the restored primary, even with the same configuration shape.
    settings.RECOVERY_JOURNAL_DSN = "dbname=test_sokoun_company_authority_20261019 user=aait host=127.0.0.1 port=55484"
    with pytest.raises(RecoveryRequired):
        PostgresRecoveryJournal().health()


def test_runtime_role_cannot_mutate_or_delete_history(independent):
    import psycopg2

    item = instruction()
    dispatch(item, {}, lambda: "synthetic-immutable")
    with independent.locked() as cursor:
        for sql in [
            "DELETE FROM sokoun_recovery.entries",
            "UPDATE sokoun_recovery.entries SET checksum=checksum",
            "TRUNCATE sokoun_recovery.entries",
        ]:
            with pytest.raises(psycopg2.errors.InsufficientPrivilege):
                cursor.execute(sql)
