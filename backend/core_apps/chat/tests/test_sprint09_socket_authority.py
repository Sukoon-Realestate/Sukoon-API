"""Both ASGI boundaries recheck current session, epoch and expiry.

The probe app bypasses event-domain authorization deliberately: authentication
must still stop content that an already-running consumer tries to send.
"""

import asyncio
import json
from datetime import timedelta
from time import time

import pytest
from channels.db import database_sync_to_async
from django.utils import timezone

from core_apps.common.testing import WebsocketCommunicator
from core_apps.common.ws_auth import JWTCookieAuthMiddleware
from core_apps.users.services.sessions import issue_refresh


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("boundary", ["receive", "send"])
@pytest.mark.parametrize(
    "revocation", ["session", "epoch", "session_expiry", "token_expiry"]
)
async def test_current_authority_on_both_socket_boundaries(user, boundary, revocation):
    token = await database_sync_to_async(issue_refresh)(user)
    proceed = asyncio.Event()
    accepted = asyncio.Event()
    app_scope = {}

    async def probe(scope, receive, send):
        app_scope.update(scope)
        assert (await receive())["type"] == "websocket.connect"
        await send({"type": "websocket.accept"})
        accepted.set()
        if boundary == "send":
            await proceed.wait()
        else:
            message = await receive()
            if message["type"] == "websocket.disconnect":
                return
        await send(
            {
                "type": "websocket.send",
                "text": json.dumps({"secret": "private content"}),
            }
        )

    socket = WebsocketCommunicator(
        JWTCookieAuthMiddleware(probe), "/ws/chat/?token=" + str(token.access_token)
    )
    try:
        assert (await socket.connect())[0]
        await accepted.wait()

        @database_sync_to_async
        def revoke():
            from core_apps.users.models import AuthSession, User

            if revocation == "session":
                AuthSession.objects.filter(id=token["session_id"]).update(
                    revoked_at=timezone.now()
                )
            elif revocation == "epoch":
                User.objects.filter(pk=user.pk).update(
                    security_epoch=user.security_epoch + 1
                )
            elif revocation == "session_expiry":
                AuthSession.objects.filter(id=token["session_id"]).update(
                    expires_at=timezone.now() - timedelta(seconds=1)
                )

        if revocation == "token_expiry":
            app_scope["auth_claims"]["exp"] = int(time()) - 1
        else:
            await revoke()
        if boundary == "send":
            proceed.set()
        else:
            await socket.send_json_to({"type": "message.read"})
        assert await socket.receive_output(timeout=3) == {
            "type": "websocket.close",
            "code": 4401,
        }
    finally:
        proceed.set()
        await socket.disconnect()
