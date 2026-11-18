"""Real HTTP acceptance with isolated actors, cookies and database transactions."""

import copy
import hashlib
import json
import os
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model

from tools.qa.connected_http import ConnectedHTTP


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("mvp", [True, False], ids=["mvp", "restoration"])
def test_cookie_account_isolation_and_revocation(live_server, settings, mvp):
    settings.SUKOON_MVP = mvp
    settings.SECURITY_TEST_BYPASS = False
    settings.COOKIE_ORIGIN_ENFORCEMENT = True
    settings.COOKIE_SECURE = False
    users = [get_user_model().objects.create_user(
        email=f"connected-{actor}@example.invalid", password="Local-acceptance-42!",
        first_name=actor, last_name="Acceptance", is_verified=True,
    ) for actor in ("first", "second")]
    clients = [ConnectedHTTP(live_server.url) for _ in users]
    login = "/api/v1/auth/login/"
    account = "/api/v1/profiles/my-account/"
    preferences = "/api/v1/profiles/settings/"
    clients[0].request("GET", account, 401)
    for client, user in zip(clients, users):
        client.request("POST", login, 200, body={
            "email": user.email, "password": "Local-acceptance-42!",
        })
        assert {cookie.name for cookie in client.cookies} >= {"access", "refresh"}
        identity = client.request("GET", account, 200)
        assert identity["data"]["user"]["id"] == str(user.id)
        assert client.request("GET", preferences, 200)["data"]["owner_messages"] is True

    first, second = clients
    first.request("PATCH", preferences, 403, body={"owner_messages": False},
                  origin="https://untrusted.example.invalid")
    assert first.request("GET", preferences, 200)["data"]["owner_messages"] is True
    assert first.request("PATCH", preferences, 200, body={"owner_messages": False},
                         origin=live_server.url)["data"]["owner_messages"] is False
    assert first.request("GET", preferences, 200)["data"]["owner_messages"] is False
    assert second.request("GET", preferences, 200)["data"]["owner_messages"] is True

    replay = ConnectedHTTP(live_server.url)
    for cookie in first.cookies:
        replay.cookies.set_cookie(copy.copy(cookie))
    first.request("POST", "/api/v1/auth/logout/", 200, body={}, origin=live_server.url)
    assert not {cookie.name for cookie in first.cookies} & {"access", "refresh", "logged_in"}
    first.request("GET", account, 401)
    replay.request("GET", account, 401)
    assert second.request("GET", account, 200)["data"]["user"]["id"] == str(users[1].id)

    # Publish only after every behavior assertion passes; never serialize bodies/cookies.
    destination = os.environ.get("CONNECTED_ACCEPTANCE_OUT")
    if destination:
        output = Path(destination)
        output.mkdir(parents=True, exist_ok=True)
        mode = "mvp" if mvp else "restoration"
        root = Path(__file__).resolve().parents[2]
        sources = ["tools/qa/connected_http.py", "core_apps/common/test_connected_acceptance.py",
                   "core_apps/users/urls.py", "core_apps/profiles/urls.py",
                   "core_apps/users/views_parts/set_auth_cookies.py", "core_apps/common/cookie_auth.py"]
        (output / f"cookie-acceptance-{mode}.json").write_text(json.dumps({
            "schema_version": 1, "transport": "loopback_http", "release_mode": mode,
            "database": "pytest_disposable", "security_test_bypass": False,
            "result": "passed", "scenario": "cookie_account_isolation_and_revocation",
            "source_sha256": {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                              for name in sources},
            "assertions": ["authenticated_identity", "cross_origin_write_rejected_without_mutation",
                           "settings_persisted_and_actor_isolated", "logout_clears_cookies",
                           "revoked_access_replay_rejected", "other_actor_session_survives"],
            "observations": [row for client in (*clients, replay) for row in client.observations],
        }, indent=2) + "\n")


@pytest.mark.parametrize("origin", ["https://example.com", "http://localhost",
                                      "http://user@localhost:8000", "http://localhost:8000/api"])
def test_connected_client_refuses_non_disposable_origins(origin):
    with pytest.raises(ValueError):
        ConnectedHTTP(origin)


@pytest.mark.parametrize("path", ["//example.com/", "https://example.com/", "/?token=secret", "/#token"])
def test_connected_client_refuses_non_local_or_sensitive_paths(path):
    with pytest.raises(ValueError):
        ConnectedHTTP("http://localhost:8000").request("GET", path, 200)
