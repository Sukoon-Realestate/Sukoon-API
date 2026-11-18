"""Enabled company authority through real login and HTTP, not forced auth."""

import hashlib
import json
import os
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model

from core_apps.features.company_models import CompanyMembership
from core_apps.features.services.company import membership
from tools.qa.connected_http import ConnectedHTTP


@pytest.mark.integration
@pytest.mark.mvp_deferred
@pytest.mark.django_db(transaction=True)
def test_company_role_scope_and_current_membership_over_http(live_server, settings):
    settings.SECURITY_TEST_BYPASS = False
    settings.COMPANY_HOUSING_ENABLED = True
    actors = [get_user_model().objects.create_user(
        email=f"company-http-{name}@example.invalid", password="Connected-role-42!",
        first_name=name, last_name="Acceptance", is_verified=True,
    ) for name in ("coordinator", "employee", "outsider")]
    coordinator, employee, outsider = actors
    company = membership.create_company(coordinator, {
        "name": "Connected acceptance company", "registration_number": "CONNECTED-QA-ONLY",
        "contact_email": "company-http@example.invalid",
    })
    CompanyMembership.objects.filter(company=company, user=coordinator).update(is_coordinator=True)
    CompanyMembership.objects.create(company=company, user=employee, is_employee=True)
    clients = [ConnectedHTTP(live_server.url) for _ in actors]
    for client, actor in zip(clients, actors):
        client.request("POST", "/api/v1/auth/login/", 200, body={
            "email": actor.email, "password": "Connected-role-42!",
        })
    manager, worker, stranger = clients
    prefix = "/api/v1/features/v1/companies/"
    detail = f"{prefix}{company.id}/"
    contexts = detail + "role-contexts/"
    rows = manager.request("GET", prefix, 200)["data"]
    assert len(rows) == 1 and rows[0]["id"] == str(company.id)
    assert not {"readiness", "budget_limit_minor", "permissions", "contact_email"} & rows[0].keys()
    assert stranger.request("GET", prefix, 200)["data"] == []
    assert {row["role"] for row in manager.request("GET", contexts, 200)["data"]["roles"]} == {
        "admin", "coordinator",
    }
    assert {row["role"] for row in worker.request("GET", contexts, 200)["data"]["roles"]} == {"employee"}
    manager.opener.addheaders = [("X-Sukoon-Company-ID", str(company.id)), ("X-Sukoon-Company-Role", "coordinator")]
    assert manager.request("GET", detail, 200)["data"]["id"] == str(company.id)
    worker.opener.addheaders = [("X-Sukoon-Company-ID", str(company.id)), ("X-Sukoon-Company-Role", "coordinator")]
    worker.request("GET", detail, 403)
    worker.opener.addheaders = [("X-Sukoon-Company-ID", str(company.id)), ("X-Sukoon-Company-Role", "employee")]
    assert worker.request("GET", detail, 200)["data"]["id"] == str(company.id)
    stranger.opener.addheaders = [("X-Sukoon-Company-ID", str(company.id)), ("X-Sukoon-Company-Role", "coordinator")]
    denied = stranger.request("GET", detail, 404)
    assert company.name not in json.dumps(denied)
    # A fixture-side authority change must affect the very next HTTP request.
    CompanyMembership.objects.filter(company=company, user=coordinator).update(is_active=False)
    manager.request("GET", detail, 404)
    assert worker.request("GET", detail, 200)["data"]["id"] == str(company.id)
    assert stranger.request("GET", prefix, 200)["data"] == []

    target = os.environ.get("CONNECTED_ACCEPTANCE_OUT")
    if target:
        root = Path(__file__).resolve().parents[2]
        sources = ["core_apps/common/test_connected_company_acceptance.py", "tools/qa/connected_http.py",
                   "core_apps/features/company_views.py", "core_apps/features/services/company/role_context.py",
                   "core_apps/features/services/company/role_routes.py"]
        output = Path(target)
        output.mkdir(parents=True, exist_ok=True)
        (output / "company-authority-restoration.json").write_text(json.dumps({
            "schema_version": 1, "result": "passed", "transport": "loopback_http",
            "release_mode": "restoration", "security_test_bypass": False,
            "scenario": "company_role_scope_and_current_membership",
            "prerequisites": "synthetic accounts/company/memberships seeded; no financial or provider transitions",
            "assertions": ["discovery_minimizes_private_data", "outsider_discovery_empty",
                           "explicit_role_contexts", "employee_role_spoof_rejected",
                           "outsider_role_spoof_rejected", "revocation_effective_next_request",
                           "other_member_access_preserved"],
            "source_sha256": {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in sources},
            "observations": [{**row, "path": row["path"].replace(str(company.id), "{company_id}")}
                             for client in clients for row in client.observations],
        }, indent=2) + "\n")
