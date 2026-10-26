"""Catalog edits are versioned and never rewrite an issued purchase or grant."""

import uuid
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from core_apps.admin_api.models import StaffProfile
from core_apps.admin_api.tests.test_content_editor import operator, client, save, ROOT
from core_apps.common.content_models import ContentEditAudit
from core_apps.features.models import (
    SubscriptionPlan,
    PromotionOption,
    CommerceFeature,
    PlanBenefit,
)
from core_apps.advertising.models import AdvertisingPlan
from core_apps.features.tests import test_billing_subscriptions as billing

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "role",
    [
        "support",
        "financial_approver",
        "property_reviewer",
        "security_recovery_reviewer",
    ],
)
def test_catalog_authority_is_not_inherited_from_operational_roles(role):
    actor = get_user_model().objects.create_user(
        email=f"{role}@example.test", password="local"
    )
    StaffProfile.objects.create(user=actor, role_name=role)
    api = client(actor)
    assert api.get(ROOT).status_code == 403
    assert (
        save(api, "subscription_plans", {"name_en": "Unauthorized"})[0].status_code
        == 403
    )


def test_subscription_catalog_reaches_mobile_and_preserves_invoice_and_benefits():
    actor = operator()
    api = client(actor)
    created, key = save(
        api,
        "subscription_plans",
        {
            "name_ar": "اختبار محلي",
            "name_en": "Local fixture",
            "description_ar": "",
            "description_en": "",
            "workspace": "both",
            "audience": "personal",
            "period_months": 1,
            "amount_minor": 12500,
            "active": True,
            "sort_order": 5,
        },
    )
    assert created.status_code == 201, created.data
    identity = created.data["id"]
    plan = SubscriptionPlan.objects.get(id=identity)
    feature = CommerceFeature.objects.create(
        code="existing-test-feature",
        workspace="tenant",
        label_en="Existing",
        label_ar="قائم",
        available=True,
        free=True,
        enforced=False,
    )
    benefit = PlanBenefit.objects.create(plan=plan, feature=feature, included=True)
    buyer = get_user_model().objects.create_user(
        email="catalog-buyer@example.test", password="local"
    )
    buyer_api = client(buyer)
    original = billing.body(billing.issue(buyer_api, plan)[0], 201)
    changed, changed_key = save(
        api,
        "subscription_plans",
        {
            "name_ar": "وصف محدث",
            "amount_minor": 18000,
            "period_months": 2,
        },
        1,
        identity,
    )
    assert changed.status_code == 200 and changed.data["revision"] == 2
    repeated, _ = save(
        api,
        "subscription_plans",
        {
            "name_ar": "وصف محدث",
            "amount_minor": 18000,
            "period_months": 2,
        },
        1,
        identity,
        changed_key,
    )
    assert repeated.data == changed.data
    assert (
        save(api, "subscription_plans", {"name_ar": "stale"}, 1, identity)[
            0
        ].status_code
        == 409
    )
    catalog = billing.body(
        buyer_api.get(billing.ROOT + "subscription-plans/", HTTP_ACCEPT_LANGUAGE="ar")
    )
    current = next(row for row in catalog if row["id"] == identity)
    assert current["amount_minor"] == 18000 and current["name"] == "وصف محدث"
    receipt = billing.body(
        buyer_api.get(billing.ROOT + f"billing/invoices/{original['id']}/")
    )
    assert receipt["total_minor"] == 12500
    from core_apps.features.models import RentInvoice

    saved = RentInvoice.objects.get(id=original["id"])
    assert saved.purchase_snapshot["period_months"] == 1
    benefit.refresh_from_db()
    feature.refresh_from_db()
    assert benefit.included and feature.free and not feature.enforced
    assert (
        save(api, "subscription_plans", {"enforced": True}, 2, identity)[0].status_code
        == 400
    )
    assert (
        save(api, "subscription_plans", {"audience": "organization"}, 2, identity)[
            0
        ].status_code
        == 400
    )
    inactive, _ = save(api, "subscription_plans", {"active": False}, 2, identity)
    assert inactive.status_code == 200
    catalog = billing.body(buyer_api.get(billing.ROOT + "subscription-plans/"))
    assert identity not in [row["id"] for row in catalog]
    assert RentInvoice.objects.filter(id=original["id"]).exists()
    assert api.delete(ROOT + f"subscription_plans/{identity}/").status_code == 405
    assert (
        ContentEditAudit.objects.filter(
            kind="subscription_plans", object_id=identity
        ).count()
        == 3
    )


def test_advertising_preserves_opaque_revision_and_recovery():
    api = client(operator())
    existing = AdvertisingPlan.objects.create(
        id="local-ad",
        title_en="Local",
        title_ar="محلي",
        duration_unit="week",
        amount_minor=100000,
        revision=uuid.uuid4().hex,
    )
    prior = existing.revision
    changed, key = save(
        api, "advertising_plans", {"title_ar": "عنوان محفوظ"}, prior, existing.id
    )
    assert changed.status_code == 200, changed.data
    assert (
        isinstance(changed.data["revision"], str) and changed.data["revision"] != prior
    )
    assert (
        save(api, "advertising_plans", {"title_ar": "آخر"}, prior, existing.id)[
            0
        ].status_code
        == 409
    )
    recovered = api.post(
        ROOT + f"advertising_plans/receipts/{key}/",
        {"identity": existing.id},
        format="json",
    )
    assert recovered.data["receipt"] == changed.data
    assert (
        save(
            api,
            "advertising_plans",
            {"id": "different"},
            changed.data["revision"],
            existing.id,
        )[0].status_code
        == 400
    )
    public = api.get(reverse("advertising:plan-list"), HTTP_ACCEPT_LANGUAGE="ar")
    assert public.status_code == 200
    assert "عنوان محفوظ" in str(public.data)
    detail = api.get(ROOT + f"advertising_plans/{existing.id}/").data
    assert (
        len(detail["history"]) == 1
        and detail["history"][0]["before"]["revision"] == prior
    )


def test_free_promotion_is_managed_without_becoming_a_paid_gate():
    api = client(operator())
    created, _ = save(
        api,
        "promotion_options",
        {
            "id": "local-free",
            "title_ar": "مجاني محلي",
            "title_en": "Local free",
            "duration_days": 7,
            "amount_minor": 0,
            "active": True,
            "sort_order": 0,
        },
    )
    assert created.status_code == 201, created.data
    assert (
        save(api, "promotion_options", {"amount_minor": 100}, 1, "local-free")[
            0
        ].status_code
        == 400
    )
    changed, _ = save(api, "promotion_options", {"duration_days": 9}, 1, "local-free")
    assert changed.status_code == 200
    catalog = billing.body(
        api.get(billing.ROOT + "configuration/", {"workspace": "owner"})
    )
    current = next(row for row in catalog["boost_options"] if row["id"] == "local-free")
    assert (
        current["duration_days"] == 9
        and PromotionOption.objects.get(pk="local-free").amount_minor == 0
    )
    inactive, _ = save(api, "promotion_options", {"active": False}, 2, "local-free")
    assert inactive.status_code == 200
    assert (
        save(api, "promotion_options", {"active": True}, 3, "local-free")[0].status_code
        == 200
    )
    assert api.delete(ROOT + "promotion_options/local-free/").status_code == 405


def test_catalog_schema_exposes_supported_fields_and_current_revision_format():
    api = client(operator())
    result = api.get(ROOT)
    assert result.status_code == 200
    catalogs = {row["kind"]: row for row in result.data["catalogs"]}
    for kind in ["subscription_plans", "advertising_plans", "promotion_options"]:
        assert catalogs[kind]["guidance"]
        fields = {f["name"] for f in catalogs[kind]["fields"]}
        assert not fields & {
            "enforced",
            "currency",
            "exponent",
            "permissions",
            "entitlements",
            "benefits",
        }
    assert catalogs["advertising_plans"]["revision_type"] == "opaque"
    assert catalogs["subscription_plans"]["revision_type"] == "integer"
