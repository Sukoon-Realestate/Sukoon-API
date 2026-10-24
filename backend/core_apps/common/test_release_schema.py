from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection, connections

from core_apps.common.management.commands.migrate_release import LOCK_KEY, release_lock


@pytest.mark.django_db(transaction=True)
def test_competing_release_cannot_apply_schema_and_can_retry_after_unlock():
    if connection.vendor != "postgresql":
        pytest.skip("Requires real independent PostgreSQL sessions")
    other = connection.copy(alias="migration_competitor")
    connections[other.alias] = other
    try:
        with other.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_lock(%s)", [LOCK_KEY])
        with patch("core_apps.common.management.commands.migrate_release.call_command") as migrate:
            with pytest.raises(CommandError, match="startup is stopped"):
                call_command("migrate_release", lock_timeout=0.1, verbosity=0)
            migrate.assert_not_called()
        other.close()
        # This runs the actual migration command and verifies the applied plan.
        call_command("migrate_release", lock_timeout=1, verbosity=0)
    finally:
        other.close()
        del connections[other.alias]


@pytest.mark.django_db(transaction=True)
def test_failed_release_does_not_leave_a_schema_lock_behind():
    if connection.vendor != "postgresql":
        pytest.skip("Requires real independent PostgreSQL sessions")
    with pytest.raises(RuntimeError):
        with release_lock(1):
            raise RuntimeError("Interrupted release")
    other = connection.copy(alias="migration_after_failure")
    connections[other.alias] = other
    try:
        with other.cursor() as cursor:
            cursor.execute("SELECT pg_try_advisory_lock(%s)", [LOCK_KEY])
            assert cursor.fetchone()[0] is True
    finally:
        other.close()
        del connections[other.alias]
