"""DEFERRED: independent recovery prototype; no active application consumers.

The product owner removed the independent journal/reopening dependency on
2026-10-19. This module is retained only for historical isolated drill evidence.
Ordinary account revocation and command/provider identities remain in their
own domain services. Do not import this prototype into runtime paths.

Independent recovery fence and an explicitly LOCAL drill journal.

The local fsync journal is suitable for an isolated primary-database-loss drill,
not an approved independent production failure domain. Production has no default
journal adapter and therefore cannot dispatch through this boundary.
"""

import hashlib
import json
import os
import fcntl
from contextlib import contextmanager
from pathlib import Path
from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import APIException


class RecoveryRequired(APIException):
    status_code = 503
    default_detail = "Original operations are being reconciled. Read existing receipts; do not create a replacement operation."
    default_code = "recovery_in_progress"


def state():
    location = getattr(settings, "RECOVERY_CONTROL_FILE", "")
    if not location:
        return {
            "mode": "quarantined",
            "generation": "unconfigured",
            "security_epoch": "unconfigured",
            "scopes": [],
        }
    try:
        item = json.loads(Path(location).read_text())
        required = {"mode", "generation", "security_epoch", "environment", "scopes"}
        if (
            not required.issubset(item)
            or item["environment"] != getattr(settings, "RECOVERY_ENVIRONMENT", "")
            or not isinstance(item["scopes"], list)
        ):
            raise ValueError()
        if (
            item["mode"] not in {"quarantined", "reconciling", "open"}
            or not item["generation"]
            or not item["security_epoch"]
        ):
            raise ValueError()
        return item
    except (OSError, ValueError, TypeError):
        raise RecoveryRequired()


def test_bypass():
    return getattr(
        settings, "RENTAL_RUNTIME_ENVIRONMENT", "production"
    ) == "test" and getattr(settings, "RECOVERY_TEST_BYPASS", False)


def require_scope(scope, generation=None):
    if test_bypass():
        return "isolated-test"
    control = state()
    if (
        control["mode"] != "open"
        or scope not in control["scopes"]
        or (generation is not None and generation != control["generation"])
    ):
        raise RecoveryRequired()
    # Scope approval evidence belongs outside the restored primary DB as well.
    if not control.get("approval_reference") or not control.get("coverage_reference"):
        raise RecoveryRequired()
    return control["generation"]


def security_epoch():
    return state()["security_epoch"]


def scope_available(scope):
    """For read projections only; commands must call require_scope again."""
    try:
        require_scope(scope)
        return True
    except RecoveryRequired:
        return False


class LocalDrillJournal:
    """Append-only JSONL, process-locked and fsynced before external invocation."""

    allowed = {
        "operation",
        "environment",
        "provider",
        "account",
        "kind",
        "subject_id",
        "subject_revision",
        "amount_minor",
        "currency",
        "destination_revision",
        "document_hash",
        "payload_digest",
        "generation",
        "status",
        "provider_reference",
        "event_id",
        "created_at",
    }

    def __init__(self):
        if not settings.DEBUG or not getattr(settings, "RECOVERY_LOCAL_JOURNAL", ""):
            raise RecoveryRequired(
                "An approved independent journal adapter is required."
            )
        self.path = Path(settings.RECOVERY_LOCAL_JOURNAL)
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)

    @contextmanager
    def locked(self):
        fd = os.open(self.path, os.O_CREAT | os.O_RDWR | os.O_APPEND, 0o600)
        with os.fdopen(fd, "r+", encoding="utf-8") as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            try:
                yield stream
            finally:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)

    @staticmethod
    def records(stream):
        stream.seek(0)
        try:
            rows = [json.loads(line) for line in stream if line.strip()]
        except ValueError as error:
            raise RecoveryRequired(
                "The independent journal needs integrity review."
            ) from error
        previous = ""
        for row in rows:
            record = dict(row)
            checksum = record.pop("checksum", None)
            if (
                record.get("previous") != previous
                or checksum
                != hashlib.sha256(
                    json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest()
            ):
                raise RecoveryRequired(
                    "The independent journal needs integrity review."
                )
            previous = checksum
        return rows

    def append(self, stream, record):
        if set(record) - self.allowed:
            raise RecoveryRequired("Unsupported journal fields.")
        rows = self.records(stream)
        item = {
            **record,
            "created_at": timezone.now().isoformat(),
            "previous": rows[-1]["checksum"] if rows else "",
        }
        item["checksum"] = hashlib.sha256(
            json.dumps(item, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        stream.seek(0, os.SEEK_END)
        stream.write(json.dumps(item, sort_keys=True, separators=(",", ":")) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
        directory = os.open(self.path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        return item

    def lookup(self, operation):
        with self.locked() as stream:
            return [
                row for row in self.records(stream) if row["operation"] == operation
            ]


def journal():
    # No live adapter is inferred from a local file or the primary database.
    driver = getattr(settings, "RECOVERY_JOURNAL_ADAPTER", "")
    if driver == "local_drill":
        return LocalDrillJournal()
    if driver:
        from django.utils.module_loading import import_string

        adapter = import_string(driver)()
        if getattr(adapter, "test_only", False) and not settings.DEBUG:
            raise RecoveryRequired()
        return adapter
    raise RecoveryRequired("An approved independent journal adapter is required.")


def dispatch(instruction, facts, transport):
    """No second send when a prepared record exists, even after DB restore.

    The adapter's lock must serialize this operation across workers. A prepared
    record with no outcome requires authoritative lookup, never a fresh send.
    """
    generation = require_scope("provider_outbound")
    store = journal()
    operation = f"{getattr(settings, 'RECOVERY_ENVIRONMENT', '')}:{instruction.provider}:{instruction.reference}"
    base = {
        "operation": operation,
        "environment": settings.RECOVERY_ENVIRONMENT,
        "provider": instruction.provider,
        "kind": instruction.kind,
        "subject_id": str(instruction.subject_id),
        "subject_revision": instruction.subject_revision,
        "payload_digest": instruction.request_fingerprint,
        "generation": generation,
        **facts,
    }
    with store.locked() as stream:
        previous = [
            row for row in store.records(stream) if row["operation"] == operation
        ]
        if previous:
            raise RecoveryRequired(
                "The original instruction requires reconciliation; dispatch is forbidden."
            )
        store.append(stream, {**base, "status": "prepared"})
        require_scope("provider_outbound", generation)
        try:
            provider_reference = transport()
        except Exception:
            store.append(stream, {**base, "status": "unknown"})
            raise
        # Persist the external fact even if the recovery generation changed.
        store.append(
            stream,
            {**base, "status": "confirmed", "provider_reference": provider_reference},
        )
        require_scope("provider_outbound", generation)
        return provider_reference


def reconcile_instruction(instruction):
    """Restore original dispatch evidence only; domain accounting stays canonical."""
    store = journal()
    operation = f"{settings.RECOVERY_ENVIRONMENT}:{instruction.provider}:{instruction.reference}"
    records = store.lookup(operation)
    matches = [
        row
        for row in records
        if row["status"] == "confirmed"
        and row["payload_digest"] == instruction.request_fingerprint
        and row["subject_id"] == str(instruction.subject_id)
    ]
    if not matches or len({row["provider_reference"] for row in matches}) != 1:
        return {"status": "unknown", "operation": operation}
    from django.db import transaction

    with transaction.atomic():
        current = type(instruction).objects.select_for_update().get(pk=instruction.pk)
        if (
            current.status == "confirmed"
            and current.provider_reference != matches[0]["provider_reference"]
        ):
            raise RecoveryRequired(
                "Conflicting provider evidence requires investigation."
            )
        current.status = "confirmed"
        current.provider_reference = matches[0]["provider_reference"]
        current.result = {
            "recovery": "instruction_evidence_restored",
            "domain_reconciliation_required": True,
        }
        current.save(
            update_fields=["status", "provider_reference", "result", "updated_at"]
        )
    return {
        "status": "instruction_evidence_restored",
        "operation": operation,
        "domain_reconciliation_required": True,
    }
