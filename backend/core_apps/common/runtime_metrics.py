"""Bounded operational counts; no user identifiers, query strings or bodies."""

import hashlib
import json
import time
import math
from pathlib import Path

from django.conf import settings
from config.runtime import redis_client, key, release_sha, execution_report

BUCKETS = (50, 100, 250, 500, 1000, 2000, 5000, 60000)
WINDOW_MINUTES = 10


def record(method, route, status, elapsed_ms, *, client=None, now=None):
    if not settings.RUNTIME_METRICS_ENABLED:
        return
    now = time.time() if now is None else now
    route = route[:200]
    bucket = key(f"metrics:{int(now // 60)}")
    duration = max(round(elapsed_ms), 0)
    upper = next((limit for limit in BUCKETS if duration <= limit), "overflow")
    route_key = hashlib.sha256(f"{method}:{route}".encode()).hexdigest()[:16]
    client = client or redis_client()
    pipe = client.pipeline(transaction=True)
    for field, amount in (("requests", 1), ("server_errors", int(status >= 500)), ("duration_ms", duration), (f"latency_{upper}", 1), (f"route:{route_key}:requests", 1), (f"route:{route_key}:duration_ms", duration), (f"route:{route_key}:errors", int(status >= 500))):
        pipe.hincrby(bucket, field, amount)
    pipe.hset(bucket, f"route:{route_key}:name", f"{method} {route}")
    pipe.expire(bucket, 3600)
    pipe.execute()


class RuntimeMetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started = time.monotonic()
        response = self.get_response(request)
        if settings.RUNTIME_METRICS_ENABLED:
            match = getattr(request, "resolver_match", None)
            route = getattr(match, "route", None) or "unmatched"
            try:
                record(request.method, route, response.status_code, (time.monotonic() - started) * 1000)
            except Exception:
                # Telemetry failure cannot change or replay a business result.
                pass
        return response


def memory():
    for used, limit in (("/sys/fs/cgroup/memory.current", "/sys/fs/cgroup/memory.max"), ("/sys/fs/cgroup/memory/memory.usage_in_bytes", "/sys/fs/cgroup/memory/memory.limit_in_bytes")):
        try:
            current, maximum = int(Path(used).read_text()), int(Path(limit).read_text())
            if 0 < maximum < 2**60:
                return {"used_bytes": current, "limit_bytes": maximum, "ratio": current / maximum, "scope": "container"}
        except (OSError, ValueError):
            continue
    return {"used_bytes": None, "limit_bytes": None, "ratio": None, "scope": "unknown"}



def queue_snapshot(client, now):
    if not settings.GENERAL_BACKGROUND_ENABLED:
        return {"state": "disabled", "pending": None, "oldest_seconds": None}
    # Inspect only our dedicated Redis queue. Return metadata from Redis, never
    # a task body, arguments, credentials or arbitrary queue names.
    if settings.CELERY_BROKER_URL != settings.REDIS_URL:
        return {"state": "unavailable", "pending": None, "oldest_seconds": None}
    options = getattr(settings, "CELERY_BROKER_TRANSPORT_OPTIONS", {})
    prefix = options.get("global_keyprefix", "")
    steps = options.get("priority_steps", [0, 3, 6, 9])
    if len(steps) > 10:
        return {"state": "unavailable", "pending": None, "oldest_seconds": None}
    script = """
        local n = redis.call('llen', KEYS[1])
        local raw = redis.call('lindex', KEYS[1], -1)
        local stamp = ''
        if raw and string.len(raw) <= 262144 then
          local ok, message = pcall(cjson.decode, raw)
          if ok and type(message) == 'table' and type(message.headers) == 'table' then
            stamp = tostring(message.headers.sokoun_dispatched_at or '')
          end
        end
        return {n, stamp}
    """
    pending, timestamps, unknown = 0, [], 0
    for priority in steps:
        name = prefix + "sokoun-general" + ("\x06\x16" + str(priority) if priority else "")
        count, stamp = client.eval(script, 1, name)
        pending += int(count)
        try:
            stamp = float(stamp)
            if not math.isfinite(stamp) or stamp <= 0 or stamp > now + 5: raise ValueError()
            timestamps.append(stamp)
        except (TypeError, ValueError):
            unknown += int(bool(count))
    return {"state": "measured", "pending": pending,
        "oldest_seconds": max(0, now-min(timestamps)) if timestamps and not unknown else None,
        "queues_with_unknown_age": unknown}

def snapshot(*, client=None, now=None):
    now = time.time() if now is None else now
    result = {"measured_at": now, "window_seconds": WINDOW_MINUTES * 60, "state": "unavailable", "requests": None, "server_errors": None, "error_rate": None, "average_ms": None, "p95_upper_ms": None, "p95_lower_ms": None, "routes": [], "memory": memory(), "release_sha": release_sha(), "runtime": None, "queue": {"state": "unavailable", "pending": None, "oldest_seconds": None}}
    if not settings.RUNTIME_METRICS_ENABLED:
        return result
    try:
        client = client or redis_client()
        pipe = client.pipeline()
        for minute in range(int(now // 60) - WINDOW_MINUTES + 1, int(now // 60) + 1):
            pipe.hgetall(key(f"metrics:{minute}"))
        rows = pipe.execute()
        count = sum(int(row.get("requests", 0)) for row in rows)
        errors = sum(int(row.get("server_errors", 0)) for row in rows)
        elapsed = sum(int(row.get("duration_ms", 0)) for row in rows)
        p95, p95_lower, seen, previous_limit = None, None, 0, 0
        for limit in BUCKETS:
            seen += sum(int(row.get(f"latency_{limit}", 0)) for row in rows)
            if count and seen >= count * .95:
                p95, p95_lower = limit, previous_limit
                break
            previous_limit = limit
        overflow = sum(int(row.get("latency_overflow", 0)) for row in rows)
        if count and p95 is None and seen + overflow >= count * .95:
            p95_lower = BUCKETS[-1]
        routes = {}
        for row in rows:
            for field, name in row.items():
                if not field.startswith("route:") or not field.endswith(":name"):
                    continue
                prefix = field[:-4]
                route = routes.setdefault(name, {"route": name, "requests": 0, "errors": 0, "duration_ms": 0})
                for metric in ("requests", "errors", "duration_ms"):
                    route[metric] += int(row.get(prefix + metric, 0))
        result.update(state="measured" if count else "no_samples", requests=count, server_errors=errors, error_rate=errors / count if count else None, average_ms=elapsed / count if count else None, p95_upper_ms=p95, p95_lower_ms=p95_lower, routes=sorted(routes.values(), key=lambda item: -item["requests"])[:40])
        result["queue"] = queue_snapshot(client, now)
        if settings.GENERAL_BACKGROUND_ENABLED:
            result["runtime"] = execution_report(client, expected_sha=release_sha(), now=now)
    except Exception:
        result["state"] = "unavailable"
    return result


def evaluate_incidents(report):
    from .runtime_models import RuntimeIncident
    from django.utils import timezone
    from django.db import transaction

    latency = report.get("p95_upper_ms")
    if latency is None:
        latency = report.get("p95_lower_ms")
    conditions = {
        "runtime.telemetry": report["state"] == "unavailable",
        "runtime.api_errors": None if report["requests"] is None or report["requests"] < 100 else (report["error_rate"] or 0) > .01,
        "runtime.api_latency": None if report["requests"] is None or report["requests"] < 100 or latency is None else latency > 2000,
        "runtime.memory": None if report["memory"]["ratio"] is None else report["memory"]["ratio"] >= .8,
        "runtime.scheduler": None if report["runtime"] is None else bool(report["runtime"]["failures"]),
    }
    queue = report.get("queue", {})
    conditions["runtime.queue_backlog"] = None if queue.get("pending") is None else queue["pending"] >= 100
    conditions["runtime.queue_delay"] = (
        False if queue.get("state") == "measured" and queue.get("pending") == 0
        else None if queue.get("oldest_seconds") is None
        else queue["oldest_seconds"] >= 180
    )
    now = timezone.now()
    for code, active in conditions.items():
        if active is None:
            continue
        with transaction.atomic():
            item, created = RuntimeIncident.objects.get_or_create(code=code, defaults={"state": "open" if active else "resolved", "occurrences": int(active), "opened_at": now if active else None})
            item = RuntimeIncident.objects.select_for_update().get(pk=item.pk)
            if active:
                if item.state != "open":
                    item.occurrences += 1
                    item.opened_at = now
                item.state, item.resolved_at = "open", None
                item.last_seen_at = now
            elif item.state == "open":
                item.state, item.resolved_at = "resolved", now
            item.save()
    return RuntimeIncident.objects.filter(state="open").count()
