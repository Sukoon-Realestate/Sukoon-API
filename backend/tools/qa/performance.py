"""Local probe measurements. Import explicitly in tests; never install in production.

Payloads are renderer bytes for HTTP responses, JSON estimates for projections.
Query execution time includes lock acquisition; transaction spans cover only
Atomic blocks entered by the measured call. These are not production SLOs.
"""

from contextlib import ExitStack
import json
from pathlib import Path
import os
from time import perf_counter, process_time
import tracemalloc
from unittest.mock import patch

from django.core.files.storage import FileSystemStorage
from django.db import connection, transaction
from django.test.utils import CaptureQueriesContext
import requests


def measured(name, size, operation):
    provider = {"http_calls": 0, "http_seconds": 0.0, "storage_exists_calls": 0}
    transactions, entered = [], {}
    request = requests.sessions.Session.request
    exists = FileSystemStorage.exists
    enter, leave = transaction.Atomic.__enter__, transaction.Atomic.__exit__

    def http(session, *args, **kwargs):
        provider["http_calls"] += 1
        start = perf_counter()
        try:
            return request(session, *args, **kwargs)
        finally:
            provider["http_seconds"] += perf_counter() - start

    def storage(store, *args, **kwargs):
        provider["storage_exists_calls"] += 1
        return exists(store, *args, **kwargs)

    def begin(block):
        result = enter(block)
        entered.setdefault(id(block), []).append(perf_counter())
        return result

    def end(block, *args):
        pending = entered.get(id(block))
        if not pending:
            return leave(block, *args)
        start = pending.pop()
        try:
            return leave(block, *args)
        finally:
            transactions.append(perf_counter() - start)

    already_tracing = tracemalloc.is_tracing()
    if not already_tracing:
        tracemalloc.start()
    baseline, _ = tracemalloc.get_traced_memory()
    started, cpu = perf_counter(), process_time()
    try:
        with ExitStack() as stack:
            stack.enter_context(patch.object(requests.sessions.Session, "request", http))
            stack.enter_context(patch.object(FileSystemStorage, "exists", storage))
            stack.enter_context(patch.object(transaction.Atomic, "__enter__", begin))
            stack.enter_context(patch.object(transaction.Atomic, "__exit__", end))
            queries = stack.enter_context(CaptureQueriesContext(connection))
            result = operation()
        elapsed, cpu_elapsed = perf_counter() - started, process_time() - cpu
        _, peak = tracemalloc.get_traced_memory()
    finally:
        if not already_tracing:
            tracemalloc.stop()
    rendered = hasattr(result, "content") and not getattr(result, "streaming", False)
    payload = result.content if rendered else json.dumps(result, default=str).encode()
    report = {
        "case": name,
        "size": size,
        "queries": len(queries),
        "seconds": elapsed,
        "cpu_seconds": cpu_elapsed,
        "peak_python_bytes": max(0, peak - baseline),
        "heap_scope": "shared_trace_peak" if already_tracing else "probe_peak",
        "payload_bytes": len(payload),
        "payload_measure": "rendered" if rendered else "projection_json",
        "transaction_spans": len(transactions),
        "max_transaction_seconds": max(transactions, default=0.0),
        "caller_in_atomic": connection.in_atomic_block,
        "lock_queries": sum(
            "FOR UPDATE" in row["sql"].upper() or "FOR NO KEY UPDATE" in row["sql"].upper() for row in queries
        ),
        "rows_inspected": None,  # Requires explicit EXPLAIN/algorithm instrumentation.
        **provider,
    }
    if os.environ.get("SPRINT04_METRICS"):
        with Path(os.environ["SPRINT04_METRICS"]).open("a") as stream:
            stream.write(json.dumps(report) + "\n")
    return result, report
