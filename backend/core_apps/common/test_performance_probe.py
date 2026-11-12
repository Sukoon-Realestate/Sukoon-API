"""Instrumentation reports real work without changing transport or transactions."""

from unittest.mock import patch

import pytest
import requests
from django.db import transaction
from django.http import HttpResponse
from tools.qa.performance import measured


@pytest.mark.django_db
def test_probe_records_rendered_bytes_provider_calls_and_atomic_spans():
    def operation():
        with transaction.atomic():
            requests.Session().get("https://synthetic.invalid/probe")
        return HttpResponse("مرحبا", content_type="text/plain; charset=utf-8")

    with patch.object(requests.sessions.Session, "request", return_value=object()):
        response, report = measured("probe", 10, operation)
    assert report["http_calls"] == 1
    assert report["transaction_spans"] == 1
    assert report["max_transaction_seconds"] > 0
    assert report["payload_bytes"] == len(response.content)
    assert report["payload_measure"] == "rendered"
    assert report["rows_inspected"] is None
    assert report["cpu_seconds"] >= 0


@pytest.mark.django_db
def test_probe_cleans_up_on_failure_and_preserves_an_existing_trace():
    import tracemalloc

    original = requests.sessions.Session.request
    tracemalloc.start()
    try:
        with pytest.raises(ValueError, match="injected"):
            measured("fault", 1, lambda: (_ for _ in ()).throw(ValueError("injected")))
        assert tracemalloc.is_tracing()
        assert requests.sessions.Session.request is original
    finally:
        tracemalloc.stop()
