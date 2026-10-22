"""Small, secret-free proof of beat -> broker -> worker execution.

Redis records expire, and only beat-published task IDs are accepted as scheduled
evidence. Calling task.run(), eager tests or manually publishing a task cannot
produce a successful scheduled-run report.
"""

import json
import hashlib
import logging
import re
import time
from uuid import uuid4

from celery import signals
from celery.beat import Scheduler
from django.conf import settings
from redis import Redis

logger = logging.getLogger(__name__)
LEASE_SECONDS = 60
EVIDENCE_SECONDS = 3600


def redis_client():
    return Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=3,
        socket_timeout=3,
    )


def namespace():
    return settings.RUNTIME_EVIDENCE_NAMESPACE


def release_sha():
    value = settings.SOKOUN_RELEASE_SHA
    return value if re.fullmatch(r"[a-fA-F0-9]{40}", value) else "unknown"


def configuration_identity():
    database = settings.DATABASES["default"]
    target = {
        name: str(database.get(name, ""))
        for name in ("ENGINE", "HOST", "PORT", "NAME", "USER")
    }
    return {
        "settings_module": settings.SETTINGS_MODULE,
        "environment": settings.RENTAL_RUNTIME_ENVIRONMENT,
        "provider_mode": settings.RENTAL_PROVIDER_BACKEND,
        "eager_tasks": settings.CELERY_TASK_ALWAYS_EAGER,
        "database_fingerprint": hashlib.sha256(
            json.dumps(target, sort_keys=True).encode()
        ).hexdigest(),
    }


def key(suffix):
    return f"sokoun:runtime:{namespace()}:{suffix}"


def write_record(client, suffix, value, ttl=EVIDENCE_SECONDS):
    client.set(key(suffix), json.dumps(value, sort_keys=True), ex=ttl)


class LeaseScheduler(Scheduler):
    """One publishing scheduler per deployment environment, including rollouts."""

    def __init__(self, *args, **kwargs):
        self.identity = str(uuid4())
        self.client = redis_client()
        super().__init__(*args, **kwargs)

    def lease(self):
        # Lua makes renewal conditional on ownership. A paused old scheduler
        # cannot renew or remove its replacement's lease.
        return bool(
            self.client.eval(
                "if redis.call('get', KEYS[1]) == ARGV[1] then "
                "return redis.call('expire', KEYS[1], ARGV[2]) end "
                "return redis.call('set', KEYS[1], ARGV[1], 'NX', 'EX', ARGV[2])",
                1,
                key("beat-lease"),
                self.identity,
                LEASE_SECONDS,
            )
        )

    def tick(self, *args, **kwargs):
        if not self.lease():
            return 5.0
        write_record(
            self.client,
            "beat",
            {
                "scheduler_id": self.identity,
                "release_sha": release_sha(),
                "configuration": configuration_identity(),
                "at": time.time(),
            },
            ttl=LEASE_SECONDS,
        )
        return min(super().tick(*args, **kwargs), 15.0)

    def apply_async(self, entry, producer=None, advance=True, **kwargs):
        if not self.lease():
            raise RuntimeError("Scheduler lease was lost before dispatch.")
        task_id = str(uuid4())
        marker = {
            "schedule": entry.name,
            "task": entry.task,
            "task_id": task_id,
            "scheduler_id": self.identity,
            "scheduler_release_sha": release_sha(),
            "scheduler_configuration": configuration_identity(),
            "dispatched_at": time.time(),
        }
        write_record(self.client, f"dispatch:{task_id}", marker)
        original = entry.options
        entry.options = {
            **original,
            "task_id": task_id,
            "headers": {**original.get("headers", {}), "sokoun_schedule": entry.name, "sokoun_dispatched_at": marker["dispatched_at"]},
        }
        try:
            return super().apply_async(
                entry, producer=producer, advance=advance, **kwargs
            )
        finally:
            entry.options = original

    def close(self):
        self.client.eval(
            "if redis.call('get', KEYS[1]) == ARGV[1] then "
            "return redis.call('del', KEYS[1]) end return 0",
            1,
            key("beat-lease"),
            self.identity,
        )
        super().close()


@signals.task_postrun.connect(weak=False)
def record_scheduled_execution(
    sender=None, task_id=None, task=None, state=None, retval=None, **kwargs
):
    if not settings.RUNTIME_EVIDENCE_ENABLED or task is None:
        return
    request = task.request
    if request.is_eager or request.called_directly:
        return
    schedule = (request.headers or {}).get("sokoun_schedule")
    expected = settings.CELERY_BEAT_SCHEDULE.get(schedule, {})
    if expected.get("task") != task.name:
        return
    try:
        client = redis_client()
        raw = client.get(key(f"dispatch:{task_id}"))
        if not raw:
            return
        marker = json.loads(raw)
        if marker.get("schedule") != schedule or marker.get("task") != task.name:
            return
        # Store counts only. Never task args, exception text, URLs, credentials,
        # document bytes or business objects in operational evidence.
        counts = {}
        if type(retval) is int:
            counts = {"affected": retval}
        elif isinstance(retval, dict):
            counts = {
                name: value
                for name, value in retval.items()
                if type(value) is int and re.fullmatch(r"[a-z_]{1,64}", str(name))
            }
        write_record(
            client,
            f"execution:{schedule}",
            {
                **marker,
                "worker_release_sha": release_sha(),
                "worker_configuration": configuration_identity(),
                "worker": str(request.hostname or "unknown")[:128],
                "completed_at": time.time(),
                "state": state,
                "counts": counts,
            },
        )
    except Exception as error:
        # Evidence failures must not turn a completed financial task into a
        # retry. The readiness command reports the absent/stale evidence.
        logger.error(
            "Scheduled execution evidence unavailable (%s)", type(error).__name__
        )


def execution_report(client, *, expected_sha, since=0, now=None):
    now = time.time() if now is None else now
    raw = client.get(key("beat"))
    beat = json.loads(raw) if raw else {}
    failures = []
    if not beat or now - beat.get("at", 0) > LEASE_SECONDS:
        failures.append("scheduler_missing_or_stale")
    elif beat.get("release_sha") != expected_sha:
        failures.append("scheduler_release_mismatch")
    elif beat.get("configuration") != configuration_identity():
        failures.append("scheduler_configuration_mismatch")
    elif client.get(key("beat-lease")) != beat.get("scheduler_id"):
        failures.append("scheduler_lease_missing")
    records = []
    for name, entry in settings.CELERY_BEAT_SCHEDULE.items():
        raw = client.get(key(f"execution:{name}"))
        record = json.loads(raw) if raw else {}
        age_limit = max(float(entry["schedule"]) * 2 + 60, 180)
        valid = (
            record.get("state") == "SUCCESS"
            and record.get("task") == entry["task"]
            and record.get("worker_release_sha") == expected_sha
            and record.get("scheduler_release_sha") == expected_sha
            and record.get("worker_configuration") == configuration_identity()
            and record.get("scheduler_configuration") == configuration_identity()
            and since
            <= record.get("dispatched_at", 0)
            <= record.get("completed_at", 0)
            <= now + 5
            and now - record.get("completed_at", 0) <= age_limit
        )
        if not valid:
            failures.append(f"scheduled_execution_unverified:{name}")
        records.append({"schedule": name, "verified": valid, "evidence": record})
    return {"scheduler": beat, "tasks": records, "failures": failures}
