"""Loopback-only synthetic HTTP/worker harness. Never a deployment setting."""
from pathlib import Path
from os import environ
from .postgres_test import *  # noqa: F403

assert DATABASES['default']['NAME'] == 'mvp_http_isolated'  # noqa: F405
assert DATABASES['default']['HOST'] == '127.0.0.1'  # noqa: F405
assert DATABASES['default']['PORT'] == '55439'  # noqa: F405
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver']
CSRF_TRUSTED_ORIGINS = ['http://127.0.0.1:8026']
SUKOON_MVP = True
RENTAL_CHECKOUT_ENABLED = False
SECURITY_TEST_BYPASS = False
PROPERTY_CAPTURE_ENABLED = True
GEMINI_API_KEY = ''
CELERY_TASK_ALWAYS_EAGER = False
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'
FIREBASE_CREDENTIALS_JSON = FIREBASE_CREDENTIALS_FILE = ''
FIREBASE_CLIENT_EMAIL = FIREBASE_PRIVATE_KEY = ''
VIRTUAL_TOUR_PROCESSOR_MODE = 'polling'
VIRTUAL_TOUR_STORAGE_PROVIDER = 's3'
VIRTUAL_TOUR_S3_BUCKET = ''
VIRTUAL_TOUR_PRIVATE_ROOT = str(Path(environ['MVP_HTTP_ROOT']) / 'private-tours')
MEDIA_ROOT = str(Path(environ['MVP_HTTP_ROOT']) / 'media')

# This test-only process cannot contact providers, even if the parent shell or
# local dotenv contains credentials. Native PostgreSQL uses the asserted DSN.
import socket

_local_connect = socket.socket.connect
_local_connect_ex = socket.socket.connect_ex


def _check_local(address):
    if isinstance(address, tuple) and address[0] not in {'127.0.0.1', '::1', 'localhost'}:
        raise RuntimeError('Provider network is disabled in the isolated MVP HTTP harness')


def _connect(stream, address):
    _check_local(address)
    return _local_connect(stream, address)


def _connect_ex(stream, address):
    _check_local(address)
    return _local_connect_ex(stream, address)


socket.socket.connect = _connect
socket.socket.connect_ex = _connect_ex
