from importlib import import_module
from django.apps import apps
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.test import RequestFactory
from django.urls import reverse
import pytest
from core_apps.common.content_models import PublicContentPage
from core_apps.common.contract_testing import api_json
from core_apps.support.models import HelpArticle, HelpContact
from core_apps.admin_api.models import PlatformPreferences, PlatformPreferenceAudit
from core_apps.admin_api.services.settings_service import (
    get_platform_settings,
    update_platform_settings,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def published_catalogs(db):
    # Transaction tests flush migration data. Reuse the approved seed contents
    # explicitly, so this preservation suite also works on a reused empty DB.
    import_module("core_apps.common.migrations.0004_seed_public_content").seed_content(
        apps, None
    )
    import_module("core_apps.support.migrations.0004_seed_help_content").seed_content(
        apps, None
    )
    from core_apps.advertising.models import AdvertisingPlan

    for plan in import_module(
        "core_apps.advertising.migrations.0002_seed_advertising_plans"
    ).PLANS:
        AdvertisingPlan.objects.get_or_create(
            id=plan["id"],
            defaults={key: value for key, value in plan.items() if key != "id"},
        )


def test_admin_content_edit_is_localized_and_visible_without_restart(
    api_client, superuser, user
):
    request = RequestFactory().post("/admin/")
    request.user = user
    entry = admin.site._registry[PublicContentPage]
    assert not entry.has_change_permission(request)
    request.user = superuser
    page = PublicContentPage.objects.get(pk="about-us")
    revision = page.revision
    page.title_ar = "عنوان محدث"
    page.content_ar = "محتوى محدث من لوحة الإدارة"
    entry.save_model(request, page, None, True)
    response = api_client.get(reverse("page-about-us"), {"lang": "ar"})
    value = api_json(response)["data"]
    assert value["title"] == page.title_ar and value["content"] == page.content_ar
    assert value["revision"] == revision + 1 and value["content_format"] == "plain_text"
    assert response["Content-Language"] == "ar"
    assert (
        api_json(api_client.get(reverse("page-about-us"), {"lang": "en"}))["data"][
            "title"
        ]
        == page.title_en
    )
    faq = HelpArticle.objects.get(pk="visit-booking")
    faq.answer_en = "Updated answer from administration."
    admin.site._registry[HelpArticle].save_model(request, faq, None, True)
    result = api_json(
        api_client.get(
            reverse("support-help-center"), {"workspace": "tenant", "lang": "en"}
        )
    )["data"]
    assert result["faqs"][0]["answer"] == faq.answer_en
    faq.active = False
    admin.site._registry[HelpArticle].save_model(request, faq, None, True)
    result = api_json(
        api_client.get(
            reverse("support-help-center"), {"workspace": "tenant", "lang": "en"}
        )
    )["data"]
    assert "visit-booking" not in [row["id"] for row in result["faqs"]]
    page.active = False
    entry.save_model(request, page, None, True)
    assert api_client.get(reverse("page-about-us")).status_code == 404


def test_content_validation_and_seed_replay_preserve_edits():
    page = PublicContentPage.objects.get(pk="terms")
    page.title_en = ""
    with pytest.raises(ValidationError):
        page.full_clean()
    contact = HelpContact.objects.get(pk="owner")
    contact.email = "not an email"
    with pytest.raises(ValidationError):
        contact.full_clean()
    faq = HelpArticle.objects.get(pk="visit-booking")
    faq.answer_en = "Edited text"
    faq.save()
    import_module("core_apps.support.migrations.0004_seed_help_content").seed_content(
        apps, None
    )
    faq.refresh_from_db()
    assert faq.answer_en == "Edited text" and HelpArticle.objects.count() == 10
    import_module("core_apps.common.migrations.0004_seed_public_content").seed_content(
        apps, None
    )
    assert PublicContentPage.objects.count() == 3


def test_inert_settings_are_hidden_without_rewriting_history(superuser):
    previous, _ = PlatformPreferences.objects.get_or_create(pk=1)
    before = dict(previous.values)
    audit = PlatformPreferenceAudit.objects.create(
        actor=superuser, revision=previous.revision, before=before, after=before
    )
    assert get_platform_settings() == {}
    from rest_framework.exceptions import ValidationError as ApiValidationError

    for bad in [
        {"autoVerification": False},
        {"autoVerification": "false"},
        {"authorizationBypass": True},
        [],
    ]:
        with pytest.raises(ApiValidationError):
            update_platform_settings(bad, actor=superuser)
    assert update_platform_settings({}, actor=superuser) == {}
    previous.refresh_from_db()
    audit.refresh_from_db()
    assert previous.values == before and audit.before == before


def test_release_notes_target_exact_version_workspace_schedule_and_language(
    api_client, superuser
):
    from datetime import timedelta
    from django.utils import timezone
    from core_apps.common.content_models import ReleaseNote

    request = RequestFactory().post("/admin/")
    request.user = superuser
    row = ReleaseNote(
        version="1.2.3",
        workspace="owner",
        items_en="Owner changes",
        items_ar="تحديثات المالك",
    )
    admin.site._registry[ReleaseNote].save_model(request, row, None, False)
    route = reverse("release-notes")
    result = api_json(
        api_client.get(
            route, {"version": "1.2.3", "workspace": "owner"}, HTTP_ACCEPT_LANGUAGE="ar"
        )
    )["data"]
    assert result["items"] == ["تحديثات المالك"]
    for version, workspace in [("1.2.4", "owner"), ("1.2.3", "tenant")]:
        assert (
            api_json(
                api_client.get(route, {"version": version, "workspace": workspace})
            )["data"]["items"]
            == []
        )
    row.publish_at = timezone.now() + timedelta(days=1)
    row.save()
    assert (
        api_json(api_client.get(route, {"version": "1.2.3", "workspace": "owner"}))[
            "data"
        ]["items"]
        == []
    )
    assert (
        api_client.get(
            route, {"version": "arbitrary/script", "workspace": "tenant"}
        ).status_code
        == 400
    )
    row.version = "invalid"
    with pytest.raises(ValidationError):
        row.full_clean()


def test_advertising_catalog_edit_changes_revision_and_validates_values(
    auth_client, user
):
    from core_apps.advertising.models import AdvertisingPlan, MockAdvertisementPayment

    plan = AdvertisingPlan.objects.first()
    before = plan.revision
    request = RequestFactory().post("/admin/")
    request.user = user
    assert not admin.site._registry[AdvertisingPlan].has_change_permission(request)
    plan.title_ar = "خطة إعلانات محدثة"
    admin.site._registry[AdvertisingPlan].save_model(request, plan, None, True)
    assert plan.revision != before
    assert not admin.site._registry[MockAdvertisementPayment].has_change_permission(
        request
    )
    plan.duration_count = 0
    with pytest.raises(ValidationError):
        plan.full_clean()
