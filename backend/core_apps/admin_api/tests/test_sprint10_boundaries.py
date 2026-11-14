"""Current command authority, replay and honest operational history."""

from contextlib import nullcontext
from uuid import uuid4
from unittest.mock import patch

import pytest
from django.contrib import admin
from django.db import DatabaseError
from django.test import RequestFactory
from django.urls import reverse
from rest_framework.exceptions import PermissionDenied, ValidationError

from core_apps.admin_api.models import StaffProfile, UserReport
from core_apps.admin_api.permissions import require_staff_actor
from core_apps.admin_api.services.report_service import take_report_action
from core_apps.admin_api.services.system_service_parts.get_audit_logs import (
    get_audit_logs,
)
from core_apps.common.content_admin import PublicContentPageAdmin
from core_apps.common.content_models import PublicContentPage, ContentEditAudit
from core_apps.properties.models import PropertyModerationDecision
from core_apps.properties.services.moderation import decide, version
from tools.qa.performance import measured

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("action", ["dismiss", "mark_active"])
@pytest.mark.parametrize("blocked", ["disabled", "frozen", "removed"])
def test_report_service_rechecks_stale_actor(action, blocked, user, another_user):
    profile = StaffProfile.objects.create(user=another_user, role_name="support")
    require_staff_actor(another_user)  # Prime a formerly authorized actor.
    if blocked == "disabled":
        StaffProfile.objects.filter(pk=profile.pk).update(is_active=False)
    elif blocked == "frozen":
        type(another_user).objects.filter(pk=another_user.pk).update(
            sensitive_actions_frozen=True
        )
    else:
        profile.delete()
    report = UserReport.objects.create(reported_user=user, reason="Synthetic")
    with pytest.raises(PermissionDenied):
        take_report_action(report.id, action, another_user)
    report.refresh_from_db()
    assert report.status == "active" and report.reviewed_by_id is None


@pytest.mark.parametrize(
    "role", ["support", "support_supervisor", "kyc_reviewer", "main_admin"]
)
def test_report_non_suspension_retains_broad_staff_scope(role, user, another_user):
    StaffProfile.objects.create(user=another_user, role_name=role)
    report = UserReport.objects.create(reported_user=user, reason="Synthetic")
    assert take_report_action(report.id, "dismiss", another_user).status == "dismissed"
    with pytest.raises(PermissionDenied) if role != "main_admin" else nullcontext():
        take_report_action(report.id, "suspend_user", another_user)


@pytest.mark.parametrize("alias", ["legacy", "canonical"])
def test_moderation_alias_replay_rechecks_role_and_factor(
    alias, superuser, user, make_property, api_client
):
    prop = make_property(owner=user)
    StaffProfile.objects.create(user=superuser, role_name="system_owner")
    prop.refresh_from_db()
    payload = {"expected_version": version(prop), "reason": "Synthetic violation"}
    url = (
        reverse("admin-moderation-delete", kwargs={"property_id": prop.id})
        if alias == "legacy"
        else f"/api/v1/admin/properties/{prop.id}/block/"
    )
    api_client.force_authenticate(superuser)
    key = str(uuid4())
    assert (
        api_client.post(
            url, payload, format="json", HTTP_IDEMPOTENCY_KEY=key
        ).status_code
        == 200
    )
    replay = api_client.post(url, payload, format="json", HTTP_IDEMPOTENCY_KEY=key)
    assert replay.status_code == 200 and replay["Idempotency-Replayed"] == "true"
    type(superuser).objects.filter(pk=superuser.pk).update(
        sensitive_actions_frozen=True
    )
    assert (
        api_client.post(
            url, payload, format="json", HTTP_IDEMPOTENCY_KEY=key
        ).status_code
        == 403
    )
    type(superuser).objects.filter(pk=superuser.pk).update(
        sensitive_actions_frozen=False
    )
    StaffProfile.objects.filter(user=superuser).update(is_active=False)
    assert (
        api_client.post(
            url, payload, format="json", HTTP_IDEMPOTENCY_KEY=key
        ).status_code
        == 403
    )
    assert PropertyModerationDecision.objects.filter(property=prop).count() == 1


def test_moderation_command_fences_original_session_on_replay(
    superuser, user, make_property
):
    from core_apps.users.services.sessions import issue_refresh, revoke_all
    from rest_framework_simplejwt.exceptions import AuthenticationFailed

    claims = issue_refresh(superuser).access_token
    prop = make_property(owner=user)
    prop.refresh_from_db()
    command = dict(
        reviewer=superuser,
        action="block",
        expected_version=version(prop),
        request_key=str(uuid4()),
        reason="Synthetic",
        auth_claims=claims,
    )
    decide(prop.id, **command)
    revoke_all(superuser)
    with pytest.raises(AuthenticationFailed):
        decide(prop.id, **command)
    assert PropertyModerationDecision.objects.filter(property=prop).count() == 1


@pytest.mark.parametrize(
    "payload", [[], ["unexpected"], {"expected_version": {}}, {"expected_version": 12}]
)
def test_legacy_moderation_rejects_malformed_command(
    payload, superuser, user, make_property, api_client
):
    prop = make_property(owner=user)
    api_client.force_authenticate(superuser)
    response = api_client.post(
        reverse("admin-moderation-delete", kwargs={"property_id": prop.id}),
        payload,
        format="json",
    )
    assert response.status_code == 400
    assert not PropertyModerationDecision.objects.filter(property=prop).exists()


def test_audit_database_failure_is_not_an_empty_history():
    with patch(
        "core_apps.support.models.TicketTransition.objects.select_related",
        side_effect=DatabaseError("private database address"),
    ):
        with pytest.raises(DatabaseError):
            get_audit_logs(type_filter="support")


def test_native_content_requires_current_domain_role(superuser, user):
    page = PublicContentPage.objects.create(
        slug="sprint10", title_en="Before", content_en="Original"
    )
    model_admin = PublicContentPageAdmin(PublicContentPage, admin.site)
    request = RequestFactory().post("/admin/")
    request.user = superuser
    StaffProfile.objects.create(
        user=superuser, role_name="system_owner", is_active=False
    )
    page.title_en = "Must not save"
    from django.core.exceptions import PermissionDenied as NativePermissionDenied

    with pytest.raises(NativePermissionDenied):
        model_admin.save_model(request, page, None, True)
    page.refresh_from_db()
    assert (
        page.title_en == "Before"
        and not ContentEditAudit.objects.filter(object_id=str(page.pk)).exists()
    )


@pytest.mark.parametrize("size", [1, 20, 100])
def test_campaign_preview_batch_budget(size, superuser, django_user_model):
    from core_apps.admin_api.services.workspace_campaigns import preview
    from core_apps.profiles.models import UserSettings

    users = django_user_model.objects.bulk_create(
        [
            django_user_model(email=f"s10-{i}@example.invalid", password="!")
            for i in range(size)
        ]
    )
    UserSettings.objects.bulk_create(
        [UserSettings(user=user, promotions_and_updates=True) for user in users]
    )
    item, report = measured(
        "sprint10-campaign-preview",
        size,
        lambda: preview(
            superuser,
            {
                "title": "Synthetic",
                "body": "No provider calls",
                "audience": "all",
                "request_key": str(uuid4()),
            },
        ),
    )
    assert item.recipients.count() == size
    # Fixed per 500-account batch, including preference initialization and writes.
    assert report["queries"] <= 20


@pytest.mark.parametrize("mvp", [True, False])
@pytest.mark.parametrize(
    "audience", ["all", "landlords", "tenants", "verified", "students", "companies"]
)
def test_prepared_campaign_spaces_match_current_service(
    mvp, audience, user, settings, make_property
):
    from core_apps.admin_api.services.campaign_audience import candidates, spaces
    from core_apps.admin_api.services.workspace_campaigns import eligible_spaces
    from core_apps.features.company_models import Company, CompanyMembership
    from core_apps.features.student_models import StudentProfile
    from core_apps.features.planning_models import HousingRequest
    from core_apps.users.models import User

    settings.SUKOON_MVP = mvp
    make_property(owner=user)
    StudentProfile.objects.create(user=user)
    company = Company.objects.create(
        name="Synthetic",
        registration_number="S10",
        contact_email="s10@example.invalid",
        review_status="verified",
    )
    CompanyMembership.objects.create(company=company, user=user, is_employee=True)
    from django.utils import timezone

    HousingRequest.objects.create(
        user=user, title="Synthetic renter", expires_at=timezone.now()
    )
    expected = eligible_spaces(User.objects.get(pk=user.pk), audience)
    rows = list(candidates(User.objects.filter(pk=user.pk), audience))
    assert (spaces(rows[0], audience) if rows else set()) == expected


def test_role_summary_uses_one_grouped_query(superuser, django_assert_num_queries):
    from core_apps.admin_api.services.staff_service import get_roles_summary

    StaffProfile.objects.create(user=superuser, role_name="system_owner")
    with django_assert_num_queries(1):
        roles = get_roles_summary()
    assert next(row for row in roles if row["id"] == "system_owner")["userCount"] == 1


def test_native_content_supported_form_save_records_revision_and_audit(superuser):
    page, _ = PublicContentPage.objects.update_or_create(
        slug="about-us",
        defaults={
            "title_en": "Before",
            "title_ar": "عنوان",
            "content_en": "Original",
            "content_ar": "محتوى",
            "revision": 1,
        },
    )
    request = RequestFactory().post("/admin/")
    request.user = superuser
    page.title_en = "Reviewed native edit"
    PublicContentPageAdmin(PublicContentPage, admin.site).save_model(
        request, page, None, True
    )
    page.refresh_from_db()
    audit = ContentEditAudit.objects.get(kind="pages", object_id=str(page.pk))
    assert page.revision == audit.revision == 2
    assert (
        audit.actor_id == superuser.pk
        and audit.after["values"]["title_en"] == "Reviewed native edit"
    )


def test_native_tour_emergency_suppression_rechecks_disabled_profile(
    superuser, user, make_property
):
    from core_apps.virtual_tours.admin_commands import disable_viewing
    from core_apps.virtual_tours.models import PropertyVirtualTour

    prop = make_property(owner=user)
    tour = PropertyVirtualTour.objects.create(property=prop, kind="panorama_360")
    StaffProfile.objects.create(
        user=superuser, role_name="system_owner", is_active=False
    )
    with pytest.raises(PermissionDenied):
        disable_viewing(superuser, [tour.pk])
    tour.refresh_from_db()
    assert tour.disabled is False
    StaffProfile.objects.filter(user=superuser).update(is_active=True)
    assert disable_viewing(superuser, [tour.pk]) == 1
    tour.refresh_from_db()
    assert tour.disabled is True


@pytest.mark.parametrize("party", ["reported_user", "reporter"])
@pytest.mark.parametrize(
    "action", ["dismiss", "mark_active", "suspend_user", "ban_user"]
)
def test_report_decision_requires_independent_reviewer(party, action, user, superuser):
    StaffProfile.objects.create(user=superuser, role_name="system_owner")
    report = UserReport.objects.create(
        reported_user=user,
        reason="Synthetic",
        **({"reporter": superuser} if party == "reporter" else {}),
    )
    if party == "reported_user":
        UserReport.objects.filter(pk=report.pk).update(reported_user=superuser)
    with pytest.raises(PermissionDenied, match="independent reviewer"):
        take_report_action(report.id, action, superuser)
    report.refresh_from_db()
    assert report.status == "active" and report.reviewed_by_id is None


def test_legacy_supplied_whitespace_version_is_stale_not_bodyless_fallback(
    superuser, user, make_property, api_client
):
    prop = make_property(owner=user)
    api_client.force_authenticate(superuser)
    response = api_client.post(
        reverse("admin-moderation-delete", kwargs={"property_id": prop.id}),
        {"expected_version": " "},
        format="json",
        HTTP_IDEMPOTENCY_KEY="literal-whitespace-version",
    )
    assert response.status_code == 409
    assert not PropertyModerationDecision.objects.filter(property=prop).exists()
