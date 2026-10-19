"""Independent PostgreSQL journal. No primary-DB or local-file fallback.

Provision with recovery_journal_setup.sql on a separate cluster. The runtime
role can read/append entries but cannot edit, delete, truncate or own them.
"""

import hashlib
import json
from contextlib import contextmanager
import psycopg2
from django.conf import settings
from django.db import connection
from django.utils import timezone
from .recovery import RecoveryRequired, LocalDrillJournal

LOCK_KEY = 7200606190301


def checksum(record):
    return hashlib.sha256(
        json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class PostgresRecoveryJournal:
    test_only = False

    def __init__(self):
        self.dsn = getattr(settings, "RECOVERY_JOURNAL_DSN", "")
        if not self.dsn or not getattr(settings, "RECOVERY_ENVIRONMENT", ""):
            raise RecoveryRequired(
                "Configure the independent journal and environment first."
            )

    def verify(self, cursor):
        # System identifiers identify physical clusters, not database names.
        # A second database on the primary cluster is not an independent journal.
        with connection.cursor() as primary:
            primary.execute("SELECT system_identifier::text FROM pg_control_system()")
            primary_id = primary.fetchone()[0]
        cursor.execute(
            "SELECT cluster_id, environment FROM sokoun_recovery.identity WHERE singleton = TRUE"
        )
        row = cursor.fetchone()
        cursor.execute("SELECT system_identifier::text FROM pg_control_system()")
        actual_id = cursor.fetchone()[0]
        if (
            not row
            or row[0] != actual_id
            or actual_id == primary_id
            or row[1] != settings.RECOVERY_ENVIRONMENT
        ):
            raise RecoveryRequired(
                "The recovery journal must match this environment on an independent physical cluster."
            )
        cursor.execute(
            """SELECT rolsuper, rolcreaterole,
            has_table_privilege(current_user, 'sokoun_recovery.entries', 'UPDATE'),
            has_table_privilege(current_user, 'sokoun_recovery.entries', 'DELETE'),
            has_table_privilege(current_user, 'sokoun_recovery.entries', 'TRUNCATE'),
            has_table_privilege(current_user, 'sokoun_recovery.identity', 'INSERT'),
            has_table_privilege(current_user, 'sokoun_recovery.identity', 'UPDATE'),
            has_table_privilege(current_user, 'sokoun_recovery.identity', 'DELETE'),
            has_schema_privilege(current_user, 'sokoun_recovery', 'CREATE')
            FROM pg_roles WHERE rolname=current_user"""
        )
        if any(cursor.fetchone()):
            raise RecoveryRequired(
                "The journal runtime role must be restricted to append and read."
            )
        return actual_id

    @contextmanager
    def locked(self):
        conn = None
        try:
            conn = psycopg2.connect(
                self.dsn,
                connect_timeout=5,
                application_name="sokoun-independent-recovery",
            )
            conn.autocommit = True
            with conn.cursor() as cursor:
                cursor.execute("SET lock_timeout = '5s'")
                cursor.execute("SET statement_timeout = '15s'")
                cursor.execute("SET synchronous_commit = on")
                self.verify(cursor)
                cursor.execute("SELECT pg_advisory_lock(%s)", [LOCK_KEY])
                yield cursor
        except psycopg2.Error as exc:
            # Driver exceptions may contain credentials/hosts. Never expose them
            # in an API response. No dispatch is possible after a failed append.
            raise RecoveryRequired(
                "The independent journal is unavailable or failed integrity checks."
            ) from None
        finally:
            if conn:
                conn.close()  # Session advisory lock survives commits, not death.

    @staticmethod
    def records(cursor):
        cursor.execute(
            "SELECT sequence, payload, checksum, previous FROM sokoun_recovery.entries ORDER BY sequence"
        )
        rows, previous = [], ""
        for index, (sequence, payload, digest, predecessor) in enumerate(
            cursor.fetchall(), 1
        ):
            if (
                sequence != index
                or predecessor != previous
                or payload.get("previous") != previous
                or checksum(payload) != digest
            ):
                raise RecoveryRequired(
                    "The independent journal hash chain requires investigation."
                )
            rows.append({**payload, "checksum": digest})
            previous = digest
        return rows

    def append(self, cursor, record):
        if set(record) - LocalDrillJournal.allowed:
            raise RecoveryRequired("Unsupported journal fields.")
        if record.get("environment") != settings.RECOVERY_ENVIRONMENT:
            raise RecoveryRequired("Journal environment mismatch.")
        rows = self.records(cursor)
        item = {
            **record,
            "created_at": timezone.now().isoformat(),
            "previous": rows[-1]["checksum"] if rows else "",
        }
        digest = checksum(item)
        cursor.execute(
            "INSERT INTO sokoun_recovery.entries(sequence, payload, checksum, previous) VALUES (%s,%s::jsonb,%s,%s)",
            [len(rows) + 1, json.dumps(item), digest, item["previous"]],
        )
        # Autocommit + synchronous_commit ensure prepared is durable before the
        # caller crosses the provider boundary, independently of primary rollback.
        return {**item, "checksum": digest}

    def lookup(self, operation):
        with self.locked() as cursor:
            return [r for r in self.records(cursor) if r["operation"] == operation]

    def health(self):
        with self.locked() as cursor:
            rows = self.records(cursor)
            latest = {}
            for row in rows:
                latest[row["operation"]] = row
            return {
                "adapter": "independent_postgresql",
                "entries": len(rows),
                "chain_head": rows[-1]["checksum"] if rows else "",
                "unresolved_operations": sum(
                    r["status"] != "confirmed" for r in latest.values()
                ),
                "environment": settings.RECOVERY_ENVIRONMENT,
            }
