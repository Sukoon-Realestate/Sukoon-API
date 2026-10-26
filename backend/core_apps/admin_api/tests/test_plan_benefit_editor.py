"""Existing benefit catalog changes preserve purchased access and immutable policy flags."""

from datetime import timedelta
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from core_apps.admin_api.tests.test_content_editor import operator, client, save, ROOT
from core_apps.common.content_models import ContentEditAudit
from core_apps.features.models import (
    CommerceFeature,
    PlanBenefit,
    SubscriptionPlan,
    RentInvoice,
    AccountSubscription,
)
from core_apps.features.services.entitlements import decision
from core_apps.features.tests import test_billing_subscriptions as billing
from core_apps.features.tests.test_cycle_concurrency import parallel_calls

pytestmark = pytest.mark.django_db


@pytest.fixture
def catalog():
    plan = SubscriptionPlan.objects.create(
        name_ar="خطة محلية",
        name_en="Local plan",
        workspace="tenant",
        audience="personal",
        period_months=1,
        amount_minor=12500,
    )
    feature = CommerceFeature.objects.create(
        code="existing-reviewed-feature",
        workspace="tenant",
        label_ar="ميزة قائمة",
        label_en="Existing feature",
        available=True,
        free=False,
        enforced=False,
    )
    return plan, feature


def values(plan, feature, **changes):
    return {
        "plan": str(plan.id),
        "feature": str(feature.id),
        "included": True,
        "limit": 5,
        **changes,
    }


def test_benefit_edits_version_plan_and_keep_issued_snapshot_and_access(catalog):
    plan, feature = catalog
    api = client(operator())
    created, key = save(api, "plan_benefits", values(plan, feature))
    assert created.status_code == 201, created.data
    benefit = PlanBenefit.objects.get(id=created.data["id"])
    plan.refresh_from_db()
    assert plan.revision == 2 and benefit.revision == 1
    assert created.data["relation_labels"] == {
        "plan": plan.name_ar,
        "feature": feature.label_ar,
    }
    buyer = get_user_model().objects.create_user(
        email="benefit-buyer@example.invalid", password="local"
    )
    buyer_api = client(buyer)
    invoice_data = billing.body(billing.issue(buyer_api, plan)[0], 201)
    invoice = RentInvoice.objects.get(id=invoice_data["id"])
    subscription = AccountSubscription.objects.create(
        user=buyer,
        plan=plan,
        invoice=invoice,
        workspace="tenant",
        plan_snapshot=invoice.purchase_snapshot,
        starts_at=timezone.now() - timedelta(minutes=1),
        ends_at=timezone.now() + timedelta(days=30),
    )
    changed, changed_key = save(api, "plan_benefits", {"limit": 9}, 1, str(benefit.id))
    assert changed.status_code == 200, changed.data
    plan.refresh_from_db()
    assert plan.revision == 3 and changed.data["revision"] == 2
    replay, _ = save(
        api, "plan_benefits", {"limit": 9}, 1, str(benefit.id), changed_key
    )
    assert replay.data == changed.data
    plan.refresh_from_db()
    assert plan.revision == 3
    recovered = api.post(
        ROOT + f"plan_benefits/receipts/{changed_key}/",
        {"identity": str(benefit.id)},
        format="json",
    )
    assert recovered.data["receipt"] == changed.data
    assert (
        ContentEditAudit.objects.filter(
            kind="subscription_plans", object_id=str(plan.id)
        ).count()
        == 2
    )
    subscription.refresh_from_db()
    invoice.refresh_from_db()
    assert invoice.purchase_snapshot["benefits"][0]["limit"] == 5
    assert subscription.plan_snapshot["benefits"][0]["limit"] == 5
    assert decision(buyer, feature.code, "tenant")["limit"] == 5
    current = billing.body(
        buyer_api.get(billing.ROOT + "subscription-plans/", HTTP_ACCEPT_LANGUAGE="ar")
    )
    assert (
        next(row for row in current if row["id"] == str(plan.id))["benefits"][0][
            "limit"
        ]
        == 9
    )
    assert (
        save(api, "plan_benefits", {"limit": 1}, 1, str(benefit.id))[0].status_code
        == 409
    )
    disabled, _ = save(
        api, "plan_benefits", {"included": False, "limit": None}, 2, str(benefit.id)
    )
    assert disabled.status_code == 200 and disabled.data["values"]["limit"] is None
    assert decision(buyer, feature.code, "tenant")["allowed"] is True
    feature.refresh_from_db()
    assert not feature.enforced and not feature.free
    assert api.delete(ROOT + f"plan_benefits/{benefit.id}/").status_code == 405


@pytest.mark.parametrize(
    "failure",
    ["organization", "wrong_workspace", "inactive_plan", "unavailable_feature"],
)
def test_benefits_do_not_create_company_features_or_cross_workspace_access(
    catalog, failure
):
    plan, feature = catalog
    if failure == "organization":
        plan.audience = "organization"
    elif failure == "wrong_workspace":
        plan.workspace = "owner"
    elif failure == "inactive_plan":
        plan.active = False
    else:
        feature.available = False
        feature.save()
    plan.save()
    api = client(operator())
    result, _ = save(api, "plan_benefits", values(plan, feature))
    assert result.status_code == 400, result.data
    assert not PlanBenefit.objects.filter(plan=plan).exists()
    plan.refresh_from_db()
    assert plan.revision == 1


def test_feature_description_cannot_enable_or_price_a_feature(catalog):
    _, feature = catalog
    api = client(operator())
    schema = {row["kind"]: row for row in api.get(ROOT).data["catalogs"]}
    assert schema["commerce_features"]["allow_create"] is False
    assert next(
        row for row in schema["plan_benefits"]["fields"] if row["name"] == "limit"
    )["nullable"]
    changed, _ = save(
        api, "commerce_features", {"label_ar": "اسم محدث"}, 1, str(feature.id)
    )
    assert changed.status_code == 200 and changed.data["revision"] == 2
    assert (
        api.get(ROOT + "commerce_features/", {"search": "اسم محدث"}).data["count"] == 1
    )
    for field in ("enforced", "free", "available", "free_limit"):
        assert (
            save(api, "commerce_features", {field: True}, 2, str(feature.id))[
                0
            ].status_code
            == 400
        )
    assert (
        save(api, "commerce_features", {"code": "new-execution-feature"})[0].status_code
        == 400
    )
    assert (
        save(api, "commerce_features", {"workspace": "owner"}, 2, str(feature.id))[
            0
        ].status_code
        == 400
    )
    feature.refresh_from_db()
    assert (
        feature.label_ar == "اسم محدث"
        and feature.available
        and not feature.free
        and not feature.enforced
    )


@pytest.mark.django_db(transaction=True)
def test_purchase_and_benefit_edit_share_plan_lock_and_snapshot_revision(catalog):
    plan, feature = catalog
    benefit = PlanBenefit.objects.create(plan=plan, feature=feature, limit=5)
    actor = operator()
    buyer = get_user_model().objects.create_user(
        email="parallel-benefit-buyer@example.invalid", password="local"
    )

    def run(index):
        if index == 0:
            return save(
                client(actor), "plan_benefits", {"limit": 9}, 1, str(benefit.id)
            )[0]
        return billing.issue(client(buyer), plan)[0]

    edited, purchased = parallel_calls(run)
    assert edited.status_code == 200, edited.data
    assert purchased.status_code in (201, 409), purchased.data
    if purchased.status_code == 201:
        snapshot = RentInvoice.objects.get(
            id=billing.body(purchased, 201)["id"]
        ).purchase_snapshot
        assert snapshot["revision"] == 1 and snapshot["benefits"][0]["limit"] == 5
    else:
        assert not RentInvoice.objects.filter(payer=buyer).exists()
