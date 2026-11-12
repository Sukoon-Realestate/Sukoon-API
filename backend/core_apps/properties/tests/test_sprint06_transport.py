"""Frozen pre-conversion transport contracts for every migrated route alias.

Fixtures use absent synthetic UUIDs to characterize error precedence, authentication,
OPTIONS/HEAD, Arabic/English rendering, methods and privacy headers. Positive
workflows and concurrency are covered by the domain suites, not these fixtures.
"""

import json
from pathlib import Path
import re

import pytest
from django.urls import resolve
from django.test import override_settings
from django.utils.translation import override
from rest_framework.test import APIRequestFactory, force_authenticate

EVIDENCE = Path(__file__).resolve().parents[3] / "sprints/evidence/sprint-06"


@pytest.mark.django_db
def test_all_migrated_alias_transport_contracts(user, settings):
    settings.REST_FRAMEWORK = {
        **settings.REST_FRAMEWORK,
        "DEFAULT_THROTTLE_RATES": {"anon": "999999/day", "user": "999999/day"},
    }
    failures = []
    for expected in json.loads((EVIDENCE / "transport-before.json").read_text()):
        url = "/" + re.sub(
            r"<([^:>]+):([^>]+)>",
            lambda m: (
                "11111111-1111-4111-8111-111111111111"
                if m[1] == "uuid"
                else "1" if m[1] == "int" else "missing"
            ),
            expected["route"],
        )
        match = resolve(url)
        method = expected["method"]
        request = APIRequestFactory().generic(
            method,
            url,
            data=b"{}" if method not in ["GET", "HEAD", "OPTIONS"] else b"",
            content_type="application/json",
            HTTP_ACCEPT_LANGUAGE=expected["locale"],
        )
        request.resolver_match = match
        if expected["auth"] == "account":
            force_authenticate(request, user=user)
        with override(expected["locale"]):
            response = match.func(request, **match.kwargs)
        if hasattr(response, "render"):
            response.render()
        actual = {
            "status": response.status_code,
            "body": (
                json.loads(response.content)
                if response.get("Content-Type", "").startswith("application/json")
                else response.content.decode()
            ),
            "headers": {key: response.get(key) for key in expected["headers"]},
        }
        wanted = {key: expected[key] for key in actual}
        # DRF's api_view used a set for methods; header order varies by process.
        wanted["headers"] = dict(wanted["headers"])
        for value in [actual, wanted]:
            if value["headers"].get("Allow"):
                value["headers"]["Allow"] = sorted(
                    value["headers"]["Allow"].split(", ")
                )
        if actual != wanted:
            failures.append(
                {
                    "case": {
                        key: expected[key]
                        for key in ["route", "method", "auth", "locale"]
                    },
                    "expected": wanted,
                    "actual": actual,
                }
            )
    from os import environ

    if environ.get("SPRINT06_TRANSPORT_DIFF"):
        Path(environ["SPRINT06_TRANSPORT_DIFF"]).write_text(
            json.dumps(failures, ensure_ascii=False, indent=2)
        )
    assert not failures, json.dumps(failures[:6], ensure_ascii=False, indent=2)


def test_runtime_scope_has_no_function_callbacks_or_transport_drift():
    from tools.qa.route_matrix import build

    # The incoming ledger records the production-default release gate.
    with override_settings(SUKOON_MVP=True):
        current = {row["route"]: row for row in build()}
    for old in json.loads((EVIDENCE / "routes-before.json").read_text()):
        new = current[old["route"]]
        assert new["style"] not in {"plain function", "decorated FBV"}
        for field in [
            "name",
            "methods",
            "authentication",
            "permissions",
            "parsers",
            "throttles",
            "mvp_allowed",
        ]:
            assert new[field] == old[field], (old["route"], field)


def test_domain_modules_do_not_import_http_adapters():
    import ast

    root = EVIDENCE.parents[2]
    files = [
        *root.glob("core_apps/properties/services/**/*.py"),
        *root.glob("core_apps/virtual_tours/*commands.py"),
        root / "core_apps/virtual_tours/operations.py",
        root / "core_apps/virtual_tours/selectors.py",
    ]
    for file in files:
        for node in ast.walk(ast.parse(file.read_text())):
            if isinstance(node, ast.ImportFrom):
                assert not any(
                    part
                    in {
                        "views",
                        "capture_views",
                        "review_views",
                        "viewer_views",
                        "http",
                    }
                    for part in (node.module or "").split(".")
                ), file
