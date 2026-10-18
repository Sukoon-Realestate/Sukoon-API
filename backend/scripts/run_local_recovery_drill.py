"""Real pg_dump/pg_restore of disposable, synthetic local data; no live providers.

Run with the backend virtualenv, --port for an already-owned local PostgreSQL
server and --output for a sanitized JSON report. This command never accepts a
database name or a remote host. It creates and removes its own UUID database.
The journal/control plane remain outside the restored database. They are LOCAL
drill evidence, not an approved production failure domain or RPO/RTO.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
SCOPES = [
    "provider_outbound",
    "inventory_commitments",
    "private_artifacts",
    "notifications",
    "company_mail",
]


def write_json(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.chmod(temporary, 0o600)
    with temporary.open("rb") as handle:
        os.fsync(handle.fileno())
    temporary.replace(path)


def stage(phase, folder):
    sys.path.insert(0, str(ROOT))
    os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.postgres_test"
    import django

    django.setup()
    from django.conf import settings
    from core_apps.common.recovery import (
        RecoveryRequired,
        dispatch,
        reconcile_instruction,
        require_scope,
    )
    from core_apps.features.models import RentalProviderInstruction, LedgerTransaction
    from core_apps.features.services.rental_phase3_parts.issue_invoice import (
        post_ledger_transaction,
    )
    from core_apps.users.models import User
    from core_apps.users.services.sessions import (
        issue_refresh,
        revoke_all,
        validate_session,
    )
    from rest_framework_simplejwt.exceptions import AuthenticationFailed
    from rest_framework_simplejwt.tokens import RefreshToken

    assert settings.DATABASES["default"]["HOST"] == "127.0.0.1"
    assert settings.DATABASES["default"]["NAME"].startswith("sokoun_recovery_drill_")
    settings.DEBUG = True
    settings.RECOVERY_TEST_BYPASS = False
    settings.RECOVERY_ENVIRONMENT = "isolated-local-restore"
    settings.RECOVERY_CONTROL_FILE = str(folder / "control.json")
    settings.RECOVERY_LOCAL_JOURNAL = str(folder / "journal.jsonl")
    settings.RECOVERY_JOURNAL_ADAPTER = "local_drill"
    control_path = Path(settings.RECOVERY_CONTROL_FILE)
    fixture_path = folder / "fixture.private.json"
    effects_path = folder / "synthetic-provider-effects.json"

    def control(mode, generation, epoch):
        write_json(
            control_path,
            {
                "environment": settings.RECOVERY_ENVIRONMENT,
                "mode": mode,
                "generation": generation,
                "security_epoch": epoch,
                "scopes": SCOPES if mode == "open" else [],
                "approval_reference": "SYNTHETIC-LOCAL-DRILL-ONLY",
                "coverage_reference": "SYNTHETIC-LOCAL-DRILL-ONLY",
            },
        )

    def ledger(item):
        return post_ledger_transaction(
            reference="local-drill:" + str(item.pk),
            kind="synthetic_recovery",
            entries=[
                ("synthetic_clearing", "debit", 700),
                ("synthetic_payable", "credit", 700),
            ],
            metadata={
                "instruction": str(item.pk),
                "provider_reference": "synthetic-confirmed-001",
            },
        )

    if phase == "before":
        control("open", "generation-1", "epoch-1")
        user = User.objects.create_user(
            email="restore-drill@example.invalid",
            password="SyntheticLocalOnly123!",
            is_active=True,
            is_verified=True,
        )
        claims = str(issue_refresh(user))
        ids = []
        for suffix in ("confirmed", "unknown"):
            item = RentalProviderInstruction.objects.create(
                reference="local-drill:" + suffix,
                provider="synthetic",
                kind="payout",
                subject_id=uuid.uuid4(),
                subject_revision=1,
                request_fingerprint=hashlib.sha256(suffix.encode()).hexdigest(),
            )
            ids.append(str(item.pk))
        write_json(
            fixture_path,
            {"user_id": str(user.pk), "claims": claims, "instructions": ids},
        )
        write_json(effects_path, {"confirmed": 0, "unknown": 0})
        return {"instructions_before_backup": 2, "ledger_before_backup": 0}

    fixture = json.loads(fixture_path.read_text())
    user = User.objects.get(pk=fixture["user_id"])
    confirmed, unknown = [
        RentalProviderInstruction.objects.get(pk=pk) for pk in fixture["instructions"]
    ]

    def effect(kind):
        effects = json.loads(effects_path.read_text())
        effects[kind] += 1
        write_json(effects_path, effects)
        if kind == "unknown":
            raise TimeoutError(
                "Synthetic provider accepted instruction but response was lost"
            )
        return "synthetic-confirmed-001"

    facts = {
        "account": "synthetic-local-only",
        "amount_minor": 700,
        "currency": "EGP",
        "destination_revision": 1,
    }
    if phase == "after":
        confirmed.provider_reference = dispatch(
            confirmed, facts, lambda: effect("confirmed")
        )
        confirmed.status = "confirmed"
        confirmed.save()
        ledger(confirmed)
        try:
            dispatch(unknown, facts, lambda: effect("unknown"))
        except TimeoutError:
            pass
        revoke_all(user, action="local_restore_drill", freeze=True)
        control("quarantined", "generation-2", "epoch-2")
        assert LedgerTransaction.objects.count() == 1
        return {
            "ledger_after_backup": 1,
            "external_effects": json.loads(effects_path.read_text()),
            "db_epoch_after_backup": 1,
        }

    assert phase == "restored"
    assert confirmed.status == "pending"
    assert LedgerTransaction.objects.count() == 0
    assert user.security_epoch == 0
    blocked = []
    for scope in SCOPES:
        try:
            require_scope(scope)
        except RecoveryRequired:
            blocked.append(scope)
        else:
            raise AssertionError("Restored scope reopened without reconciliation")
    try:
        validate_session(user, RefreshToken(fixture["claims"]))
    except AuthenticationFailed:
        token_blocked = True
    else:
        raise AssertionError("Restored stale authority was accepted")
    control("reconciling", "generation-2", "epoch-2")
    receipt = reconcile_instruction(confirmed)
    assert receipt["domain_reconciliation_required"]
    confirmed.refresh_from_db()
    ledger(confirmed)
    reconcile_instruction(confirmed)
    ledger(confirmed)
    assert LedgerTransaction.objects.count() == 1
    assert LedgerTransaction.objects.get().entries.count() == 2
    assert reconcile_instruction(unknown)["status"] == "unknown"
    control("open", "generation-3", "epoch-2")
    duplicate_denials = 0
    for item in (confirmed, unknown):
        try:
            dispatch(item, facts, lambda: effect("confirmed"))
        except RecoveryRequired:
            duplicate_denials += 1
    assert duplicate_denials == 2
    assert json.loads(effects_path.read_text()) == {"confirmed": 1, "unknown": 1}
    control("quarantined", "generation-4", "epoch-2")
    return {
        "restored_pending_instructions": 2,
        "restored_missing_ledger_transactions": 1,
        "blocked_scopes_before_reconciliation": blocked,
        "restored_token_rejected": token_blocked,
        "canonical_ledger_transactions_after_two_replays": 1,
        "canonical_ledger_entries": 2,
        "duplicate_dispatches_denied": duplicate_denials,
        "unknown_outcome": "manual_reconciliation_required",
        "external_effects_after_reconciliation": json.loads(effects_path.read_text()),
        "final_mode": "quarantined",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--user", default="closure_test")
    parser.add_argument(
        "--pg-bin", type=Path, default=Path("/opt/homebrew/opt/postgresql@16/bin")
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--phase", choices=["before", "after", "restored"])
    parser.add_argument("--folder", type=Path)
    args = parser.parse_args()
    if args.phase:
        print(json.dumps(stage(args.phase, args.folder), sort_keys=True))
        return
    if args.output is None:
        parser.error("--output is required")
    database = "sokoun_recovery_drill_" + uuid.uuid4().hex[:16]
    env = {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": "config.settings.postgres_test",
        "TEST_POSTGRES_DB": database,
        "TEST_POSTGRES_USER": args.user,
        "TEST_POSTGRES_HOST": "127.0.0.1",
        "TEST_POSTGRES_PORT": str(args.port),
        "PGPASSWORD": "",
        "PGHOST": "127.0.0.1",
        "PGPORT": str(args.port),
        "PGUSER": args.user,
    }
    env.pop("TEST_POSTGRES_PASSWORD", None)
    env.pop("PGSERVICE", None)
    env.pop("PGSERVICEFILE", None)
    conn = ["-h", "127.0.0.1", "-p", str(args.port), "-U", args.user]
    started = datetime.now(timezone.utc).isoformat()
    before_time = time.monotonic()
    report = {
        "started_at": started,
        "environment": "isolated-local-postgresql",
        "provider": "synthetic-local-effect-file",
        "production_approval": False,
        "approved_rpo": None,
        "approved_rto": None,
        "commands": [],
        "phases": {},
    }

    def run(command):
        result = subprocess.run(
            command, env=env, cwd=ROOT, text=True, capture_output=True
        )
        if result.returncode:
            raise RuntimeError(
                f"{Path(command[0]).name} failed: {result.stderr[-4000:]}"
            )
        report["commands"].append(Path(command[0]).name)
        return result.stdout

    created = False
    try:
        run([str(args.pg_bin / "createdb"), *conn, "--template=template0", database])
        created = True
        with tempfile.TemporaryDirectory(
            prefix="sokoun-isolated-restore-"
        ) as temporary:
            folder = Path(temporary)
            run(
                [
                    sys.executable,
                    "manage.py",
                    "migrate",
                    "--noinput",
                    "--verbosity",
                    "0",
                ]
            )

            def phase(name):
                value = run(
                    [
                        sys.executable,
                        str(Path(__file__).resolve()),
                        "--port",
                        str(args.port),
                        "--phase",
                        name,
                        "--folder",
                        str(folder),
                    ]
                )
                report["phases"][name] = json.loads(value.strip().splitlines()[-1])

            phase("before")
            backup = folder / "synthetic-primary.dump"
            run(
                [
                    str(args.pg_bin / "pg_dump"),
                    *conn,
                    "-Fc",
                    "--file",
                    str(backup),
                    database,
                ]
            )
            report["backup_sha256"] = hashlib.sha256(backup.read_bytes()).hexdigest()
            phase("after")
            restore_start = time.monotonic()
            run(
                [
                    str(args.pg_bin / "pg_restore"),
                    *conn,
                    "--clean",
                    "--if-exists",
                    "--exit-on-error",
                    "--dbname",
                    database,
                    str(backup),
                ]
            )
            report["restore_seconds"] = round(time.monotonic() - restore_start, 3)
            phase("restored")
            report["journal_sha256"] = hashlib.sha256(
                (folder / "journal.jsonl").read_bytes()
            ).hexdigest()
            report["status"] = "passed_local_only"
    finally:
        if created:
            run([str(args.pg_bin / "dropdb"), *conn, database])
            report["disposable_database_removed"] = True
    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    report["elapsed_seconds"] = round(time.monotonic() - before_time, 3)
    report["limits"] = [
        "No live provider, PITR, production backup or physical device was used.",
        "Local journal and control files are not an approved independent production store.",
        "Synthetic accounting mapping was explicit; production refund/payout/signature/role/artifact reconciliation remains provider and policy dependent.",
        "Measured duration is evidence for this small fixture only, never an approved RTO.",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.output, report)
    print(
        json.dumps(
            {
                "status": report["status"],
                "report": str(args.output),
                "elapsed_seconds": report["elapsed_seconds"],
            }
        )
    )


if __name__ == "__main__":
    main()
