import io
import uuid

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command, CommandError
from rest_framework.test import APIClient

from core_apps.features.models import (
    AccountSubscription,
    CommerceFeature,
    EntitlementGrant,
    PaymentAttempt,
    RentInvoice,
    StoreProduct,
    SubscriptionPlan,
)
from core_apps.features.tests.test_billing_subscriptions import body, pay, ROOT

pytestmark = pytest.mark.django_db


def seed():
    call_command("seed_commerce_test_catalog", stdout=io.StringIO())


def authenticated_client():
    user = get_user_model().objects.create_user(
        email="sample-catalog@example.test", password="test"
    )
    client = APIClient()
    client.force_authenticate(user)
    return client


def test_sample_catalog_is_localized_and_cannot_enable_store_sales():
    seed()
    assert SubscriptionPlan.objects.filter(name_en__startswith="[TEST]").count() == 8
    assert StoreProduct.objects.count() == 16
    assert not StoreProduct.objects.filter(active=True).exists()
    assert not StoreProduct.objects.filter(environment="live").exists()
    assert not RentInvoice.objects.exists() and not PaymentAttempt.objects.exists()
    assert (
        not AccountSubscription.objects.exists()
        and not EntitlementGrant.objects.exists()
    )
    client = authenticated_client()
    for language in ("en", "ar"):
        catalog = body(
            client.get(
                ROOT + "subscription-plans/?projection=mobile_v1&workspace=tenant",
                HTTP_ACCEPT_LANGUAGE=language,
            )
        )
        assert len(catalog["plans"]) == 2
        monthly = next(plan for plan in catalog["plans"] if plan["period_months"] == 1)
        assert monthly["amount_minor"] == 4900 and monthly["currency"] == "EGP"
        assert monthly["benefits"][0]["limit"] == 5
        assert monthly["benefits"][0]["unit_label"]
        assert all(
            not route["enabled"] for route in monthly["purchase_routes"].values()
        )
        assert ("[اختبار]" if language == "ar" else "[TEST]") in monthly["name"]
    owners = body(
        client.get(ROOT + "subscription-plans/?projection=mobile_v1&workspace=owner")
    )
    assert len(owners["plans"]) == 4
    assert {plan["tier"] for plan in owners["plans"]} == {"owner-pro", "owner-business"}


def test_repeat_seed_preserves_ids_revisions_rollout_and_unrelated_plans():
    unrelated = SubscriptionPlan.objects.create(
        name_en="Existing plan",
        name_ar="خطة حالية",
        workspace="tenant",
        amount_minor=12345,
    )
    feature = CommerceFeature.objects.get(code="priority_alerts")
    feature.available = False
    feature.enforced = True
    feature.free = True
    feature.save()
    seed()
    plans = dict(SubscriptionPlan.objects.values_list("id", "revision"))
    seed()
    assert dict(SubscriptionPlan.objects.values_list("id", "revision")) == plans
    unrelated.refresh_from_db()
    assert unrelated.amount_minor == 12345
    feature.refresh_from_db()
    assert not feature.available and feature.enforced and feature.free


@pytest.mark.parametrize(
    "runtime,qa,store",
    [
        ("production", True, False),
        ("staging", True, False),
        ("test", False, False),
        ("test", True, True),
    ],
)
def test_sample_prices_are_rejected_outside_isolated_qa(settings, runtime, qa, store):
    settings.RENTAL_RUNTIME_ENVIRONMENT = runtime
    settings.OWNER_TENANT_QA_ENABLED = qa
    settings.COMMERCE_STORE_PURCHASES_ENABLED = store
    with pytest.raises(CommandError):
        seed()
    assert not SubscriptionPlan.objects.filter(name_en__startswith="[TEST]").exists()
    assert not StoreProduct.objects.exists()


def test_sample_price_and_quota_flow_through_invoice_and_entitlement():
    seed()
    client = authenticated_client()
    plan = SubscriptionPlan.objects.get(tier="tenant-plus", period_months=1)
    invoice = body(
        client.post(
            ROOT + "billing/invoices/",
            {
                "purpose": "subscription",
                "workspace": "tenant",
                "plan_id": str(plan.id),
                "plan_revision": plan.revision,
                "request_key": str(uuid.uuid4()),
            },
            format="json",
        ),
        201,
    )
    assert invoice["total_minor"] == 4900 and invoice["balance_minor"] == 4900
    body(pay(client, invoice)[0])
    entitlement = body(
        client.get(
            ROOT + "billing/entitlements/?feature=priority_alerts&workspace=tenant"
        )
    )
    assert (
        entitlement["allowed"]
        and entitlement["source"] == "subscription"
        and entitlement["limit"] == 5
    )
    seed()
    assert RentInvoice.objects.get().amount_minor == 4900
    assert AccountSubscription.objects.count() == PaymentAttempt.objects.count() == 1
