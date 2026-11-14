"""Pre-conversion synthetic HTTP contracts for each converted housing alias."""

from datetime import datetime, timezone
import json
import hashlib
from pathlib import Path
import re
from unittest.mock import patch

import pytest
from django.core.cache import caches
from django.test import override_settings
from django.urls import resolve
from django.utils.translation import override
from rest_framework.test import APIRequestFactory, force_authenticate

EVIDENCE = Path(__file__).resolve().parents[3] / "sprints/evidence/sprint-07"


@pytest.mark.django_db
@pytest.mark.parametrize("mvp", [True, False], ids=["mvp", "restoration"])
def test_frozen_housing_transport_contracts(user, settings, mvp):
    settings.SUKOON_MVP = mvp
    baseline = EVIDENCE / "transport-before.json"
    rows = json.loads(baseline.read_text())
    if not mvp:
        restoration = json.loads(
            (EVIDENCE / "transport-restoration-overrides.json").read_text()
        )
        assert (
            restoration["baseline_sha256"]
            == hashlib.sha256(baseline.read_bytes()).hexdigest()
        )
        assert restoration["characterizations"] == len(rows)
        key = lambda row: tuple(
            row[field] for field in ("route", "method", "auth", "locale")
        )
        overrides = {key(row): row for row in restoration["overrides"]}
        rows = [overrides.get(key(row), row) for row in rows]
    failures = []
    for expected in rows:
        # IDs, clocks and throttles have a deterministic fixture lifetime; each
        # request still runs its real authentication, permissions and parsers.
        expected = json.loads(
            json.dumps(expected).replace(
                "22222222-2222-4222-8222-222222222222", str(user.id)
            )
        )
        for cache in caches.all():
            cache.clear()
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
            data=b"{}" if method not in {"GET", "HEAD", "OPTIONS"} else b"",
            content_type="application/json",
            HTTP_ACCEPT_LANGUAGE=expected["locale"],
        )
        request.resolver_match = match
        if expected["auth"] == "account":
            force_authenticate(request, user=user)
        with override(expected["locale"]), patch(
            "django.utils.timezone.now",
            return_value=datetime(2026, 11, 12, 12, tzinfo=timezone.utc),
        ):
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
        for value in (actual, wanted):
            if value["headers"].get("Allow"):
                value["headers"]["Allow"] = sorted(
                    value["headers"]["Allow"].split(", ")
                )
        if actual != wanted:
            failures.append(
                {
                    "route": expected["route"],
                    "method": method,
                    "auth": expected["auth"],
                    "locale": expected["locale"],
                    "expected": wanted,
                    "actual": actual,
                }
            )
    assert not failures, json.dumps(failures[:5], ensure_ascii=False, indent=2)


def test_scoped_routes_are_explicit_and_keep_transport_metadata():
    from tools.qa.route_matrix import build

    with override_settings(SUKOON_MVP=True):
        current = {row["route"]: row for row in build()}
    for before in json.loads((EVIDENCE / "routes-before.json").read_text()):
        after = current[before["route"]]
        assert after["style"] not in {"plain function", "decorated FBV"}
        for field in (
            "name",
            "methods",
            "authentication",
            "permissions",
            "parsers",
            "throttles",
            "mvp_allowed",
        ):
            assert before[field] == after[field], (before["route"], field)
        if before["style"] == "decorated FBV":
            cls = resolve(
                "/"
                + re.sub(
                    r"<([^:>]+):([^>]+)>",
                    lambda m: (
                        "11111111-1111-4111-8111-111111111111"
                        if m[1] == "uuid"
                        else "1" if m[1] == "int" else "missing"
                    ),
                    before["route"],
                )
            ).func.view_class
            assert set(cls.action_policies) == {m.lower() for m in before["methods"]}
