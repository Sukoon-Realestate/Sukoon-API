"""Offline settings and HTTP security checks; no deployed system is contacted."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

SCRIPT = """
import django, json
from django.conf import settings
from django.core.management import call_command
from django.core.checks import run_checks, WARNING
from django.http import HttpResponse
from django.test import Client, override_settings
from django.urls import path
django.setup()
issues = run_checks(include_deployment_checks=True)
assert {issue.id for issue in issues if issue.level >= WARNING} == {'security.W005', 'security.W021'}
call_command('check', deploy=True, fail_level='ERROR', verbosity=0)
urlpatterns = [path('probe/', lambda request: HttpResponse('ok'))]
with override_settings(ROOT_URLCONF=__name__):
    client = Client()
    redirected = client.get('/probe/', HTTP_HOST='staging.example.invalid')
    secure = client.get('/probe/', HTTP_HOST='staging.example.invalid', secure=True)
    forwarded = client.get('/probe/', HTTP_HOST='staging.example.invalid', HTTP_X_FORWARDED_PROTO='https')
    assert redirected.status_code == 301
    assert redirected['Location'] == 'https://staging.example.invalid/probe/'
    assert secure.status_code == 200
    assert secure['Strict-Transport-Security'] == 'max-age=3600'
    assert settings.SESSION_COOKIE_SECURE and settings.CSRF_COOKIE_SECURE and settings.COOKIE_SECURE
    print(json.dumps({'forwarded_status': forwarded.status_code}))
"""


def environment():
    return {
        **os.environ,
        "DOTENV_DISABLED": "1",
        "DEBUG": "False",
        "POSTGRES_DB": "offline_acceptance",
        "POSTGRES_USER": "offline_acceptance",
        "POSTGRES_PASSWORD": "",
        "POSTGRES_HOST": "127.0.0.1",
        "POSTGRES_PORT": "65534",
        "RENTAL_PROVIDER_BACKEND": "disabled",
        "DJANGO_SETTINGS_MODULE": "config.settings.staging_acceptance",
        "SECRET_KEY": "offline-acceptance-secret-7jH2cvR8mL5nP0sX4aQ9tW6bK3yD1fZ5gU8eV2iO6rA9",
        "SIGNING_KEY": "offline-acceptance-signing-8kJ3dcS9nM6oQ1tY5bR0uX7cL4zE2gA6hV9fW3jP7sB0",
        "ALLOWED_HOSTS": "staging.example.invalid",
        "COOKIE_TRUSTED_ORIGINS": "https://staging.example.invalid",
        "STAGING_HSTS_SECONDS": "3600",
        "STAGING_TRUST_HTTPS_PROXY": "false",
        "DOMAIN": "staging.example.invalid",
        "REDIS_URL": "redis://127.0.0.1:65534/0",
    }


def run(settings_env, script=SCRIPT):
    return subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path(__file__).resolve().parents[2],
        env=settings_env,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize("trust", [False, True])
def test_acceptance_profile_passes_deploy_checks_and_enforces_https(trust):
    env = environment()
    env["STAGING_TRUST_HTTPS_PROXY"] = str(trust).lower()
    result = run(env)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout.splitlines()[-1])["forwarded_status"] == (200 if trust else 301)


@pytest.mark.parametrize(
    "key,value",
    [
        ("ALLOWED_HOSTS", "*"),
        ("COOKIE_TRUSTED_ORIGINS", ""),
        ("COOKIE_TRUSTED_ORIGINS", "http://staging.example.invalid"),
        ("COOKIE_TRUSTED_ORIGINS", "https://staging.example.invalid/private/"),
        ("COOKIE_TRUSTED_ORIGINS", "https://staging.example.invalid:bad"),
        ("COOKIE_TRUSTED_ORIGINS", "https://staging.example.invalid:0"),
        ("STAGING_HSTS_SECONDS", ""),
        ("STAGING_HSTS_SECONDS", "-1"),
        ("STAGING_TRUST_HTTPS_PROXY", "maybe"),
    ],
)
def test_acceptance_profile_rejects_incomplete_host_tls_or_proxy_configuration(key, value):
    env = environment()
    env[key] = value
    result = run(env, "import django; django.setup()")
    assert result.returncode != 0
    assert "ImproperlyConfigured" in result.stderr
