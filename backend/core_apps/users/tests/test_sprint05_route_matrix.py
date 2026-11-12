"""Every identity pattern/method: cookie/bearer, locale, shape and stale authority."""
import json
import re
import os
from types import SimpleNamespace
from pathlib import Path

import pytest
from django.urls import get_resolver
from django.utils import translation
from rest_framework.test import APIRequestFactory

from core_apps.users.services.sessions import issue_refresh, revoke_all
from tools.qa.route_matrix import walk

ROOT = Path(__file__).resolve().parents[3]
ROWS = json.loads((ROOT / "sprints/evidence/sprint-05/routes-before.json").read_text())
CASES = [(row, method) for row in ROWS for method in row["methods"]]


def address(row, user):
    route = row["route"]
    values = {"id": str(user.id), "format": "json", "provider": "unsupported-provider"}
    kwargs = {}

    def named(match):
        name = match[1]
        value = values.get(name, "00000000-0000-4000-8000-000000000000")
        kwargs[name] = value
        return value

    route = re.sub(r"\(\?P<(\w+)>[^)]*\)", named, route)

    def converter(match):
        name = match[2]
        value = ".json" if name == "format" else "status" if name == "action" else (
            "id_face" if name == "field" else "00000000-0000-4000-8000-000000000000")
        kwargs[name] = value.lstrip(".") if name == "format" else value
        return value

    route = re.sub(r"<(?:(\w+):)?(\w+)>", converter, route)
    route = route.replace("^", "").replace("$", "").replace("\\.", ".").replace("/?", "/")
    return "/" + route, kwargs


@pytest.mark.django_db
@pytest.mark.parametrize("row,method", CASES, ids=[f'{row["route"]}|{method}' for row, method in CASES])
@pytest.mark.parametrize("transport,locale", [("anonymous", "en"), ("bearer", "en"), ("cookie", "ar"), ("form", "en")])
def test_complete_identity_route_authentication_contract(user, row, method, transport, locale):
    routes = dict(walk(get_resolver().url_patterns))
    path, kwargs = address(row, user)
    callback = routes[row["route"]].callback
    factory = APIRequestFactory()
    request = getattr(factory, method.lower())(path, {}, format="multipart" if transport == "form" else "json")
    request.resolver_match = SimpleNamespace(namespace="")
    request.session = {}
    if transport != "anonymous":
        token = issue_refresh(user).access_token
        if transport == "cookie":
            request.COOKIES["access"] = str(token)
        else:
            request.META["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    with translation.override(locale):
        response = callback(request, **kwargs)
        if hasattr(response, "render"):
            response.render()
    assert 200 <= response.status_code < 500, (path, response.status_code)
    if transport == "anonymous" and "IsAuthenticated" in row["permissions"]:
        assert response.status_code == 401, path
    # A normal account never receives staff-only identity/recovery/closure queues.
    if transport != "anonymous" and any(fragment in path for fragment in (
        "security/totp/", "account-closure/review/",
    )):
        assert response.status_code in {400, 403, 404, 405}, path
    statuses = ROOT / "sprints/evidence/sprint-05/completion/contract-statuses.json"
    expected = json.loads(statuses.read_text())
    key = "|".join((row["route"], method, transport, locale))
    assert response.status_code == expected[key], (path, transport, response.data)
    destination = os.getenv("SPRINT05_ROUTE_OBSERVATIONS")
    if destination:
        with Path(destination).open("a") as output:
            output.write(json.dumps({"route": row["route"], "method": method, "transport": transport,
                                     "locale": locale, "status": response.status_code}) + "\n")


@pytest.mark.django_db
@pytest.mark.parametrize("row", ROWS, ids=[row["route"] for row in ROWS])
def test_all_protected_identity_aliases_reject_revoked_authority(user, row):
    callback = dict(walk(get_resolver().url_patterns))[row["route"]].callback
    if not getattr(callback.cls, "authentication_classes", ()):
        return  # Native public token/registration adapters intentionally disable request authentication.
    token = issue_refresh(user).access_token
    revoke_all(user)
    path, kwargs = address(row, user)
    method = row["methods"][0]
    request = getattr(APIRequestFactory(), method.lower())(
        path, {}, format="json", HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    callback = dict(walk(get_resolver().url_patterns))[row["route"]].callback
    assert callback(request, **kwargs).status_code == 401


@pytest.mark.django_db
@pytest.mark.parametrize("path", ["account-closure/receipt/", "security/sessions/", "security/challenges/",
                                  "email-change/start/", "security/totp/recoveries/"])
@pytest.mark.parametrize("data", [[], "bad", {"action": []}])
def test_malformed_commands_are_client_errors(user, path, data):
    from rest_framework.test import APIClient

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {issue_refresh(user).access_token}")
    response = client.post("/api/v1/auth/" + path, data, format="json")
    expected = {201} if isinstance(data, dict) and path == "email-change/start/" else {400, 403}
    assert response.status_code in expected


STAFF_ROWS = [row for row in ROWS if "security/totp/" in row["route"] or "account-closure/" in row["route"]]


@pytest.mark.django_db
@pytest.mark.parametrize("role", [
    "system_owner", "account_closure_reviewer", "security_recovery_reviewer", "payout_operator",
])
@pytest.mark.parametrize("row", STAFF_ROWS, ids=[row["route"] for row in STAFF_ROWS])
def test_staff_identity_alias_role_matrix(row, role):
    from .test_totp_recovery import staff

    user = staff("matrix-" + role, role)
    path, kwargs = address(row, user)
    method = row["methods"][0]
    request = getattr(APIRequestFactory(), method.lower())(
        path, {}, format="json", HTTP_AUTHORIZATION=f"Bearer {issue_refresh(user).access_token}",
    )
    request.resolver_match = SimpleNamespace(namespace="")
    request.session = {}
    result = dict(walk(get_resolver().url_patterns))[row["route"]].callback(request, **kwargs)
    assert result.status_code < 500
    if "account-closure/review/" in path and role not in {"system_owner", "account_closure_reviewer"}:
        assert result.status_code == 403
    if "staff-identities/" in path and role != "system_owner":
        assert result.status_code in {400, 403}
