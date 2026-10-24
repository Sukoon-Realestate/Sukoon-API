import hashlib
import uuid
from datetime import timedelta
from unittest.mock import patch
from dataclasses import replace
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from core_apps.features.models import (
    AccountSubscription,
    CommerceFeature,
    EntitlementGrant,
    PlanBenefit,
    StoreAccount,
    StoreProduct,
    StoreTransaction,
    PaymentAttempt,
    PaymentReceipt,
    LedgerTransaction,
    Company,
    CompanyMembership,
    SearchAlert,
    RentInvoice,
)
from core_apps.features.services.store_payments import VerifiedPurchase
from core_apps.features.tests.test_billing_subscriptions import (
    buyer,
    client,
    plan,
    body,
    issue,
    ROOT,
)

pytestmark = pytest.mark.django_db


class TestStoreAdapter:
    __test__ = False

    def verify(self, proof, *, product_id):
        account = StoreAccount.objects.get()
        now = timezone.now()
        return VerifiedPurchase(
            "store-tx-1",
            "store-tx-1",
            product_id,
            str(account.app_account_token),
            "sandbox",
            12500,
            "EGP",
            2,
            now,
            now + timedelta(days=30),
        )


@pytest.fixture
def store(settings, plan):
    settings.COMMERCE_STORE_PURCHASES_ENABLED = True
    settings.COMMERCE_STORE_ADAPTERS = {
        "android": "core_apps.features.tests.test_commerce_v1.TestStoreAdapter"
    }
    return StoreProduct.objects.create(
        plan=plan,
        platform="android",
        environment="sandbox",
        product_id="test.plus.monthly",
        amount_minor=12500,
        period_months=1,
        active=True,
    )


def store_checkout(client, plan):
    invoice = body(issue(client, plan)[0], 201)
    base = ROOT + f"billing/invoices/{invoice['id']}/"
    quote = body(
        client.post(
            base + "quote/?platform=android",
            {"expected_revision": 1, "request_key": str(uuid.uuid4())},
            format="json",
        ),
        201,
    )
    command = {
        "expected_revision": 1,
        "request_key": str(uuid.uuid4()),
        "quote_id": quote["id"],
    }
    attempt = body(client.post(base + "checkout/", command, format="json"))
    return invoice, quote, command, attempt


def proof_body():
    proof = "private-proof"
    return {
        "contract_version": 1,
        "platform": "android",
        "product_id": "test.plus.monthly",
        "verification_source": "google_play",
        "verification_data": proof,
        "proof_digest": hashlib.sha256(proof.encode()).hexdigest(),
    }


def test_catalog_context_and_disabled_provider_are_truthful(client, plan):
    catalog = body(client.get(ROOT + "subscriptions/current/?projection=mobile_v1"))
    assert catalog["contract_version"] == 1 and catalog["organization_id"] == ""
    assert catalog["subscription"] is None and not catalog["management"]["auto_renew"]
    assert not catalog["plans"][0]["purchase_routes"]["android"]["enabled"]
    context = body(client.get(ROOT + "billing/store/context/?platform=android"))
    assert not context["enabled"]
    assert (
        body(client.get(ROOT + "billing/store/context/?platform=android"))[
            "app_account_token"
        ]
        == context["app_account_token"]
    )
    response = client.post(ROOT + "billing/store/verify/", proof_body(), format="json")
    body(response, 503)
    assert response["X-App-Error-Code"] == "provider_unavailable"
    assert not StoreTransaction.objects.exists()


def test_store_intent_verifies_once_and_restore_works_with_sales_off(
    client, buyer, plan, store, settings
):
    invoice, quote, command, attempt = store_checkout(client, plan)
    assert quote["provider_mode"] == "play_billing"
    assert attempt["payment_status"] == "pending" and not attempt["receipt_id"]
    assert attempt["fulfillment_status"] == "pending" and not attempt["retry_allowed"]
    session = attempt["store_session"]
    assert (
        session["invoice_id"] == invoice["id"]
        and session["payment_attempt_id"] == attempt["id"]
    )
    assert (
        not AccountSubscription.objects.exists() and not PaymentReceipt.objects.exists()
    )
    replay = body(
        client.post(
            ROOT + f"billing/invoices/{invoice['id']}/checkout/", command, format="json"
        )
    )
    assert replay["id"] == attempt["id"]
    settings.COMMERCE_STORE_PURCHASES_ENABLED = False
    verified = body(
        client.post(ROOT + "billing/store/verify/", proof_body(), format="json")
    )
    assert (
        verified["account_id"] == str(buyer.id)
        and verified["recorded"]
        and verified["finish_transaction"]
    )
    assert (
        verified["attempt"]["payment_status"] == "captured"
        and verified["attempt"]["fulfillment_status"] == "fulfilled"
    )
    restored = body(
        client.post(ROOT + "billing/store/verify/", proof_body(), format="json")
    )
    assert restored["attempt"]["id"] == attempt["id"]
    assert (
        StoreTransaction.objects.count()
        == PaymentReceipt.objects.count()
        == AccountSubscription.objects.count()
        == PaymentAttempt.objects.count()
        == 1
    )
    assert LedgerTransaction.objects.filter(kind="store_purchase_capture").count() == 1
    fresh = body(client.get(ROOT + "subscriptions/current/?projection=mobile_v1"))
    assert (
        fresh["management"]["platform"] == "android"
        and fresh["management"]["auto_renew"]
    )


def test_unresolved_store_attempt_blocks_cancel_and_different_key(client, plan, store):
    invoice, quote, command, attempt = store_checkout(client, plan)
    base = ROOT + f"billing/invoices/{invoice['id']}/"
    for endpoint, value in [
        ("checkout/", {**command, "request_key": str(uuid.uuid4())}),
        ("cancel/", {"expected_revision": 1, "request_key": str(uuid.uuid4())}),
    ]:
        response = client.post(base + endpoint, value, format="json")
        body(response, 409)
        assert response["X-App-Error-Code"] == "payment_in_progress"
    assert PaymentAttempt.objects.count() == 1


@pytest.mark.parametrize(
    "alteration,code",
    [
        ("account", "store_account_mismatch"),
        ("price", "store_price_mismatch"),
        ("pending", "outcome_unknown"),
        ("time", "outcome_unknown"),
    ],
)
def test_verified_provider_mismatch_never_records_money(
    client, plan, store, alteration, code
):
    store_checkout(client, plan)
    verified = TestStoreAdapter().verify("proof", product_id=store.product_id)
    values = {
        "account": {"app_account_token": str(uuid.uuid4())},
        "price": {"amount_minor": 1},
        "pending": {"state": "pending"},
        "time": {"purchased_at": timezone.now() - timedelta(days=1)},
    }
    with patch.object(
        TestStoreAdapter, "verify", return_value=replace(verified, **values[alteration])
    ):
        response = client.post(
            ROOT + "billing/store/verify/", proof_body(), format="json"
        )
    body(response, 409)
    assert response["X-App-Error-Code"] == code
    assert not StoreTransaction.objects.exists() and not PaymentReceipt.objects.exists()
    assert PaymentAttempt.objects.get().payment_status == "pending"


def test_digest_and_cross_account_replay_are_rejected(client, plan, store):
    store_checkout(client, plan)
    body(
        client.post(
            ROOT + "billing/store/verify/",
            {**proof_body(), "proof_digest": "0" * 64},
            format="json",
        ),
        400,
    )
    body(client.post(ROOT + "billing/store/verify/", proof_body(), format="json"))
    other = get_user_model().objects.create_user(
        email="other-commerce@example.test", password="test"
    )
    client.force_authenticate(other)
    response = client.post(ROOT + "billing/store/verify/", proof_body(), format="json")
    body(response, 409)
    assert response["X-App-Error-Code"] == "store_account_mismatch"
    assert StoreTransaction.objects.count() == 1


def test_catalog_price_mismatch_disables_route(client, plan, store):
    store.amount_minor = 1
    store.save()
    route = body(client.get(ROOT + "subscription-plans/?projection=mobile_v1"))[
        "plans"
    ][0]["purchase_routes"]["android"]
    assert not route["enabled"] and route["reason"] == "store_price_mismatch"


def test_entitlement_grant_is_current_and_read_does_not_consume(client, buyer):
    feature = CommerceFeature.objects.get(code="priority_alerts")
    grant = EntitlementGrant.objects.create(
        user=buyer,
        feature=feature,
        source="grandfathered",
        limit=1,
        starts_at=timezone.now() - timedelta(days=1),
        policy_reference="test",
    )
    path = ROOT + "billing/entitlements/?feature=priority_alerts&workspace=tenant"
    first, second = body(client.get(path)), body(client.get(path))
    assert (
        first["allowed"] and second["allowed"] and first["used"] == second["used"] == 0
    )
    assert first["source"] == "grandfathered" and first["account_id"] == str(buyer.id)
    assert client.get(path)["Cache-Control"] == "private, no-store"
    SearchAlert.objects.create(user=buyer, name="instant", cadence="instant")
    assert not body(client.get(path))["allowed"]
    grant.revoked_at = timezone.now()
    grant.save()
    assert body(client.get(path))["source"] == ""


def test_cancel_auto_renew_preserves_paid_access_and_snapshotted_benefits(
    client, buyer, plan, store
):
    feature = CommerceFeature.objects.get(code="priority_alerts")
    benefit = PlanBenefit.objects.create(plan=plan, feature=feature, limit=3)
    store_checkout(client, plan)
    body(client.post(ROOT + "billing/store/verify/", proof_body(), format="json"))
    subscription = AccountSubscription.objects.get()
    subscription.auto_renew = False
    subscription.cancelled_at = timezone.now()
    subscription.save()
    benefit.delete()
    value = body(client.get(ROOT + "billing/entitlements/?feature=priority_alerts"))
    assert (
        value["allowed"] and value["source"] == "subscription" and value["limit"] == 3
    )
    subscription.store_status = "revoked"
    subscription.save()
    assert not body(client.get(ROOT + "billing/entitlements/?feature=priority_alerts"))[
        "allowed"
    ]


def test_enforced_quota_keeps_daily_alerts_and_existing_history(
    client, buyer, settings
):
    settings.COMMERCE_ENTITLEMENTS_ENABLED = True
    feature = CommerceFeature.objects.get(code="priority_alerts")
    feature.enforced = True
    feature.save()
    EntitlementGrant.objects.create(
        user=buyer,
        feature=feature,
        source="grandfathered",
        limit=1,
        starts_at=timezone.now(),
        policy_reference="test",
    )

    def create(cadence):
        return client.post(
            ROOT + "search-alerts/",
            {
                "name": "test",
                "cadence": cadence,
                "filters": {},
                "request_key": str(uuid.uuid4()),
            },
            format="json",
        )

    body(create("instant"), 201)
    response = create("instant")
    body(response, 409)
    assert response["X-App-Error-Code"] == "quota_exceeded"
    body(create("daily"), 201)
    assert client.get(ROOT + "search-alerts/").status_code == 200


def test_company_catalog_scope_and_revoked_membership(client, buyer, plan):
    company = Company.objects.create(
        name="test", registration_number="test", contact_email="company@example.test"
    )
    member = CompanyMembership.objects.create(
        company=company, user=buyer, is_admin=True
    )
    plan.audience = "organization"
    plan.save()
    assert (
        body(client.get(ROOT + "subscription-plans/?projection=mobile_v1"))["plans"]
        == []
    )
    scoped = body(
        client.get(ROOT + f"subscriptions/current/?organization_id={company.id}")
    )
    assert scoped["contract_version"] == 1 and scoped["organization_id"] == str(
        company.id
    )
    assert len(scoped["plans"]) == 1
    command = {
        "request_key": str(uuid.uuid4()),
        "purpose": "subscription",
        "workspace": "tenant",
        "organization_id": str(company.id),
        "plan_id": str(plan.id),
        "plan_revision": 1,
    }
    body(client.post(ROOT + "billing/invoices/", command, format="json"), 403)
    assert not RentInvoice.objects.exists()
    member.is_active = False
    member.save()
    response = client.get(ROOT + f"subscriptions/current/?organization_id={company.id}")
    body(response, 403)
    assert response["X-App-Error-Code"] == "organization_permission_revoked"


def test_absent_issue_operation_is_not_permission_to_retry(client):
    assert body(client.get(ROOT + f"billing/invoice-operations/{uuid.uuid4()}/")) == {
        "invoice": None,
        "absence_confirmed": False,
    }


def test_store_notifications_fail_closed_without_authentication_adapter(client):
    body(
        client.post(
            ROOT + "billing/store/notifications/android/",
            {"status": "paid"},
            format="json",
        ),
        503,
    )
    assert not StoreTransaction.objects.exists()


def test_verified_notifications_are_idempotent_and_ordered(client, plan, store):
    from core_apps.features.services.store_notifications import VerifiedStoreEvent
    from core_apps.features.models import StoreNotification

    store_checkout(client, plan)
    purchase = TestStoreAdapter().verify("proof", product_id=store.product_id)
    body(client.post(ROOT + "billing/store/verify/", proof_body(), format="json"))
    now = timezone.now()
    event = VerifiedStoreEvent(
        "evt-1", replace(purchase, auto_renew=False), now, "revoked"
    )
    with patch.object(
        TestStoreAdapter, "verify_notification", create=True, return_value=event
    ):
        for _ in range(2):
            assert body(
                client.post(
                    ROOT + "billing/store/notifications/android/",
                    {"signed": "test"},
                    format="json",
                )
            )["recorded"]
    assert StoreNotification.objects.count() == 1
    assert AccountSubscription.objects.get().store_status == "revoked"
    late = replace(
        event,
        event_id="evt-late",
        observed_at=now - timedelta(hours=1),
        status="active",
    )
    with patch.object(
        TestStoreAdapter, "verify_notification", create=True, return_value=late
    ):
        body(
            client.post(
                ROOT + "billing/store/notifications/android/",
                {"signed": "late"},
                format="json",
            )
        )
    assert AccountSubscription.objects.get().store_status == "revoked"


def test_renewal_records_invoice_receipt_without_new_mobile_checkout(
    client, plan, store
):
    from core_apps.features.services.store_notifications import VerifiedStoreEvent

    store_checkout(client, plan)
    body(client.post(ROOT + "billing/store/verify/", proof_body(), format="json"))
    previous = AccountSubscription.objects.get()
    previous.starts_at = timezone.now() - timedelta(days=30)
    previous.ends_at = timezone.now() - timedelta(seconds=1)
    previous.save()
    purchase = replace(
        TestStoreAdapter().verify("proof", product_id=store.product_id),
        transaction_id="store-renewal-2",
    )
    event = VerifiedStoreEvent("renew-1", purchase, timezone.now(), "active")
    with patch.object(
        TestStoreAdapter, "verify_notification", create=True, return_value=event
    ):
        for _ in range(2):
            body(
                client.post(
                    ROOT + "billing/store/notifications/android/",
                    {"signed": "renew"},
                    format="json",
                )
            )
    assert (
        StoreTransaction.objects.count()
        == PaymentReceipt.objects.count()
        == AccountSubscription.objects.count()
        == RentInvoice.objects.count()
        == 2
    )
    latest = body(client.get(ROOT + "subscriptions/current/?projection=mobile_v1"))[
        "subscription"
    ]
    assert latest["invoice_id"] != str(previous.invoice.id)


from core_apps.features.tests.test_rental_phase5 import phase5_lease, client_for


def test_maintenance_approval_issues_one_versioned_invoice_and_blocks_stale_cost(
    phase5_lease,
):
    from core_apps.features.models import MaintenanceRequest, BillingSourceLink

    owner, tenant, lease = phase5_lease
    item = MaintenanceRequest.objects.create(
        lease=lease,
        reporter=tenant,
        title="Repair",
        description="Repair",
        category="plumbing",
        priority="normal",
        status="appointment_proposed",
        proposed_cost_minor=2500,
        cost_payer="tenant",
        cost_version=1,
    )
    tenant_client = client_for(tenant)
    path = ROOT + f"maintenance-requests/{item.id}/actions/"
    command = {
        "action": "approve_cost",
        "expected_revision": 1,
        "cost_version": 1,
        "request_key": str(uuid.uuid4()),
    }
    approved = body(tenant_client.post(path, command, format="json"))["resource"]
    link = approved["billing_invoices"][0]
    assert link["family"] == "billing"
    assert (
        body(tenant_client.post(path, command, format="json"))["resource"][
            "billing_invoices"
        ]
        == approved["billing_invoices"]
    )
    assert BillingSourceLink.objects.filter(source_id=item.id).count() == 1
    invoice = body(tenant_client.get(ROOT + f"billing/invoices/{link['id']}/"))
    assert invoice["purpose"] == "maintenance" and invoice["total_minor"] == 2500
    proposal = {
        "action": "propose_cost",
        "expected_revision": 2,
        "cost": {"amount_minor": 5000},
        "cost_payer": "tenant",
        "request_key": str(uuid.uuid4()),
    }
    body(client_for(owner).post(path, proposal, format="json"))
    assert (
        body(tenant_client.get(ROOT + f"billing/invoices/{link['id']}/"))["status"]
        == "cancelled"
    )
    assert not PaymentAttempt.objects.filter(invoice__id=link["id"]).exists()


def test_paid_promotion_uses_invoice_and_activation_time_but_free_option_stays_free(
    phase5_lease,
):
    from core_apps.features.catalog_models import PromotionOption
    from core_apps.features.models import BoostCampaign
    from core_apps.features.tests.test_billing_subscriptions import pay

    owner, tenant, lease = phase5_lease
    client = client_for(owner)
    option = PromotionOption.objects.create(
        id="commerce-paid",
        title_en="Paid",
        title_ar="مدفوع",
        duration_days=7,
        amount_minor=15000,
    )
    response = body(
        client.post(
            ROOT + "boost-campaigns/",
            {
                "property_id": str(lease.property.id),
                "option_id": option.id,
                "request_key": str(uuid.uuid4()),
            },
            format="json",
        ),
        201,
    )
    assert response["status"] == "pending" and len(response["billing_invoices"]) == 1
    invoice = body(
        client.get(ROOT + f"billing/invoices/{response['billing_invoices'][0]['id']}/")
    )
    before = timezone.now()
    paid = body(pay(client, invoice)[0])
    assert (
        paid["payment_status"] == "captured"
        and paid["fulfillment_status"] == "fulfilled"
    )
    campaign = BoostCampaign.objects.get(id=response["id"])
    assert (
        campaign.starts_at >= before
        and campaign.ends_at - campaign.starts_at == timedelta(days=7)
    )
    campaign.status = "completed"
    campaign.save()
    option.amount_minor = 0
    option.save()
    free = body(
        client.post(
            ROOT + "boost-campaigns/",
            {
                "property_id": str(lease.property.id),
                "option_id": option.id,
                "request_key": str(uuid.uuid4()),
            },
            format="json",
        ),
        201,
    )
    assert free["status"] == "active" and free["billing_invoices"] == []


@pytest.mark.django_db(transaction=True)
def test_two_devices_share_one_pending_intent_and_one_verified_capture(
    client, buyer, plan, store
):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from django.db import connection, close_old_connections

    if connection.vendor != "postgresql":
        pytest.skip("Row-lock contention requires PostgreSQL.")
    invoice = body(issue(client, plan)[0], 201)
    base = ROOT + f"billing/invoices/{invoice['id']}/"
    quote = body(
        client.post(
            base + "quote/?platform=android",
            {"expected_revision": 1, "request_key": str(uuid.uuid4())},
            format="json",
        ),
        201,
    )
    barrier = Barrier(2)

    def checkout(_):
        close_old_connections()
        try:
            local = client_for(get_user_model().objects.get(pk=buyer.pk))
            barrier.wait(timeout=10)
            response = local.post(
                base + "checkout/",
                {
                    "expected_revision": 1,
                    "quote_id": quote["id"],
                    "request_key": str(uuid.uuid4()),
                },
                format="json",
            )
            return response.status_code
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(checkout, range(2))) == [200, 409]
    assert PaymentAttempt.objects.count() == 1
    barrier = Barrier(2)

    def verify(_):
        close_old_connections()
        try:
            local = client_for(get_user_model().objects.get(pk=buyer.pk))
            barrier.wait(timeout=10)
            response = local.post(
                ROOT + "billing/store/verify/", proof_body(), format="json"
            )
            return response.status_code, response.json()["data"]
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(verify, range(2)))
    assert [code for code, data in results] == [200, 200]
    assert results[0][1]["attempt"]["id"] == results[1][1]["attempt"]["id"]
    assert (
        StoreTransaction.objects.count()
        == PaymentReceipt.objects.count()
        == AccountSubscription.objects.count()
        == 1
    )


@pytest.mark.django_db(transaction=True)
def test_two_devices_cannot_exceed_alert_quota(buyer, settings):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from django.db import connection, close_old_connections

    if connection.vendor != "postgresql":
        pytest.skip("Row-lock contention requires PostgreSQL.")
    settings.COMMERCE_ENTITLEMENTS_ENABLED = True
    feature, _ = CommerceFeature.objects.update_or_create(
        code="priority_alerts",
        defaults={"workspace": "tenant", "available": True, "enforced": True},
    )
    EntitlementGrant.objects.create(
        user=buyer,
        feature=feature,
        source="grandfathered",
        limit=1,
        starts_at=timezone.now(),
        policy_reference="test",
    )
    barrier = Barrier(2)

    def create(_):
        close_old_connections()
        try:
            local = client_for(get_user_model().objects.get(pk=buyer.pk))
            barrier.wait(timeout=10)
            return local.post(
                ROOT + "search-alerts/",
                {
                    "name": "test",
                    "cadence": "instant",
                    "filters": {},
                    "request_key": str(uuid.uuid4()),
                },
                format="json",
            ).status_code
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(create, range(2))) == [201, 409]
    assert SearchAlert.objects.filter(user=buyer).count() == 1


def test_verified_but_unfulfilled_purchase_has_durable_review_and_can_recover(
    client, plan, store
):
    from core_apps.features.models import StorePurchaseReview

    store_checkout(client, plan)
    with patch(
        "core_apps.features.services.billing_settlement.PaymentReceipt.objects.create",
        side_effect=RuntimeError("private provider detail"),
    ):
        response = client.post(
            ROOT + "billing/store/verify/", proof_body(), format="json"
        )
    body(response, 503)
    assert b"private provider detail" not in response.content
    review = StorePurchaseReview.objects.get()
    assert review.reason_code == "fulfillment_pending" and review.resolved_at is None
    assert not StoreTransaction.objects.exists() and not PaymentReceipt.objects.exists()
    body(client.post(ROOT + "billing/store/verify/", proof_body(), format="json"))
    review.refresh_from_db()
    assert review.resolved_at and PaymentReceipt.objects.count() == 1


def test_verified_grace_period_grants_access_without_rewriting_paid_period(
    client, buyer, plan, store
):
    from core_apps.features.services.store_notifications import VerifiedStoreEvent

    PlanBenefit.objects.create(
        plan=plan, feature=CommerceFeature.objects.get(code="priority_alerts"), limit=3
    )
    store_checkout(client, plan)
    body(client.post(ROOT + "billing/store/verify/", proof_body(), format="json"))
    subscription = AccountSubscription.objects.get()
    subscription.starts_at = timezone.now() - timedelta(days=31)
    subscription.ends_at = timezone.now() - timedelta(days=1)
    subscription.save()
    paid_end = subscription.ends_at
    grace_end = timezone.now() + timedelta(days=2)
    event = VerifiedStoreEvent(
        "grace-event",
        TestStoreAdapter().verify("proof", product_id=store.product_id),
        timezone.now(),
        "grace",
        grace_ends_at=grace_end,
    )
    with patch.object(
        TestStoreAdapter, "verify_notification", create=True, return_value=event
    ):
        body(
            client.post(
                ROOT + "billing/store/notifications/android/",
                {"signed": "grace"},
                format="json",
            )
        )
    entitlement = body(
        client.get(ROOT + "billing/entitlements/?feature=priority_alerts")
    )
    assert entitlement["allowed"] and entitlement["source"] == "subscription"
    subscription.refresh_from_db()
    assert subscription.ends_at == paid_end and subscription.grace_ends_at == grace_end
    assert (
        body(client.get(ROOT + "subscriptions/current/?projection=mobile_v1"))[
            "subscription"
        ]["status"]
        == "grace"
    )


def test_company_subscription_remains_owned_by_company_when_employee_changes(
    client, buyer, plan
):
    from core_apps.features.services.billing_catalog import plan_snapshot

    company = Company.objects.create(
        name="org", registration_number="org", contact_email="org@example.test"
    )
    original = CompanyMembership.objects.create(
        company=company, user=buyer, is_admin=True
    )
    invoice = RentInvoice.objects.create(
        purpose="subscription",
        payer=buyer,
        organization=company,
        workspace="tenant",
        business_reference="test-company-plan",
        reference="INV-COMPANY-TEST",
        due_date=timezone.localdate(),
        amount_minor=12500,
        status="paid",
    )
    subscription = AccountSubscription.objects.create(
        user=buyer,
        plan=plan,
        invoice=invoice,
        organization=company,
        workspace="tenant",
        starts_at=timezone.now(),
        ends_at=timezone.now() + timedelta(days=30),
        plan_snapshot=plan_snapshot(plan),
    )
    other = get_user_model().objects.create_user(
        email="new-company-admin@example.test", password="test"
    )
    CompanyMembership.objects.create(company=company, user=other, is_admin=True)
    original.is_active = False
    original.save()
    client.force_authenticate(other)
    scoped = body(
        client.get(ROOT + f"subscriptions/current/?organization_id={company.id}")
    )
    assert scoped["subscription"]["id"] == str(subscription.id)
    assert scoped["subscription"]["organization_id"] == str(company.id)
    assert (
        body(client.get(ROOT + "subscriptions/current/?projection=mobile_v1"))[
            "subscription"
        ]
        is None
    )
    assert body(
        client.get(
            ROOT + f"billing/invoices/{invoice.id}/?organization_id={company.id}"
        )
    )["organization_id"] == str(company.id)


def test_maintenance_cost_cannot_be_billed_again_in_settlement(phase5_lease):
    from django.db import transaction
    from core_apps.features.models import MaintenanceRequest
    from core_apps.features.services.billing_sources import maintenance_invoice
    from core_apps.features.services.settlements import (
        prepare_settlement,
        financial_snapshot,
    )
    from core_apps.features.services.rental_phase2 import RentalConflict

    owner, tenant, lease = phase5_lease
    lease.status, lease.occupancy_status = "ended", "returned"
    lease.save()
    item = MaintenanceRequest.objects.create(
        lease=lease,
        reporter=tenant,
        title="Repair",
        description="Repair",
        category="plumbing",
        priority="normal",
        proposed_cost_minor=2500,
        cost_payer="tenant",
        cost_version=1,
        approved_cost_version=1,
    )
    with transaction.atomic():
        invoice = maintenance_invoice(item, tenant)
    with pytest.raises(RentalConflict) as conflict:
        prepare_settlement(
            lease,
            [
                {
                    "id": str(uuid.uuid4()),
                    "type": "maintenance",
                    "amount": {"amount_minor": 2500, "currency": "EGP", "exponent": 2},
                    "maintenance_request_id": str(item.id),
                    "cost_version": 1,
                }
            ],
        )
    assert conflict.value.get_codes() == "invoice_exists"
    assert financial_snapshot(lease)["source_billing_invoices"] == [
        {"id": str(invoice.id), "revision": invoice.revision}
    ]


def test_restore_of_revoked_transaction_updates_access_without_erasing_receipt(
    client, plan, store
):
    store_checkout(client, plan)
    body(client.post(ROOT + "billing/store/verify/", proof_body(), format="json"))
    purchase = replace(
        TestStoreAdapter().verify("proof", product_id=store.product_id), state="revoked"
    )
    with patch.object(TestStoreAdapter, "verify", return_value=purchase):
        restored = body(
            client.post(ROOT + "billing/store/verify/", proof_body(), format="json")
        )
    assert restored["recorded"] and restored["finish_transaction"]
    assert AccountSubscription.objects.get().store_status == "revoked"
    assert PaymentReceipt.objects.count() == StoreTransaction.objects.count() == 1
