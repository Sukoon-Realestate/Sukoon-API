"""Verify two real local WebSocket clients against disposable Django/PostgreSQL.

No deployed database, provider, device token or real user is used. Tokens stay in
memory and use cookies, never URLs or log output. The owned server and database
are removed on success and failure; the result names the limited evidence level.
"""

import argparse
import asyncio
from contextlib import AsyncExitStack
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from uuid import uuid4

import psycopg2
from psycopg2 import sql
import requests
import websockets


async def event(connection, kind):
    async with asyncio.timeout(10):
        while True:
            value = json.loads(await connection.recv())
            if value.get("type") == kind or value.get("error"):
                return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", required=True)
    parser.add_argument("--postgres-port", type=int, default=55446)
    parser.add_argument("--postgres-user", default="plan_tester")
    args = parser.parse_args()
    if not args.template.startswith("test_sokoun_"):
        parser.error("Only an isolated test_sokoun_* template is permitted.")
    root = Path(__file__).resolve().parents[2]
    output = Path(tempfile.mkdtemp(prefix="sokoun-chat-network-"))
    database = "sokoun_chat_network_" + uuid4().hex[:12]
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    (output / "chat_network_settings.py").write_text(
        """from config.settings.postgres_test import *
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
CELERY_TASK_ALWAYS_EAGER = False
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"
GENERAL_BACKGROUND_ENABLED = False
RENTAL_PROVIDER_BACKEND = "disabled"
RENTAL_FAKE_PROVIDER_ALLOWED = False
RENTAL_CHECKOUT_ENABLED = False
SIGNWELL_TEST_ENABLED = False
SIGNWELL_API_KEY = ""
PLANNING_ROUTES_API_KEY = PLANNING_GEMINI_API_KEY = ""
"""
    )
    admin = psycopg2.connect(
        host="127.0.0.1",
        port=args.postgres_port,
        user=args.postgres_user,
        dbname="postgres",
    )
    admin.autocommit = True
    process = log = None
    created = False
    summary = {
        "local_only": True,
        "network": "loopback HTTP and WebSocket, real ASGI process",
        "physical_device": False,
        "provider_transactions": False,
    }
    try:
        with admin.cursor() as cursor:
            cursor.execute(
                sql.SQL("CREATE DATABASE {} TEMPLATE {}").format(
                    sql.Identifier(database), sql.Identifier(args.template)
                )
            )
        created = True
        os.environ.update(
            DJANGO_SETTINGS_MODULE="chat_network_settings",
            TEST_POSTGRES_DB=database,
            TEST_POSTGRES_USER=args.postgres_user,
            TEST_POSTGRES_HOST="127.0.0.1",
            TEST_POSTGRES_PORT=str(args.postgres_port),
            PYTHONPATH=os.pathsep.join([str(output), str(root)]),
        )
        sys.path[:0] = [str(output), str(root)]
        import django

        django.setup()
        from asgiref.sync import sync_to_async
        from django.conf import settings
        from django.core.management import call_command
        from django.db import connections
        from core_apps.users.models import User
        from core_apps.users.services.sessions import issue_refresh
        from core_apps.chat.models import Message
        from core_apps.chat.services.message_service import (
            get_or_create_direct_conversation,
        )

        assert settings.DATABASES["default"]["NAME"] == database
        call_command("flush", interactive=False, verbosity=0)
        people = [
            User.objects.create_user(
                email=f"qa-chat-{index}@example.invalid",
                first_name="Local",
                last_name=f"QA {index}",
                is_verified=True,
            )
            for index in range(3)
        ]
        sender, recipient, outsider = people
        tokens = [str(issue_refresh(person).access_token) for person in people]
        reviewer = User.objects.create_superuser(
            email="qa-reviewer@example.invalid",
            first_name="Local",
            last_name="Reviewer",
            password=uuid4().hex,
        )
        reviewer_token = str(issue_refresh(reviewer).access_token)
        conversation = get_or_create_direct_conversation(
            user=sender, other_user=recipient, workspace="individual"
        )
        log = (output / "server.log").open("wb")
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "config.asgi:application",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--no-access-log",
                "--log-level",
                "warning",
            ],
            cwd=root,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("Local ASGI process stopped during startup.")
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                    break
            except OSError:
                time.sleep(0.15)
        else:
            raise RuntimeError("Local ASGI readiness timed out.")

        async def exercise():
            async with AsyncExitStack() as stack:

                async def connect(token):
                    return await stack.enter_async_context(
                        websockets.connect(
                            f"ws://127.0.0.1:{port}/ws/chat/",
                            origin=f"http://127.0.0.1:{port}",
                            additional_headers={
                                "Cookie": f"{settings.COOKIE_NAME}={token}"
                            },
                            proxy=None,
                            open_timeout=10,
                            close_timeout=2,
                        )
                    )

                first = await connect(tokens[0])
                second = await connect(tokens[1])
                third = await connect(tokens[2])
                command = {
                    "type": "message.send",
                    "conversation_id": str(conversation.id),
                    "client_message_id": str(uuid4()),
                    "content": "Local network recovery — رسالة اختبار",
                }
                await first.send(json.dumps(command))
                received = await event(second, "message.new")
                assert received["payload"]["content"] == command["content"]
                identity = received["payload"]["id"]
                # The recipient proves commit; the sender never consumes the ack.
                first.transport.abort()
                restored = await connect(tokens[0])
                await restored.send(json.dumps(command))
                ack = await event(restored, "message.ack")
                assert ack["payload"]["id"] == identity
                summary["lost_ack_recovered_original_message"] = True
                await restored.send(json.dumps({**command, "content": "Changed"}))
                conflict = json.loads(await asyncio.wait_for(restored.recv(), 10))
                assert conflict["code"] == "client_message_conflict"
                summary["changed_replay_rejected"] = True

                await second.send(
                    json.dumps(
                        {
                            "type": "message.read",
                            "conversation_id": str(conversation.id),
                        }
                    )
                )
                read = await event(restored, "message.read")
                assert read["payload"]["reader_id"] == str(recipient.id)
                summary["peer_read_receipt_received"] = True
                await third.send(
                    json.dumps({**command, "client_message_id": str(uuid4())})
                )
                denied = json.loads(await asyncio.wait_for(third.recv(), 10))
                assert denied.get("error") == "Not a participant."
                summary["outsider_send_rejected"] = True

                def history(token):
                    with requests.Session() as session:
                        session.trust_env = False
                        return session.get(
                            f"http://127.0.0.1:{port}/api/v1/chat/conversations/{conversation.id}/messages/",
                            headers={"Authorization": f"Bearer {token}"},
                            timeout=10,
                        )

                response = await asyncio.to_thread(history, tokens[1])
                assert response.status_code == 200
                payload = response.json()
                payload = payload.get("data", payload)
                rows = (
                    payload.get("results", []) if isinstance(payload, dict) else payload
                )
                assert [str(row["id"]) for row in rows] == [str(identity)]
                assert (await asyncio.to_thread(history, tokens[2])).status_code == 403
                summary["http_history_and_privacy_verified"] = True

                def administrative_action(action):
                    with requests.Session() as session:
                        session.trust_env = False
                        response = session.post(
                            f"http://127.0.0.1:{port}/api/v1/admin/users/{sender.id}/{action}/",
                            headers={"Authorization": f"Bearer {reviewer_token}"},
                            json={"reason": "Local session revocation verification"},
                            timeout=10,
                        )
                        assert response.status_code == 200, response.status_code

                await asyncio.to_thread(administrative_action, "suspend")
                await restored.send(json.dumps(command))
                try:
                    await asyncio.wait_for(restored.recv(), 10)
                except websockets.ConnectionClosed as exc:
                    assert exc.rcvd.code == 4401
                else:
                    raise AssertionError("Suspended session remained authorized.")
                assert (await asyncio.to_thread(history, tokens[0])).status_code == 401

                await asyncio.to_thread(administrative_action, "unsuspend")

                def fresh_session():
                    sender.refresh_from_db()
                    return str(issue_refresh(sender).access_token)

                fresh = await sync_to_async(fresh_session)()
                assert (await asyncio.to_thread(history, tokens[0])).status_code == 401
                assert (await asyncio.to_thread(history, fresh)).status_code == 200
                summary[
                    "admin_suspension_revokes_socket_and_requires_fresh_session"
                ] = True

        asyncio.run(exercise())
        assert Message.objects.filter(conversation=conversation).count() == 1
        summary["saved_messages"] = 1
        summary["result"] = "passed"
        connections.close_all()
    finally:
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        if log:
            log.close()
        if created:
            with admin.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname=%s AND pid<>pg_backend_pid()",
                    [database],
                )
                cursor.execute(
                    sql.SQL("DROP DATABASE {}").format(sql.Identifier(database))
                )
        admin.close()
        summary["resources_stopped"] = True
        summary["database_dropped"] = created
        (output / "result.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps({"output": str(output), **summary}, indent=2))


if __name__ == "__main__":
    main()
