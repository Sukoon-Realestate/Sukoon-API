"""Read-only runtime evidence; never runs or schedules business tasks."""

import json
from datetime import datetime

from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from config.runtime import (
    configuration_identity,
    execution_report,
    redis_client,
    release_sha,
)


class Command(BaseCommand):
    help = "Verify PostgreSQL, migrations, Redis, settings, and actual scheduled worker completions."

    def add_arguments(self, parser):
        parser.add_argument("--expected-sha", required=True)
        parser.add_argument(
            "--profile", choices=["staging_mock", "probe", "general"], default="staging_mock"
        )
        parser.add_argument(
            "--since",
            help="Require tasks dispatched after this ISO-8601 UTC timestamp.",
        )

    def handle(self, *args, **options):
        since = 0
        if options["since"]:
            try:
                instant = datetime.fromisoformat(
                    options["since"].replace("Z", "+00:00")
                )
                if instant.tzinfo is None:
                    raise ValueError
                since = instant.timestamp()
            except ValueError as error:
                raise CommandError(
                    "--since requires an ISO-8601 timestamp with timezone."
                ) from error
        report = {
            "release_sha": release_sha(),
            "configuration": configuration_identity(),
            "failures": [],
            "checks": {},
        }
        failures = report["failures"]
        if release_sha() == "unknown" or release_sha() != options["expected_sha"]:
            failures.append("api_release_mismatch")
        profile = options["profile"]
        report["verification_scope"] = (
            "isolated_transport_only"
            if profile == "probe"
            else "explicit_general_schedules" if profile == "general"
            else "staging_mock_schedules"
        )
        profile_checks = (
            {
                "probe_settings": settings.SETTINGS_MODULE
                == "config.settings.background_probe",
                "providers_disabled": settings.RENTAL_PROVIDER_BACKEND == "disabled"
                and not settings.RENTAL_FAKE_PROVIDER_ALLOWED,
                "isolated_schedule": set(settings.CELERY_BEAT_SCHEDULE)
                == {"background-connectivity-probe"},
                "isolated_queue": settings.CELERY_TASK_DEFAULT_QUEUE
                == "sokoun-background-probe",
            }
            if profile == "probe"
            else {
                "staging_mock": settings.SETTINGS_MODULE
                == "config.settings.staging_mock",
                "fake_provider_explicit": settings.RENTAL_PROVIDER_BACKEND == "fake"
                and settings.RENTAL_FAKE_PROVIDER_ALLOWED,
            }
        )
        if profile == "general":
            scheduled = settings.CELERY_BEAT_SCHEDULE
            profile_checks = {
                "general_enabled": settings.GENERAL_BACKGROUND_ENABLED,
                "explicit_task_admission": bool(scheduled) and
                    {entry["task"] for entry in scheduled.values()} ==
                    set(settings.GENERAL_BACKGROUND_ALLOWED_TASKS),
                "separate_general_queue": bool(scheduled) and all(
                    entry.get("options", {}).get("queue") == "sokoun-general"
                    for entry in scheduled.values()
                ),
                "single_task_prefetch": settings.CELERY_WORKER_PREFETCH_MULTIPLIER == 1,
            }
        for name, passed in {
            "debug_disabled": settings.DEBUG is False,
            **profile_checks,
            "worker_execution_not_eager": not settings.CELERY_TASK_ALWAYS_EAGER,
            "runtime_evidence_enabled": settings.RUNTIME_EVIDENCE_ENABLED,
            "redis_channels": settings.CHANNEL_LAYERS["default"]["BACKEND"]
            == "channels_redis.core.RedisChannelLayer",
            "shared_security_cache": settings.CACHES["default"]["BACKEND"]
            == "django.core.cache.backends.redis.RedisCache",
        }.items():
            report["checks"][name] = passed
            if not passed:
                failures.append(name)
        try:
            connection.ensure_connection()
            report["checks"]["postgresql"] = connection.vendor == "postgresql"
            if connection.vendor != "postgresql":
                failures.append("postgresql_required")
            executor = MigrationExecutor(connection)
            pending = executor.migration_plan(executor.loader.graph.leaf_nodes())
            report["checks"]["migrations_applied"] = not pending
            if pending:
                failures.append("pending_migrations")
        except Exception as error:
            failures.append(f"database_unavailable:{type(error).__name__}")
        try:
            client = redis_client()
            report["checks"]["redis"] = bool(client.ping())
            scheduled = execution_report(
                client, expected_sha=options["expected_sha"], since=since
            )
            failures.extend(scheduled.pop("failures"))
            report.update(scheduled)
        except Exception as error:
            failures.append(f"runtime_evidence_unavailable:{type(error).__name__}")
        try:
            # A read checks the configured cache connection without creating an
            # OTP, resetting a limit, or flushing shared Redis data.
            cache.get("runtime-readiness:cache-connectivity")
            report["checks"]["security_cache_reachable"] = True
        except Exception as error:
            report["checks"]["security_cache_reachable"] = False
            failures.append(f"security_cache_unavailable:{type(error).__name__}")
        report["ready"] = not failures
        self.stdout.write(json.dumps(report, indent=2, sort_keys=True))
        if failures:
            raise CommandError(
                "Runtime readiness is incomplete; see the sanitized JSON report."
            )
