"""Opt-in pytest evidence: normalized routes/statuses only, never request data.

Usage: pytest -p core_apps.common.api_usage_plugin --api-usage-output=/tmp/api-usage.tsv
"""

import csv
from collections import Counter
from pathlib import Path
from threading import Lock

_counts = Counter()
_lock = Lock()
_current_test = ""
_original = None


def pytest_addoption(parser):
    parser.addoption("--api-usage-output", default=None)


def pytest_configure(config):
    if not config.getoption("--api-usage-output"):
        return
    from core_apps.common.renderers import GenericJsonRenderer
    from django.urls import resolve, Resolver404

    global _original
    _original = GenericJsonRenderer.render

    def render(self, data, accepted_media_type=None, renderer_context=None):
        result = _original(self, data, accepted_media_type, renderer_context)
        context = renderer_context or {}
        request, response = context.get("request"), context.get("response")
        if request is not None and response is not None:
            try:
                match = resolve(request.path)
                route = match.route
            except Resolver404:
                route = "<unresolved>"
            with _lock:
                _counts[
                    (request.method, route, response.status_code, _current_test)
                ] += 1
        return result

    GenericJsonRenderer.render = render


def pytest_runtest_setup(item):
    global _current_test
    _current_test = item.nodeid


def pytest_sessionfinish(session, exitstatus):
    output = session.config.getoption("--api-usage-output")
    if not output:
        return
    from core_apps.common.renderers import GenericJsonRenderer

    if _original is not None:
        GenericJsonRenderer.render = _original
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t")
        writer.writerow(["method", "route", "status", "test", "responses"])
        with _lock:
            writer.writerows([*key, count] for key, count in sorted(_counts.items()))
