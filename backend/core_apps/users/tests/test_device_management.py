import uuid
from types import SimpleNamespace
import pytest
from rest_framework.exceptions import NotFound
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from core_apps.users.services.sessions import issue_refresh, validate_session
from core_apps.users.services.session_management import revoke_selected, update_metadata
from core_apps.users.models import AuthSession

pytestmark = pytest.mark.django_db


def test_revoke_one_and_others_preserves_current_and_epoch(user):
    current = issue_refresh(user)
    other = issue_refresh(user)
    third = issue_refresh(user)
    req = SimpleNamespace(
        user=user,
        auth=current.access_token,
        headers={"Idempotency-Key": str(uuid.uuid4())},
        data={"action": "revoke_session", "session_id": str(other["session_id"])},
    )
    result = revoke_selected(req)
    assert result[0]["current_session_revoked"] is False
    validate_session(user, current.access_token)
    validate_session(user, third.access_token)
    with pytest.raises(AuthenticationFailed):
        validate_session(user, other.access_token)
    assert revoke_selected(req)[2] is True
    req.data = {"action": "revoke_others"}
    req.headers = {"Idempotency-Key": str(uuid.uuid4())}
    revoke_selected(req)
    validate_session(user, current.access_token)
    with pytest.raises(AuthenticationFailed):
        validate_session(user, third.access_token)
    user.refresh_from_db()
    assert user.security_epoch == 0


def test_device_metadata_only_current_and_foreign_target_hidden(user, superuser):
    current = issue_refresh(user)
    foreign = issue_refresh(superuser)
    req = SimpleNamespace(
        user=user,
        auth=current.access_token,
        headers={"Idempotency-Key": str(uuid.uuid4())},
        data={
            "client_platform": "android",
            "device_model": "Pixel",
            "os_version": "15",
            "app_version": "1.0",
        },
    )
    update_metadata(req)
    assert AuthSession.objects.get(id=current["session_id"]).device_model == "Pixel"
    assert not AuthSession.objects.get(id=foreign["session_id"]).device_model
    req.data = {"action": "revoke_session", "session_id": str(foreign["session_id"])}
    with pytest.raises(NotFound):
        revoke_selected(req)


@pytest.mark.django_db(transaction=True)
def test_refresh_and_targeted_revoke_share_the_user_lock(user):
    from django.db import connection

    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL row locks")
    from core_apps.features.tests.test_cycle_concurrency import parallel_calls
    from core_apps.users.token_serializers import CanonicalTokenRefreshSerializer

    current = issue_refresh(user)
    target = issue_refresh(user)
    request = SimpleNamespace(
        user=user,
        auth=current.access_token,
        headers={"Idempotency-Key": str(uuid.uuid4())},
        data={"action": "revoke_session", "session_id": str(target["session_id"])},
    )

    def operation(index):
        if index == 0:
            return revoke_selected(request)
        try:
            return CanonicalTokenRefreshSerializer(
                data={"refresh": str(target)}
            ).is_valid(raise_exception=True)
        except AuthenticationFailed:
            return False

    parallel_calls(operation)
    with pytest.raises(AuthenticationFailed):
        validate_session(user, target.access_token)
    validate_session(user, current.access_token)


def test_device_endpoints_use_current_jwt_and_do_not_touch_foreign_session(
    user, superuser
):
    from rest_framework.test import APIClient

    current = issue_refresh(user)
    other = issue_refresh(user)
    foreign = issue_refresh(superuser)
    api = APIClient()
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {current.access_token}")
    response = api.patch(
        "/api/v1/auth/security/sessions/current/",
        {
            "client_platform": "ios",
            "device_model": "QA phone",
            "os_version": "18",
            "app_version": "1.0",
        },
        format="json",
    )
    assert response.status_code == 200, response.content
    response = api.get("/api/v1/auth/security/sessions/")
    assert response.status_code == 200, response.content
    rows = response.json()["data"]["results"]
    assert {row["id"] for row in rows} == {current["session_id"], other["session_id"]}
    row = next(row for row in rows if row["current"])
    assert row["device_model"] == "QA phone" and row["last_seen_at"]
    assert response["Cache-Control"] == "private, no-store"
    assert (
        api.post(
            "/api/v1/auth/security/sessions/",
            {
                "action": "revoke_session",
                "session_id": foreign["session_id"],
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
        ).status_code
        == 404
    )
    response = api.post(
        "/api/v1/auth/security/sessions/",
        {
            "action": "revoke_others",
        },
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
    )
    assert response.status_code == 200, response.content
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {other.access_token}")
    assert api.get("/api/v1/auth/security/sessions/").status_code == 401


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_targeted_revocation_closes_only_its_active_socket(user):
    from channels.db import database_sync_to_async
    from core_apps.chat.consumers import ChatConsumer
    from core_apps.common.ws_auth import JWTCookieAuthMiddleware
    from core_apps.common.testing import WebsocketCommunicator

    current = await database_sync_to_async(issue_refresh)(user)
    other = await database_sync_to_async(issue_refresh)(user)
    app = JWTCookieAuthMiddleware(ChatConsumer.as_asgi())
    sockets = [
        WebsocketCommunicator(app, "/ws/chat/?token=" + str(token.access_token))
        for token in [current, other]
    ]
    try:
        for socket in sockets:
            assert (await socket.connect())[0]
        request = SimpleNamespace(
            user=user,
            auth=current.access_token,
            headers={"Idempotency-Key": str(uuid.uuid4())},
            data={"action": "revoke_session", "session_id": other["session_id"]},
        )
        await database_sync_to_async(revoke_selected)(request)
        closed = await sockets[1].receive_output(timeout=3)
        assert closed == {"type": "websocket.close", "code": 4401}
        await sockets[0].send_json_to({"type": "test-current-session"})
        assert (await sockets[0].receive_json_from())[
            "error"
        ] == "Unknown message type."
    finally:
        for socket in sockets:
            await socket.disconnect()
