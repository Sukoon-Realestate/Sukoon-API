"""Verify two real local WebSocket clients against disposable Django/PostgreSQL.

No deployed database, provider, device token or real user is used. Tokens stay in
memory and use cookies, never URLs or log output. The owned server and database
are removed on success and failure; the result names the limited evidence level.
"""

import argparse
import asyncio
from concurrent.futures import ThreadPoolExecutor
from statistics import median
import math
from contextlib import AsyncExitStack
import json
import os
from pathlib import Path
import socket
import shutil
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
    parser.add_argument("--multi-worker", action="store_true", help="Use two owned ASGI processes and disposable Redis")
    parser.add_argument("--postgres-host", default="127.0.0.1")
    parser.add_argument(
        "--load-requests", type=int, default=0, help="Optional loopback read/rejection probe, 0–1000 requests"
    )
    parser.add_argument("--postgres-port", type=int, default=55446)
    parser.add_argument("--postgres-user", default="plan_tester")
    args = parser.parse_args()
    if not 0 <= args.load_requests <= 1000:
        parser.error("--load-requests must be between 0 and 1000")
    if not args.template.startswith("test_sokoun_"):
        parser.error("Only an isolated test_sokoun_* template is permitted.")
    root = Path(__file__).resolve().parents[2]
    output = Path(tempfile.mkdtemp(prefix="sokoun-chat-network-"))
    database = "sokoun_chat_network_" + uuid4().hex[:12]
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    ports = [port]
    redis_port = None
    if args.multi_worker:
        for _ in range(2):
            with socket.socket() as listener:
                listener.bind(("127.0.0.1", 0))
                ports.append(listener.getsockname()[1])
        redis_port = ports.pop()
    (output / "chat_network_settings.py").write_text(
        f"""from config.settings.postgres_test import *
from pathlib import Path
SCRATCH_ROOT = Path({str(output)!r})
MEDIA_ROOT = str(SCRATCH_ROOT / "media")
STATIC_ROOT = str(SCRATCH_ROOT / "static")
CHAT_PRIVATE_MEDIA_ROOT = str(SCRATCH_ROOT / "chat")
SUPPORT_PRIVATE_MEDIA_ROOT = str(SCRATCH_ROOT / "support")
VIRTUAL_TOUR_PRIVATE_ROOT = str(SCRATCH_ROOT / "tours")
EVIDENCE_PRIVATE_ROOT = str(SCRATCH_ROOT / "evidence")
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
    if args.multi_worker:
        with (output / "chat_network_settings.py").open("a") as settings_file:
            settings_file.write(
                "\nCHANNEL_LAYERS = "
                + repr(
                    {
                        "default": {
                            "BACKEND": "channels_redis.core.RedisChannelLayer",
                            "CONFIG": {"hosts": [f"redis://127.0.0.1:{redis_port}/0"], "prefix": "sprint04-qa"},
                        }
                    }
                )
                + "\n"
            )
    if args.multi_worker:
        with (output / "chat_network_settings.py").open("a") as settings_file:
            settings_file.write(
                "\nCACHES = "
                + repr(
                    {
                        "default": {
                            "BACKEND": "django.core.cache.backends.redis.RedisCache",
                            "LOCATION": f"redis://127.0.0.1:{redis_port}/1",
                            "KEY_PREFIX": "sprint04-qa",
                        }
                    }
                )
                + "\n"
            )
    admin = psycopg2.connect(
        host=args.postgres_host,
        port=args.postgres_port,
        user=args.postgres_user,
        dbname="postgres",
    )
    admin.autocommit = True
    processes, logs = [], []
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
            DOTENV_DISABLED="1",
            DJANGO_SETTINGS_MODULE="chat_network_settings",
            TEST_POSTGRES_DB=database,
            TEST_POSTGRES_USER=args.postgres_user,
            TEST_POSTGRES_HOST=args.postgres_host,
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
        conversation = get_or_create_direct_conversation(user=sender, other_user=recipient, workspace="individual")
        if args.multi_worker:
            binary = shutil.which("redis-server")
            if not binary:
                raise RuntimeError("A local redis-server is required for --multi-worker")
            log = (output / "redis.log").open("wb")
            logs.append(log)
            processes.append(
                subprocess.Popen(
                    [binary, "--bind", "127.0.0.1", "--port", str(redis_port), "--save", "", "--appendonly", "no"],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                )
            )
            from redis import Redis

            broker = Redis(host="127.0.0.1", port=redis_port)
            deadline = time.monotonic() + 25
            while time.monotonic() < deadline:
                try:
                    if broker.ping():
                        break
                except Exception:
                    time.sleep(0.15)
            else:
                raise RuntimeError("Disposable Redis readiness timed out")
        for server_port in ports:
            log = (output / f"server-{server_port}.log").open("wb")
            logs.append(log)
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "config.asgi:application",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(server_port),
                    "--no-access-log",
                    "--log-level",
                    "warning",
                ],
                cwd=root,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
            processes.append(process)
            deadline = time.monotonic() + 25
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError("Local ASGI process stopped during startup.")
                try:
                    with socket.create_connection(("127.0.0.1", server_port), timeout=0.2):
                        break
                except OSError:
                    time.sleep(0.15)
            else:
                raise RuntimeError("Local ASGI readiness timed out.")
        summary["asgi_processes"] = len(ports)
        summary["redis_channel_layer"] = args.multi_worker

        async def exercise():
            async with AsyncExitStack() as stack:

                async def connect(token):
                    target_port = ports[1] if args.multi_worker and token == tokens[1] else port
                    return await stack.enter_async_context(
                        websockets.connect(
                            f"ws://127.0.0.1:{target_port}/ws/chat/",
                            origin=f"http://127.0.0.1:{target_port}",
                            additional_headers={"Cookie": f"{settings.COOKIE_NAME}={token}"},
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
                await third.send(json.dumps({**command, "client_message_id": str(uuid4())}))
                denied = json.loads(await asyncio.wait_for(third.recv(), 10))
                assert denied.get("error") == "Not a participant."
                summary["outsider_send_rejected"] = True

                def history(token, target_port=port):
                    with requests.Session() as session:
                        session.trust_env = False
                        return session.get(
                            f"http://127.0.0.1:{target_port}/api/v1/chat/conversations/{conversation.id}/messages/",
                            headers={"Authorization": f"Bearer {token}"},
                            timeout=10,
                        )

                response = await asyncio.to_thread(history, tokens[1])
                assert response.status_code == 200
                payload = response.json()
                payload = payload.get("data", payload)
                rows = payload.get("results", []) if isinstance(payload, dict) else payload
                assert [str(row["id"]) for row in rows] == [str(identity)]
                assert (await asyncio.to_thread(history, tokens[2])).status_code == 403
                summary["http_history_and_privacy_verified"] = True

                if args.load_requests:

                    def load_probe():
                        for _ in range(3):
                            assert history(tokens[1]).status_code == 200

                        def sample(index):
                            denied = index % 10 == 0
                            started = time.perf_counter()
                            response = history(tokens[2] if denied else tokens[1], ports[index % len(ports)])
                            assert response.status_code == (403 if denied else 200)
                            return time.perf_counter() - started, len(response.content), response.status_code

                        started = time.perf_counter()
                        with ThreadPoolExecutor(max_workers=4) as pool:
                            samples = list(pool.map(sample, range(args.load_requests)))
                        elapsed = time.perf_counter() - started
                        times = sorted(row[0] for row in samples)
                        return {
                            "requests": len(samples),
                            "concurrency": 4,
                            "warmup": 3,
                            "fixture_messages": 1,
                            "unexpected_failures": 0,
                            "authorized": sum(row[2] == 200 for row in samples),
                            "rejected": sum(row[2] == 403 for row in samples),
                            "p50_seconds": median(times),
                            "p95_seconds": times[math.ceil(0.95 * len(times)) - 1],
                            "requests_per_second": len(samples) / elapsed,
                            "max_response_bytes": max(row[1] for row in samples),
                            "scope": "local loopback HTTP; not staging, TLS or an API-wide SLO",
                        }

                    summary["controlled_local_load"] = await asyncio.to_thread(load_probe)

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
                summary["admin_suspension_revokes_socket_and_requires_fresh_session"] = True

        asyncio.run(exercise())
        assert Message.objects.filter(conversation=conversation).count() == 1
        summary["saved_messages"] = 1
        summary["result"] = "passed"
        connections.close_all()
    finally:
        for process in reversed(processes):
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
        for log in logs:
            log.close()
        if created:
            with admin.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname=%s AND pid<>pg_backend_pid()",
                    [database],
                )
                cursor.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(database)))
        admin.close()
        summary["resources_stopped"] = True
        summary["database_dropped"] = created
        (output / "result.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps({"output": str(output), **summary}, indent=2))


if __name__ == "__main__":
    main()
