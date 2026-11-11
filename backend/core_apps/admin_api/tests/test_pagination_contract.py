"""Rendered list contracts, independent of financial calculations and persistent data."""

import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from core_apps.admin_api import permissions
from core_apps.admin_api.views import financials, system


@pytest.fixture(
    params=[
        (
            financials,
            financials.AdminTransactionListAPIView,
            "get_transactions_list",
            "status",
            "paid",
            "status_filter",
        ),
        (
            system,
            system.AdminAuditLogsAPIView,
            "get_audit_logs",
            "type",
            "kyc",
            "type_filter",
        ),
    ],
    ids=["transactions", "audit_logs"],
)
def endpoint(request, monkeypatch, settings):
    settings.ALLOWED_HOSTS = ["testserver"]
    module, view, service_name, query_name, query_value, service_filter = request.param
    rows = [
        {"id": f"row-{index}", "description": f"Record {index}"} for index in range(16)
    ]
    service = Mock(return_value=rows)
    monkeypatch.setattr(module, service_name, service)
    # Fake only the current-authority database reads. Real permission classes and
    # require_staff_actor run, including re-reading current status instead of cached user flags.
    current = SimpleNamespace(pk=1, is_active=True, is_staff=True, is_superuser=False)
    profile = SimpleNamespace(is_active=True, role_name="system_owner")
    users = Mock()
    users.get.return_value = current
    profiles = Mock()
    profiles.filter.return_value.first.return_value = profile
    monkeypatch.setattr(
        permissions, "get_user_model", lambda: SimpleNamespace(objects=users)
    )
    monkeypatch.setattr(permissions.StaffProfile, "objects", profiles)
    return SimpleNamespace(
        view=view,
        service=service,
        rows=rows,
        current=current,
        profile=profile,
        users=users,
        query_name=query_name,
        query_value=query_value,
        service_filter=service_filter,
    )


def rendered(endpoint, query=None, *, authenticated=True):
    request = APIRequestFactory().get(
        "/api/v1/admin/test-list/", query or {}, HTTP_ACCEPT="application/json"
    )
    if authenticated:
        # Intentionally cached optimistic flags: authorization must use the current actor fixture.
        force_authenticate(
            request,
            user=SimpleNamespace(pk=1, is_authenticated=True, is_superuser=True),
        )
    response = endpoint.view.as_view()(request)
    response.render()
    return response, json.loads(response.content)


def assert_page(
    response, body, *, rows, page, total, pages, next_page=None, previous=None
):
    assert response.status_code == 200
    assert set(body) == {"message", "data"}
    assert body["data"] == rows
    expected = {
        "X-Page": str(page),
        "X-Per-Page": "10",
        "X-Total-Count": str(total),
        "X-Total-Pages": str(pages),
    }
    for header, value in expected.items():
        assert response[header] == value
        assert header in response["Access-Control-Expose-Headers"]
    assert response.get("X-Next-Page") == next_page
    assert response.get("X-Previous-Page") == previous


def test_first_page_has_authoritative_metadata(endpoint):
    response, body = rendered(endpoint)
    assert_page(
        response,
        body,
        rows=endpoint.rows[:10],
        page=1,
        total=16,
        pages=2,
        next_page="2",
    )
    endpoint.service.assert_called_once_with(
        **{endpoint.service_filter: None, "search": None, "paginated": True}
    )
    endpoint.users.get.assert_called_once_with(pk=1)


def test_last_page_keeps_page_size_ten(endpoint):
    response, body = rendered(endpoint, {"page": 2})
    assert_page(
        response, body, rows=endpoint.rows[10:], page=2, total=16, pages=2, previous="1"
    )


def test_exact_search_does_not_turn_result_length_into_page_size(endpoint):
    endpoint.service.return_value = endpoint.rows[:1]
    response, body = rendered(
        endpoint, {"search": "Record 0", endpoint.query_name: endpoint.query_value}
    )
    assert_page(response, body, rows=endpoint.rows[:1], page=1, total=1, pages=1)
    endpoint.service.assert_called_once_with(
        **{endpoint.service_filter: endpoint.query_value, "search": "Record 0", "paginated": True}
    )


def test_empty_results_keep_authoritative_size_and_one_empty_page(endpoint):
    endpoint.service.return_value = []
    response, body = rendered(endpoint)
    assert_page(response, body, rows=[], page=1, total=0, pages=1)


@pytest.mark.parametrize("requested_size", [1, 100, "invalid"])
def test_page_size_query_remains_ignored(endpoint, requested_size):
    response, body = rendered(endpoint, {"page_size": requested_size})
    assert_page(
        response,
        body,
        rows=endpoint.rows[:10],
        page=1,
        total=16,
        pages=2,
        next_page="2",
    )


@pytest.mark.parametrize("page", [0, 3, "invalid"])
def test_invalid_page_still_returns_404(endpoint, page):
    response, body = rendered(endpoint, {"page": page})
    assert response.status_code == 404
    assert body["data"] is None
    assert not response.has_header("X-Page")


def test_anonymous_request_denied_before_list_service(endpoint):
    response, body = rendered(endpoint, authenticated=False)
    assert response.status_code == 401
    assert body["data"] is None
    endpoint.service.assert_not_called()
    endpoint.users.get.assert_not_called()


@pytest.mark.parametrize("changed", ["user_inactive", "staff_inactive", "wrong_role"])
def test_current_authority_denial_is_not_bypassed_by_cached_superuser(
    endpoint, changed
):
    if changed == "user_inactive":
        endpoint.current.is_active = False
    elif changed == "staff_inactive":
        endpoint.profile.is_active = False
    else:
        endpoint.profile.role_name = "support"
    response, body = rendered(endpoint)
    assert response.status_code == 403
    assert body["data"] is None
    endpoint.service.assert_not_called()
    endpoint.users.get.assert_called_once_with(pk=1)
