"""Disposable loopback workspace for native connected acceptance, never deployment."""

import json
import os
from pathlib import Path
import socket

from .postgres_test import *  # noqa: F403,F401

_root = Path(os.environ["SPRINT4_QA_ROOT"]).resolve(strict=True)
_repository = Path(__file__).resolve().parents[3]
if _repository == _root or _repository in _root.parents or not _root.name.startswith("sukoon-sprint4-connected-"):
    raise RuntimeError("Use a fresh Sprint 4 temporary acceptance workspace outside the repository")
_marker = json.loads((_root / "workspace.json").read_text())
_database = DATABASES["default"]  # noqa: F405
if (_marker.get("purpose") != "disposable_connected_acceptance"
        or _database["HOST"] != "127.0.0.1" or _database["USER"] != "sprint4_qa"
        or _database["NAME"] != _marker["database"] or not _database["NAME"].startswith("sprint4_connected_")
        or _database["PORT"] != str(_marker["postgres_port"])):
    raise RuntimeError("Connected acceptance database does not match its disposable workspace")

ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
CSRF_TRUSTED_ORIGINS = [f"http://127.0.0.1:{_marker['http_port']}"]
SUKOON_MVP = _marker["release_mode"] == "mvp"
SECURITY_TEST_BYPASS = False
RENTAL_CHECKOUT_ENABLED = False
CELERY_TASK_ALWAYS_EAGER = True
CELERY_BROKER_URL = "memory://"
GEMINI_API_KEY = ""
FIREBASE_CREDENTIALS_JSON = FIREBASE_CREDENTIALS_FILE = ""
FIREBASE_CLIENT_EMAIL = FIREBASE_PRIVATE_KEY = ""
MEDIA_ROOT = str(_root / "media")
CHAT_PRIVATE_MEDIA_ROOT = str(_root / "private-chat")
SUPPORT_PRIVATE_MEDIA_ROOT = str(_root / "private-support")
VIRTUAL_TOUR_PRIVATE_ROOT = str(_root / "private-tours")
EVIDENCE_PRIVATE_ROOT = str(_root / "private-evidence")
CONNECTED_ACCEPTANCE_ROOT = str(_root)

_connect = socket.socket.connect
_connect_ex = socket.socket.connect_ex


def _local_only(address):
    if isinstance(address, tuple) and address[0] not in {"127.0.0.1", "localhost", "::1"}:
        raise RuntimeError("External providers are disabled in the connected acceptance workspace")


def _guarded_connect(stream, address):
    _local_only(address)
    return _connect(stream, address)


def _guarded_connect_ex(stream, address):
    _local_only(address)
    return _connect_ex(stream, address)


socket.socket.connect = _guarded_connect
socket.socket.connect_ex = _guarded_connect_ex
