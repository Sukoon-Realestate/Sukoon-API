"""Expiry is an atomic business transition, not a new collection or a backfill."""
# flake8: noqa: F811

from datetime import timedelta
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.apps import apps
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied

from core_apps.features.models import AccountSubscription, BoostCampaign, PaymentReceipt
from core_apps.features.planning_models import PlanningEvent
from core_apps.features.services.commerce_expiration import expire
from core_apps.features.services.commerce_expiration_notifications import authorize
from core_apps.features.services.planning_notifications import deliver_planning_events
from core_apps.features.tests import test_purchase_events as purchases
from core_apps.features.tests.test_promotion_visibility import home  # noqa: F401
from core_apps.notifications.models import Notification

pytestmark = pytest.mark.django_db
buyer, client, plan = purchases.buyer, purchases.client, purchases.plan
paymob, hosted = purchases.paymob, purchases.hosted
ROOT = purchases.ROOT


def ended_subscription(client, plan, scope="student"):
    invoice, _ = purchases.purchase(client, plan, scope)
    item = AccountSubscription.objects.get(invoice__id=invoice["id"])
    item.starts_at = timezone.now() - timedelta(days=31)
    item.ends_at = timezone.now() - timedelta(seconds=1)
    item.save(update_fields=["starts_at", "ends_at"])
    return item


def promotion(home, **values):
    now = timezone.now()
    return BoostCampaign.objects.create(
        owner=home.owner,
        property=home,
        option_id="local-expiry",
        duration_days=1,
        starts_at=now - timedelta(days=2),
        ends_at=now - timedelta(days=1),
        **values,
    )


@pytest.mark.parametrize("scope", ["individual", "student", "owner"])
def test_expiry_notice_retains_receipt_scope_and_does_not_collect(
    client, buyer, plan, hosted, scope
):
    item = ended_subscription(client, plan, scope)
    assert expire() == 1
    assert expire() == 0
    event = PlanningEvent.objects.get(
        destination__event_kind="commerce_service_expired"
    )
    assert event.destination["workspace"] == scope
    assert event.destination["invoice_id"] == str(item.invoice.id)
    deliver_planning_events()
    deliver_planning_events()
    assert (
        Notification.objects.filter(data__event_kind="commerce_service_expired").count()
        == 1
    )
    assert PaymentReceipt.objects.count() == 1
    current = purchases.body(
        client.get(ROOT + f"billing/invoices/{item.invoice.id}/?projection=mobile_v1")
    )
    assert (
        current["status"] == "paid" and current["service_state"]["status"] == "expired"
    )
    # A later purchase does not retarget the original notice or revive its service.
    later = purchases.body(
        purchases.billing.issue(
            client, plan, workspace="owner" if scope == "owner" else "tenant"
        )[0],
        201,
    )
    assert later["id"] != str(item.invoice.id)
    assert authorize(buyer, event.destination)
    assert event.destination["invoice_id"] == str(item.invoice.id)
    assert PaymentReceipt.objects.count() == 1


def test_expiration_and_event_rollback_together_and_retry_is_safe(home):  # noqa: F811
    item = promotion(home, status="active")
    with patch(
        "core_apps.features.services.commerce_expiration.record",
        side_effect=RuntimeError("outbox unavailable"),
    ):
        with pytest.raises(RuntimeError):
            expire()
    item.refresh_from_db()
    assert item.status == "active" and item.expiration_processed_at is None
    assert not PlanningEvent.objects.exists()
    assert expire() == 1 and expire() == 0
    item.refresh_from_db()
    assert item.status == "expired" and item.expiration_processed_at
    assert PlanningEvent.objects.count() == 1
    assert not PaymentReceipt.objects.exists()


def test_free_promotion_has_exact_private_detail_and_current_authority(
    home, api_client
):  # noqa: F811
    item = promotion(home, status="paused")
    expire()
    event = PlanningEvent.objects.get()
    assert event.destination["action_type"] == "open_promotion"
    assert event.destination["target_id"] == str(item.id)
    assert authorize(home.owner, event.destination)
    api_client.force_authenticate(home.owner)
    data = purchases.body(api_client.get(ROOT + f"boost-campaigns/{item.id}/"))
    assert data["id"] == str(item.id) and data["status"] == "expired"
    outsider = get_user_model().objects.create_user(
        email="expiry-outsider@example.test", password="test"
    )
    api_client.force_authenticate(outsider)
    assert api_client.get(ROOT + f"boost-campaigns/{item.id}/").status_code == 404
    with pytest.raises(NotFound):
        authorize(outsider, event.destination)
    with pytest.raises(NotFound):
        authorize(home.owner, {**event.destination, "workspace": "student"})


@pytest.mark.parametrize("state", ["pending", "cancelled", "failed", "completed"])
def test_non_active_promotion_has_no_expiry_side_effect(home, state):  # noqa: F811
    item = promotion(home, status=state)
    assert expire() == 0
    item.refresh_from_db()
    assert item.status == state and item.expiration_processed_at is None
    assert not PlanningEvent.objects.exists()


def test_migration_does_not_backfill_expired_history(home):  # noqa: F811
    old = promotion(home, status="active")
    current = promotion(home, status="active")
    current.ends_at = timezone.now() + timedelta(days=1)
    current.save(update_fields=["ends_at"])
    module = import_module(
        "core_apps.features.migrations.0091_commerce_expiration_processing"
    )
    module.observe_history(
        apps, SimpleNamespace(connection=SimpleNamespace(alias="default"))
    )
    old.refresh_from_db()
    current.refresh_from_db()
    assert old.expiration_processed_at and current.expiration_processed_at is None
    assert expire() == 1
    assert not PlanningEvent.objects.exists()


def test_store_lifecycle_is_not_expired_by_this_worker(client, plan, hosted):
    item = ended_subscription(client, plan)
    item.store_platform, item.store_status = "ios", "active"
    item.save(update_fields=["store_platform", "store_status"])
    assert expire() == 0
    item.refresh_from_db()
    assert item.expiration_processed_at is None and item.store_status == "active"


def test_expiry_worker_is_explicitly_scheduled(settings, monkeypatch):
    from config.background import configure

    monkeypatch.setenv("SOKOUN_GENERAL_BACKGROUND_ENABLED", "true")
    monkeypatch.setenv("SOKOUN_BACKGROUND_SCHEDULES", "expire-purchase-services")
    scope = {"CELERY_BEAT_SCHEDULE": settings.BACKGROUND_SCHEDULE_CATALOG}
    configure(scope)
    task = scope["CELERY_BEAT_SCHEDULE"]["expire-purchase-services"]
    assert task["task"] in scope["GENERAL_BACKGROUND_ALLOWED_TASKS"]


def test_company_expiry_requires_current_membership_even_before_push(
    client, buyer, plan, hosted
):
    from core_apps.features.models import Company, CompanyMembership

    item = ended_subscription(client, plan)
    company = Company.objects.create(
        name="Expiry", registration_number="expiry", contact_email="org@example.test"
    )
    reviewer = get_user_model().objects.create_user(
        email="expiry-reviewer@example.test", password="test"
    )
    member = CompanyMembership.objects.create(
        company=company, user=buyer, can_execute_payments=True
    )
    CompanyMembership.objects.create(company=company, user=reviewer, is_admin=True)
    item.invoice.organization = company
    item.invoice.purchase_snapshot["notification_workspace"] = "company"
    item.invoice.save()
    item.organization = company
    item.save(update_fields=["organization"])
    expire()
    events = PlanningEvent.objects.filter(
        destination__event_kind="commerce_service_expired"
    )
    assert set(events.values_list("recipient_id", flat=True)) == {buyer.pk, reviewer.pk}
    event = events.get(recipient=buyer)
    assert event.destination["workspace"] == "company"
    assert authorize(buyer, event.destination)
    member.is_active = False
    member.save()
    with pytest.raises(PermissionDenied):
        authorize(buyer, event.destination)
    deliver_planning_events()
    event.refresh_from_db()
    assert event.delivery_status == "stale_or_unauthorized"
    assert Notification.objects.filter(
        data__event_kind="commerce_service_expired", user=reviewer
    ).exists()
    assert not Notification.objects.filter(
        data__event_kind="commerce_service_expired", user=buyer
    ).exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("service_id", "not-an-id"),
        ("service_kind", "advertising"),
        ("expired_at", "2020-01-01"),
        ("invoice_id", "other"),
        ("company_id", "other"),
        ("workspace", "owner"),
    ],
)
def test_expiry_rejects_mismatched_source(client, buyer, plan, hosted, field, value):
    ended_subscription(client, plan)
    expire()
    event = PlanningEvent.objects.get(
        destination__event_kind="commerce_service_expired"
    )
    with pytest.raises(NotFound):
        authorize(buyer, {**event.destination, field: value})


@pytest.mark.django_db(transaction=True)
def test_two_workers_observe_expiry_once(home):  # noqa: F811
    from .test_cycle_concurrency import parallel_calls

    item = promotion(home, status="active")
    outcomes = parallel_calls(lambda _: expire())
    assert sorted(outcomes) == [0, 1]
    assert (
        PlanningEvent.objects.filter(destination__service_id=str(item.id)).count() == 1
    )


@pytest.mark.parametrize("paid", [False, True])
def test_advertisement_expiry_preserves_exact_service_and_legacy_receipt(
    home, paid
):  # noqa: F811
    from core_apps.advertising.models import Advertisement, AdvertisementOperation
    from core_apps.advertising.tasks import expire_advertisements
    from core_apps.features.models import BillingSourceLink, RentInvoice

    now = timezone.now()
    operation = AdvertisementOperation.objects.create(
        owner=home.owner, operation_id="expiry-ad", state="found"
    )
    ad = Advertisement.objects.create(
        owner=home.owner,
        operation=operation,
        title="Original",
        plan_snapshot={},
        status="active",
        starts_at=now - timedelta(days=2),
        ends_at=now - timedelta(days=1),
    )
    if paid:
        invoice = RentInvoice.objects.create(
            purpose="advertising",
            payer=home.owner,
            workspace="owner",
            status="paid",
            reference="EXPIRY-AD",
            business_reference="expiry-ad",
            due_date=now.date(),
            amount_minor=100,
            purchase_snapshot={"subject_id": str(ad.id)},
        )
        BillingSourceLink.objects.create(
            invoice=invoice, source_kind="advertising", source_id=ad.id
        )
    assert expire_advertisements() == 1 and expire_advertisements() == 0
    event = PlanningEvent.objects.get()
    assert event.destination["service_id"] == str(ad.id)
    assert event.destination["action_type"] == (
        "open_purchase_invoice" if paid else "open_banner_ad"
    )
    assert authorize(home.owner, event.destination)
    deliver_planning_events()
    assert Notification.objects.count() == 1
    ad.refresh_from_db()
    assert ad.status == "expired" and ad.expiration_processed_at
