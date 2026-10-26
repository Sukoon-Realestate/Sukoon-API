"""Exercise local Redis/Celery recovery in a disposable clone of a test database.

Run with backend/.venv Python. Never connects to a deployed broker or database.
Provider, device and deployed-worker acceptance remain separate.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from uuid import uuid4

import psycopg2
from psycopg2 import sql
from redis import Redis


def until(check, description, timeout=35):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if check():
            return
        time.sleep(0.15)
    raise RuntimeError(f"Timed out: {description}")


def stop(process):
    if process and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", required=True)
    parser.add_argument("--postgres-port", type=int, default=55446)
    parser.add_argument("--postgres-user", default="plan_tester")
    args = parser.parse_args()
    if not args.template.startswith("test_sokoun_"):
        parser.error("Only an isolated test_sokoun_* template is permitted.")
    root = Path(__file__).resolve().parents[2]
    output = Path(tempfile.mkdtemp(prefix="sokoun-cycle-workers-"))
    database = "sokoun_cycles_worker_" + uuid4().hex[:12]
    queue = "sokoun-cycles-qa"
    redis_server = shutil.which("redis-server")
    if not redis_server:
        parser.error("An existing local redis-server installation is required.")
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        redis_port = listener.getsockname()[1]
    broker = f"redis://127.0.0.1:{redis_port}/0"
    redis = Redis.from_url(broker, decode_responses=True)
    admin = psycopg2.connect(
        host="127.0.0.1",
        port=args.postgres_port,
        user=args.postgres_user,
        dbname="postgres",
    )
    admin.autocommit = True
    worker = beat = server = holder = None
    created = False
    logs = []
    summary = {
        "local_only": True,
        "provider_transactions": False,
        "physical_device": False,
    }
    try:
        with admin.cursor() as cursor:
            cursor.execute(
                sql.SQL("CREATE DATABASE {} TEMPLATE {}").format(
                    sql.Identifier(database), sql.Identifier(args.template)
                )
            )
        created = True
        log = (output / "redis.log").open("wb")
        logs.append(log)
        server = subprocess.Popen(
            [
                redis_server,
                "--bind",
                "127.0.0.1",
                "--port",
                str(redis_port),
                "--save",
                "",
                "--appendonly",
                "no",
            ],
            stdout=log,
            stderr=subprocess.STDOUT,
        )

        def redis_ready():
            try:
                return redis.ping()
            except Exception:
                return False

        until(redis_ready, "local Redis readiness")
        settings_file = output / "cycle_worker_settings.py"
        schedule = {
            "qa-probe": {
                "task": "core_apps.common.tasks.background_probe",
                "schedule": 1.0,
                "options": {"queue": queue},
            }
        }
        settings_file.write_text(
            f"""from config.settings.postgres_test import *
from kombu import Queue
ALLOWED_HOSTS = ["testserver", "127.0.0.1", "localhost"]
REDIS_URL = CELERY_BROKER_URL = CELERY_RESULT_BACKEND = {broker!r}
CELERY_BROKER_USE_SSL = CELERY_REDIS_BACKEND_USE_SSL = None
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_DEFAULT_QUEUE = {queue!r}
CELERY_TASK_QUEUES = (Queue({queue!r}),)
CELERY_TASK_ROUTES = {{}}
CELERY_BEAT_SCHEDULER = "config.runtime:LeaseScheduler"
CELERY_BEAT_SCHEDULE = {schedule!r}
RUNTIME_EVIDENCE_ENABLED = True
RUNTIME_EVIDENCE_NAMESPACE = {database!r}
SOKOUN_RELEASE_SHA = {subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()!r}
GENERAL_BACKGROUND_ENABLED = True
GENERAL_BACKGROUND_ALLOWED_TASKS = (
    "core_apps.common.tasks.background_probe", "features.process_tender_packages",
    "advanced_housing.recover_jobs",
    "core_apps.features.tasks_parts.expire_rental_sources_and_holds.process_planning_jobs",
)
RENTAL_PROVIDER_BACKEND = "disabled"
RENTAL_FAKE_PROVIDER_ALLOWED = False
RENTAL_CHECKOUT_ENABLED = False
SIGNWELL_TEST_ENABLED = False
SIGNWELL_API_KEY = ""
PLANNING_ROUTES_API_KEY = PLANNING_GEMINI_API_KEY = ""
ADVANCED_HOUSING_ENABLED_SERVICES = ["collective_tender_planning"]
"""
        )
        os.environ.update(
            DJANGO_SETTINGS_MODULE="cycle_worker_settings",
            TEST_POSTGRES_DB=database,
            TEST_POSTGRES_USER=args.postgres_user,
            TEST_POSTGRES_HOST="127.0.0.1",
            TEST_POSTGRES_PORT=str(args.postgres_port),
            PYTHONPATH=os.pathsep.join([str(output), str(root)]),
            SOKOUN_WORKER_PROFILE="general",
            PGAPPNAME=database,
        )
        sys.path[:0] = [str(output), str(root)]
        import django

        django.setup()
        from django.conf import settings
        from django.db import connections
        from django.core.management import call_command
        from config.celery import app
        from config.runtime import execution_report
        from core_apps.features.tests.test_rental_phase2 import rental_participants
        from core_apps.features.tests.test_advanced_tenders import scenario, published
        from core_apps.features.tests.test_advanced_tender_construction import (
            two_unit_bid,
            start,
        )
        from core_apps.features.advanced_tender_models import TenderPackageRun
        from core_apps.features.planning_models import PlanningEvent

        # This database was created above exclusively for this run.
        assert settings.DATABASES["default"]["NAME"] == database
        call_command("flush", interactive=False, verbosity=0)
        s = scenario.__wrapped__(rental_participants.__wrapped__(None))
        tender = published(s)
        two_unit_bid(s, tender)
        first = start(s, tender)
        assert redis.llen(queue) > 0
        summary["queued_with_worker_stopped"] = True

        def launch_worker():
            log = (output / "worker.log").open("ab")
            logs.append(log)
            return subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "celery",
                    "-A",
                    "config.celery",
                    "worker",
                    "--pool=solo",
                    "--concurrency=1",
                    "--loglevel=INFO",
                    "-Q",
                    queue,
                    "--hostname=cycles-qa@localhost",
                    "--without-gossip",
                    "--without-mingle",
                ],
                cwd=root,
                stdout=log,
                stderr=subprocess.STDOUT,
                env=os.environ.copy(),
            )

        def completed(identity):
            return TenderPackageRun.objects.filter(
                id=identity, status="feasible"
            ).exists()

        worker = launch_worker()
        until(lambda: completed(first["id"]), "worker consumes the queued construction")
        summary["queued_job_processed"] = True
        app.send_task("core_apps.common.tasks.background_probe", queue=queue).get(
            timeout=10
        )
        app.send_task(
            "core_apps.features.tasks_parts.expire_rental_sources_and_holds.process_planning_jobs",
            queue=queue,
        ).get(timeout=20)
        assert PlanningEvent.objects.filter(notification__isnull=False).exists()
        summary["planning_inbox_delivered"] = True
        stop(worker)
        worker = None

        second = start(s, tender)
        holder = psycopg2.connect(
            host="127.0.0.1",
            port=args.postgres_port,
            user=args.postgres_user,
            dbname=database,
        )
        with holder.cursor() as cursor:
            cursor.execute(
                "SELECT pkid FROM features_tenderpackagerun WHERE id = %s FOR UPDATE",
                (second["id"],),
            )
        worker = launch_worker()

        def worker_blocked():
            with admin.cursor() as cursor:
                cursor.execute(
                    "SELECT count(*) FROM pg_stat_activity WHERE datname=%s AND application_name=%s AND wait_event_type='Lock'",
                    (database, database),
                )
                return cursor.fetchone()[0] > 0

        until(worker_blocked, "worker holds the broker message while awaiting its row")
        worker.kill()  # Only the disposable solo worker created by this script.
        worker.wait(timeout=5)
        worker = None
        holder.rollback()
        holder.close()
        holder = None
        assert TenderPackageRun.objects.get(id=second["id"]).status == "queued"
        worker = launch_worker()
        app.send_task("advanced_housing.recover_jobs", queue=queue).get(timeout=30)
        until(
            lambda: completed(second["id"]),
            "durable job recovery after worker interruption",
        )
        current = TenderPackageRun.objects.get(id=second["id"])
        count = current.packages.count()
        notices = PlanningEvent.objects.filter(
            destination__source_id=second["id"]
        ).count()
        app.send_task(
            "features.process_tender_packages", args=[second["id"]], queue=queue
        ).get(timeout=15)
        assert current.packages.count() == count
        assert (
            PlanningEvent.objects.filter(destination__source_id=second["id"]).count()
            == notices
        )
        summary["interrupted_job_recovered_once"] = True

        log = (output / "beat.log").open("wb")
        logs.append(log)
        beat = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "celery",
                "-A",
                "config.celery",
                "beat",
                "--loglevel=INFO",
                "--schedule",
                str(output / "beat-state"),
            ],
            cwd=root,
            stdout=log,
            stderr=subprocess.STDOUT,
            env=os.environ.copy(),
        )
        until(
            lambda: not execution_report(
                redis, expected_sha=settings.SOKOUN_RELEASE_SHA
            )["failures"],
            "beat/broker/worker scheduled evidence",
        )
        report = execution_report(redis, expected_sha=settings.SOKOUN_RELEASE_SHA)
        summary["scheduled_probe_verified"] = all(
            row["verified"] for row in report["tasks"]
        )
        summary["scheduled_tasks_verified"] = [
            row["schedule"] for row in report["tasks"]
        ]
        summary["result"] = "passed"
        print(json.dumps(summary, sort_keys=True), flush=True)
    finally:
        if holder:
            holder.rollback()
            holder.close()
        stop(beat)
        stop(worker)
        stop(server)
        if "connections" in locals():
            connections.close_all()
        if created:
            with admin.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=%s",
                    (database,),
                )
                cursor.execute(
                    sql.SQL("DROP DATABASE {}").format(sql.Identifier(database))
                )
        admin.close()
        for log in logs:
            log.close()
        summary["resources_stopped"] = True
        (output / "result.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(f"Local evidence: {output}", flush=True)


if __name__ == "__main__":
    main()
