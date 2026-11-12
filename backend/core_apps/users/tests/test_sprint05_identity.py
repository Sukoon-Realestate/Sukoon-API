"""Identity architecture, inherited aliases, domain rollback and race gates."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import ast
import json
from pathlib import Path
from threading import Barrier
from unittest.mock import patch

import pytest
from django.db import close_old_connections, connection
from django.test.utils import CaptureQueriesContext
from django.urls import get_resolver, resolve
from django.utils import timezone
from djoser.utils import encode_uid
from rest_framework.test import APIClient
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from core_apps.users.models import AuthSession, User
from core_apps.users.selectors import active_sessions
from core_apps.users.services import session_management
from core_apps.users.services.recovery_tokens import recovery_token_generator
from core_apps.users.services.sessions import issue_refresh, validate_session
from core_apps.users.services.user_service import change_user_password
from tools.qa.route_matrix import describe, walk

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "sprints/evidence/sprint-05"


def test_every_identity_route_and_alias_is_an_explicit_cbv_with_unchanged_contract():
    before = json.loads((EVIDENCE / "routes-before.json").read_text())
    routes = dict(walk(get_resolver().url_patterns))
    for row in before:
        callback = routes[row["route"]].callback
        style, cls, methods, _ = describe(callback)
        assert style not in {"plain function", "decorated FBV"}, row["route"]
        # ViewSet dispatch adds an implicit HEAD action to the shared mapping.
        explicit = [method for method in methods if method != "HEAD"]
        assert sorted(explicit) == sorted(row["methods"]), row["route"]
        assert routes[row["route"]].name == (row["name"] or None)
        for attr, field in [("authentication_classes", "authentication"),
                            ("permission_classes", "permissions"),
                            ("throttle_classes", "throttles"), ("parser_classes", "parsers")]:
            names = ", ".join(sorted({item.__name__ for item in getattr(cls, attr)})) or "—"
            assert names == row[field], (row["route"], attr)


def test_identity_services_do_not_import_http_adapters():
    for package in ("users", "profiles"):
        for path in (ROOT / "core_apps" / package / "services").rglob("*.py"):
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, ast.ImportFrom):
                    assert not any("views" in part for part in (node.module or "").split(".")), path
                if isinstance(node, ast.Import):
                    assert not any("views" in part for alias in node.names for part in alias.name.split(".")), path


@pytest.mark.django_db
@pytest.mark.parametrize("suffix", ["me/", "me.json", "id/", "id.json"])
def test_inherited_delete_aliases_keep_evidence_and_sessions(user, api_client, suffix):
    from core_apps.users.models import SecurityEvent

    token = issue_refresh(user)
    SecurityEvent.objects.create(user=user, actor=user, action="test.evidence",
                                 security_epoch=0, decision="recorded")
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    url = "/api/v1/auth/users/" + suffix.replace("id", str(user.id))
    assert resolve(url).func.cls.__name__ == "CanonicalUserViewSet"
    response = api_client.delete(url, {"current_password": "Testpass123!"}, format="json")
    assert response.status_code == 409, response.data
    assert response.data["code"] == "account_closure_review_required"
    user.refresh_from_db()
    validate_session(user, token)
    assert user.is_active and SecurityEvent.objects.filter(user=user, action="test.evidence").exists()


@pytest.mark.django_db
@pytest.mark.parametrize("path", ["set_password/", "set_password.json"])
def test_password_aliases_revoke_old_access_and_refresh(user, api_client, path):
    from core_apps.users.token_serializers import CanonicalTokenRefreshSerializer

    token = issue_refresh(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    response = api_client.post("/api/v1/auth/users/" + path, {
        "current_password": "Testpass123!", "new_password": "ChangedPassword123!",
        "re_new_password": "ChangedPassword123!",
    }, format="json")
    assert response.status_code == 200, response.data
    user.refresh_from_db()
    assert user.check_password("ChangedPassword123!")
    with pytest.raises(AuthenticationFailed):
        validate_session(user, token)
    with pytest.raises(AuthenticationFailed):
        CanonicalTokenRefreshSerializer().validate({"refresh": str(token)})


@pytest.mark.django_db
def test_password_and_revocation_rollback_together(user):
    token = issue_refresh(user)
    with patch("core_apps.users.services.passwords.revoke_all", side_effect=RuntimeError("injected")):
        with pytest.raises(RuntimeError, match="injected"):
            change_user_password(user, "Testpass123!", "ChangedPassword123!")
    user.refresh_from_db()
    assert user.check_password("Testpass123!")
    validate_session(user, token)


@pytest.mark.django_db
def test_revoke_command_rechecks_current_authority_and_expiry(user):
    token = issue_refresh(user)
    session_management.revoke_every_session(user, token)
    with pytest.raises(AuthenticationFailed):
        session_management.revoke_every_session(user, token)
    user.refresh_from_db()
    token = issue_refresh(user)
    AuthSession.objects.filter(id=token["session_id"]).update(expires_at=timezone.now())
    with pytest.raises(AuthenticationFailed):
        session_management.revoke_every_session(user, token)


@pytest.mark.django_db
@pytest.mark.parametrize("size", [1, 20, 100])
def test_session_projection_has_constant_query_budget(user, size):
    now = timezone.now()
    AuthSession.objects.bulk_create([
        AuthSession(user=user, security_epoch=user.security_epoch,
                    expires_at=now + timedelta(days=1)) for _ in range(size)
    ])
    with CaptureQueriesContext(connection) as queries:
        projection = active_sessions(user, {})
    assert len(queries) == 1
    assert len(projection["results"]) == size
    assert "email" not in json.dumps(projection)


@pytest.mark.django_db(transaction=True)
def test_postgres_duplicate_password_recovery_has_one_winner(user):
    if connection.vendor != "postgresql":
        pytest.skip("Requires disposable PostgreSQL row locks")
    payload = {"uid": encode_uid(user.pk), "token": recovery_token_generator.make_token(user),
               "new_password": "ChangedPassword123!", "re_new_password": "ChangedPassword123!"}
    token = issue_refresh(user)
    barrier = Barrier(2)

    def submit(_):
        close_old_connections()
        try:
            barrier.wait(timeout=15)
            return APIClient().post("/api/v1/auth/users/reset_password_confirm/", payload, format="json").status_code
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(submit, range(2)))
    assert sorted(results) == [200, 400]
    user.refresh_from_db()
    assert user.security_epoch == 1 and user.check_password("ChangedPassword123!")
    with pytest.raises(AuthenticationFailed):
        validate_session(user, token)


@pytest.mark.django_db
@pytest.mark.parametrize("size", [1, 20, 100])
def test_staff_identity_projection_is_prepared_and_matches_single_account_reads(user, size):
    from core_apps.users.models import StaffSecurityIdentity, TotpFactor, TotpRecoveryRequest
    from core_apps.users.selectors import staff_identities
    from core_apps.users.services.staff_setup import identity_projection

    for index in range(size):
        target = User.objects.create_user(email=f"staff-{index}@example.invalid", is_superuser=True)
        if index % 2:
            identity = StaffSecurityIdentity.objects.create(
                user=target, person_reference=f"person-{index}",
                evidence_reference="verified", known_channel_reference="known",
            )
            TotpFactor.objects.create(user=target, secret_ciphertext="synthetic", confirmed_at=timezone.now())
            TotpRecoveryRequest.objects.create(user=target, identity=identity, person_reference=f"person-{index}")
    User.objects.create_user(email="inactive-staff@example.invalid", is_superuser=True, is_active=False)
    with CaptureQueriesContext(connection) as queries:
        values = staff_identities(user)
    assert len(queries) == 1 and len(values) == size
    assert values == [identity_projection(target) for target in User.objects.filter(
        is_active=True, is_superuser=True
    ).exclude(pk=user.pk).order_by("email")]
