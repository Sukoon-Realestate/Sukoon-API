"""Per-family HTTP boundary contracts for every routed API pattern (Sprint 00, item "contract fixtures").

For each route family in sprints/ROUTE_MATRIX.md this exercises every pattern (aliases and format
variants included) with every declared method, as an anonymous caller, a verified tenant and a staff
administrator, with the MVP release gate on and off. It records what a view rewrite must preserve:
status, content type, response envelope keys, data shape, application error code, Cache-Control and
the URL name that served the request. Committed fixtures live in core_apps/common/route_contracts/.

Scope: path parameters use a fixed unknown UUID/int/slug, and write methods send an empty JSON body,
so detail and command routes record their auth, not-found and validation contracts; parameterless
reads record their success shape. Success payloads for specific objects remain covered by each
family's own tests. Generated on PostgreSQL (the production engine); skipped on SQLite.

Regenerate after an intended contract change:
    ROUTE_CONTRACTS_UPDATE=1 make test-postgres-races PG_TESTS=core_apps/common/test_route_contracts.py
"""

import json
import os
import re
from collections import defaultdict
from pathlib import Path

import pytest
from django.core.cache import caches
from django.db import transaction
from django.urls import resolve
from rest_framework.test import APIClient

from tools.qa.route_matrix import build, concrete_path

FIXTURES = Path(__file__).with_name("route_contracts")
UPDATE = os.environ.get("ROUTE_CONTRACTS_UPDATE") == "1"
IDENTITIES = ("anonymous", "tenant", "staff")
MVP_MODES = (True, False)
FALLBACK_METHODS = ["GET", "POST"]  # plain provider callbacks declare no DRF methods


def family_routes():
    grouped = defaultdict(list)
    for row in build():
        grouped[row["family"]].append(row)
    return dict(sorted(grouped.items()))


FAMILIES = family_routes()


def _slug(family):
    return re.sub(r"[^a-z0-9]+", "-", family.lower()).strip("-") or "root"


_TAKEN = defaultdict(list)
for _family in FAMILIES:
    _TAKEN[_slug(_family)].append(_family)


def slug(family):
    """Readable fixture name; families that differ only in punctuation (e.g. '^users') get a suffix."""
    base = _slug(family)
    if len(_TAKEN[base]) == 1:
        return base
    return f"{base}-{_TAKEN[base].index(family) + 1}"


def shape(value):
    if isinstance(value, dict):
        return sorted(value)
    if isinstance(value, list):
        first = value[0] if value else None
        return ["list", sorted(first) if isinstance(first, dict) else type(first).__name__ if value else "empty"]
    return type(value).__name__


def observe(response):
    content_type = (response.get("Content-Type") or "").split(";")[0]
    envelope, data, code = None, None, response.get("X-App-Error-Code")
    if content_type == "application/json":
        try:
            body = json.loads(response.content or b"null")
        except ValueError:
            body = None
        if isinstance(body, dict):
            envelope = sorted(body)
            data = shape(body.get("data")) if "data" in body else None
            code = code or (body.get("code") if isinstance(body.get("code"), str) else None)
        else:
            envelope = type(body).__name__
    return {
        "status": response.status_code,
        "content_type": content_type,
        "envelope": envelope,
        "data": data,
        "error_code": code,
        "cache_control": response.get("Cache-Control"),
    }


@pytest.fixture
def identities(db):
    from django.contrib.auth import get_user_model
    from core_apps.admin_api.models import StaffProfile

    User = get_user_model()
    tenant = User.objects.create_user(
        email="contract-tenant@example.com", first_name="Contract", last_name="Tenant",
        password="Contract-pass-1", is_verified=True,
    )
    staff = User.objects.create_superuser(
        email="contract-staff@example.com", first_name="Contract", last_name="Staff", password="Contract-pass-1",
    )
    StaffProfile.objects.create(user=staff, role_name="system_owner")
    return {"anonymous": None, "tenant": tenant, "staff": staff}


@pytest.mark.requires_postgres
@pytest.mark.django_db
@pytest.mark.parametrize("family", list(FAMILIES), ids=[slug(f) for f in FAMILIES])
def test_route_family_contract(family, identities, settings):
    observed = {}
    for row in FAMILIES[family]:
        path = concrete_path(row["route"])
        served = resolve(path).url_name or ""
        methods = [m for m in row["methods"] if m.isalpha()] or FALLBACK_METHODS
        for mvp in MVP_MODES:
            settings.SUKOON_MVP = mvp
            for identity in IDENTITIES:
                client = APIClient()
                client.raise_request_exception = False
                if identities[identity] is not None:
                    client.force_authenticate(identities[identity])
                for method in methods:
                    for cache in caches.all():  # throttles must not depend on request order
                        cache.clear()
                    call = getattr(client, method.lower())
                    # Each request runs in its own rolled-back savepoint: no side effects leak into
                    # the next request, and a database error cannot abort the shared test transaction.
                    with transaction.atomic():
                        response = call(path) if method == "GET" else call(path, {}, format="json")
                        transaction.set_rollback(True)
                    observed[f"{method} {path} {identity} mvp={'on' if mvp else 'off'}"] = {
                        "route": row["route"], "served_by": served, **observe(response),
                    }

    fixture = FIXTURES / f"{slug(family)}.json"
    if UPDATE or not fixture.exists():
        FIXTURES.mkdir(exist_ok=True)
        fixture.write_text(json.dumps(observed, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        if not UPDATE:
            pytest.fail(f"Recorded a new contract fixture for {family}; review and commit {fixture.name}")
        return
    expected = json.loads(fixture.read_text(encoding="utf-8"))
    changed = {k: {"expected": expected.get(k), "observed": observed.get(k)}
               for k in sorted(set(expected) | set(observed)) if expected.get(k) != observed.get(k)}
    assert not changed, (
        f"{len(changed)} contract change(s) in {family}; if intended, regenerate with ROUTE_CONTRACTS_UPDATE=1.\n"
        + json.dumps(dict(list(changed.items())[:5]), indent=1)
    )
