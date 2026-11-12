"""Characterized HTTP contracts for every converted identity callback.

The committed fixture was captured from incoming HEAD function adapters. Existing
workflow suites cover successful mutations; these cases guard transport parity,
including locale, forms, authentication, errors, headers and unsupported methods.
"""
import importlib.util
import json
import os
from pathlib import Path

import pytest
from django.core.cache import cache
from django.urls import resolve
from django.utils import translation
from rest_framework.test import APIRequestFactory, force_authenticate

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "sprints/evidence/sprint-05"
BEFORE = json.loads((EVIDENCE / "routes-before.json").read_text())
CONVERTED = [row for row in BEFORE if row["style"] == "decorated FBV"]
VARIANTS = [
    (True, "json", "en"),
    (True, "multipart", "ar"),
    (True, "urlencoded", "en"),
    (False, "json", "en"),
]
CASES = [(row, method, variant) for row in CONVERTED
         for method in row["methods"] + ["OPTIONS", "HEAD"] for variant in VARIANTS]


def callback(row):
    baseline = os.getenv("SPRINT05_BASELINE_VIEWS")
    if not baseline:
        return resolve(path_for(row)).func
    module, name = row["handler"].rsplit(".", 1)
    spec = importlib.util.spec_from_file_location(
        module.replace("views", "baseline_views"),
        Path(baseline) / (module.rsplit(".", 1)[1] + ".py"),
    )
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return getattr(loaded, name)


def path_for(row):
    return ("/" + row["route"].replace("<uuid:identity>", "00000000-0000-4000-8000-000000000000")
            .replace("<str:action>", "status"))


def contract_key(row, method, variant):
    return "|".join([row["route"], method, str(variant[0]), variant[1], variant[2]])


@pytest.mark.django_db
@pytest.mark.parametrize("row,method,variant", CASES, ids=[contract_key(*case) for case in CASES])
def test_converted_identity_transport_contract(user, row, method, variant):
    # Authenticated force-auth requests intentionally carry no bound claim. This
    # characterizes reauthentication errors without starting provider workflows.
    authenticated, body_format, locale = variant
    factory = APIRequestFactory()
    cache.clear()
    kwargs = {"data": {}, "format": body_format}
    if body_format == "urlencoded":
        kwargs = {"data": "", "content_type": "application/x-www-form-urlencoded"}
    request = getattr(factory, method.lower())(path_for(row), **kwargs)
    if authenticated:
        # Use the actual persisted identity for commands which lock the account.
        user.refresh_from_db()
        force_authenticate(request, user=user)
    with translation.override(locale):
        response = callback(row)(request, **resolve(path_for(row)).kwargs)
        response.render()
    headers = dict(response.items())
    if "Allow" in headers:
        headers["Allow"] = sorted(part.strip() for part in headers["Allow"].split(","))
    actual = {"status": response.status_code, "headers": headers,
              "body": json.loads(response.content) if response.content else None}
    if isinstance(actual["body"], dict) and isinstance(actual["body"].get("data"), dict):
        if "account_id" in actual["body"]["data"]:
            assert actual["body"]["data"]["account_id"] == str(user.id)
            actual["body"]["data"]["account_id"] = "__request_user_id__"
    key = contract_key(row, method, variant)
    destination = os.getenv("SPRINT05_CAPTURE_CONTRACTS")
    if destination:
        path = Path(destination)
        data = json.loads(path.read_text()) if path.exists() else {}
        data[key] = actual
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    else:
        expected = json.loads((EVIDENCE / "transport-contracts.json").read_text())
        assert actual == expected[key]
