"""Callable renames must not change method policy or wrapper error precedence."""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.utils.module_loading import import_string
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate

from core_apps.features.http import ActionPolicy, FeatureAPIView
from core_apps.features.services.company.role_context import CompanyRoleMiddleware
from core_apps.features.services.company.role_routes import authorize, authorize_policy

EVIDENCE = Path(__file__).resolve().parents[3] / "sprints/evidence/sprint-07"


def test_every_company_method_keeps_the_original_role_gate():
    for row in json.loads((EVIDENCE / "company-policy-before.json").read_text()):
        cls = import_string(row["class"])
        policy = cls.action_policies[row["method"]]
        assert (policy.resource, policy.action, policy.boundary) == (
            row["resource"],
            row["action"],
            "company",
        )
        request = SimpleNamespace(
            user=SimpleNamespace(),
            method=row["method"].upper(),
            headers={"X-Sukoon-Company-Role": row["role"]},
        )

        def check(_):
            try:
                authorize_policy(request, policy.resource, policy.action)
            except PermissionDenied as exc:
                return exc.get_codes()
            return "allowed"

        assert CompanyRoleMiddleware(check)(request) == row["outcome"], row

        def compatibility_check(_):
            try:
                authorize(request, cls.as_view())
            except PermissionDenied as exc:
                return exc.get_codes()
            return "allowed"

        assert (
            CompanyRoleMiddleware(compatibility_check)(request) == row["outcome"]
        ), row


def call(view, method="post", body=b"{}"):
    request = APIRequestFactory().generic(
        method.upper(), "/", body, content_type="application/json"
    )
    force_authenticate(request, user=SimpleNamespace(is_authenticated=True))
    return view.as_view()(request)


class PlanningProbe(FeatureAPIView):
    throttle_classes = []
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    action_policies = {"post": ActionPolicy("probe", "save", "planning")}

    def post(self, request):
        return Response({"saved": True})


def test_capability_precedes_body_parsing_and_only_runs_for_declared_methods():
    with patch(
        "core_apps.features.services.planning.require_planning",
        side_effect=PermissionDenied("disabled"),
    ) as gate:
        assert call(PlanningProbe, body=b"{").status_code == 403
        assert gate.call_count == 1
        assert call(PlanningProbe, method="head").status_code == 405
        assert call(PlanningProbe, method="options").status_code == 200
        assert gate.call_count == 1


@pytest.mark.parametrize("body", [b"[]", b'{"selection":[]}'])
def test_planning_types_fail_before_command(body):
    with patch("core_apps.features.services.planning.require_planning"):
        assert call(PlanningProbe, body=body).status_code == 400


def test_success_keeps_planning_privacy_and_domain_errors_keep_wrapper_translation():
    with patch("core_apps.features.services.planning.require_planning"):
        response = call(PlanningProbe)
        assert response.status_code == 200
        assert response["Cache-Control"] == "private, no-store"
        with patch.object(
            PlanningProbe, "post", side_effect=DjangoValidationError("bad")
        ):
            assert call(PlanningProbe).status_code == 400

    class CompanyProbe(PlanningProbe):
        action_policies = {"post": ActionPolicy("company_views", "members", "company")}

    with patch.object(CompanyProbe, "post", side_effect=IntegrityError("duplicate")):
        assert call(CompanyProbe).status_code == 400


def test_preparation_actor_authority_precedes_invalid_scope_validation():
    from core_apps.features.company_contract_views import PreparationsView

    request = APIRequestFactory().get("/?company_id=invalid")
    force_authenticate(
        request,
        user=SimpleNamespace(
            is_authenticated=True,
            is_active=True,
            is_verified=False,
        ),
    )
    response = PreparationsView.as_view(throttle_classes=[])(request)
    assert response.status_code == 403
