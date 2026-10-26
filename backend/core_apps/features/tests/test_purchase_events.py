"""Purchase receipts survive retries, scope changes and service expiration."""

import uuid
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.exceptions import NotFound
from core_apps.features.models import (
    AccountSubscription,
    Company,
    CompanyMembership,
    PaymentReceipt,
)
from core_apps.features.planning_models import PlanningEvent
from core_apps.features.services.billing_notifications import (
    authorize,
    record_fulfilled,
)
from core_apps.features.services.planning_notifications import deliver_planning_events
from core_apps.features.tests import test_billing_subscriptions as billing
from core_apps.features.tests import test_hosted_checkout_all_products as checkout_tests
from core_apps.notifications.models import DeviceToken, Notification, PushDelivery
from core_apps.notifications.services.push_delivery import dispatch

pytestmark = pytest.mark.django_db
buyer, client, plan = billing.buyer, billing.client, billing.plan
body, ROOT = billing.body, billing.ROOT
paymob, hosted = checkout_tests.paymob, checkout_tests.hosted
pay_invoice = checkout_tests.pay_invoice
SEND = "core_apps.notifications.services.fcm_service.FCMService.send_push_to_device"


def purchase(client, plan, scope="individual"):
    request = {
        "purpose": "subscription",
        "workspace": "owner" if scope == "owner" else "tenant",
        "notification_workspace": scope,
        "plan_id": str(plan.id),
        "plan_revision": plan.revision,
        "request_key": str(uuid.uuid4()),
    }
    invoice = body(client.post(ROOT + "billing/invoices/", request, format="json"), 201)
    return invoice, pay_invoice(client, invoice)


@pytest.mark.parametrize("scope", ["individual", "student", "owner"])
def test_capture_bridge_and_device_retry_keep_one_purchase(
    client, buyer, plan, hosted, scope
):
    DeviceToken.objects.create(
        user=buyer, token="purchase-device", device_type="android"
    )
    invoice, payment = purchase(client, plan, scope)
    event = PlanningEvent.objects.get(destination__event_kind="purchase_fulfilled")
    assert event.destination["invoice_id"] == invoice["id"]
    assert event.destination["workspace"] == scope
    with patch(
        "core_apps.notifications.services.fcm_service.FCMService.send_push_to_user"
    ) as direct:
        deliver_planning_events()
        deliver_planning_events()
        direct.assert_not_called()
    notification = Notification.objects.get()
    assert notification.scope == scope and PushDelivery.objects.count() == 1
    with patch(SEND, side_effect=[False, True]) as send:
        assert dispatch() == 0
        PushDelivery.objects.update(
            next_attempt_at=timezone.now() - timedelta(seconds=1)
        )
        assert dispatch() == 1
        assert dispatch() == 0
        assert {call.kwargs["data"]["invoice_id"] for call in send.call_args_list} == {
            invoice["id"]
        }
    assert PaymentReceipt.objects.count() == AccountSubscription.objects.count() == 1


def test_old_event_reads_expired_service_and_retains_paid_receipt(
    client, buyer, plan, hosted
):
    invoice, payment = purchase(client, plan, "student")
    event = PlanningEvent.objects.get()
    AccountSubscription.objects.update(
        starts_at=timezone.now() - timedelta(days=31),
        ends_at=timezone.now() - timedelta(seconds=1),
    )
    assert authorize(buyer, event.destination)
    current = body(
        client.get(ROOT + f"billing/invoices/{invoice['id']}/?projection=mobile_v1")
    )
    assert current["status"] == "paid" and current["receipt_id"]
    assert current["service_state"]["status"] == "expired"
    assert current["presentation_workspace"] == "student"
    assert current["allowed_actions"] == []


def test_activation_case_keeps_its_own_recovery_notice(client, plan, hosted):
    from core_apps.features.tests import test_fulfillment_cases as cases
    from core_apps.features.services.payment_fulfillment import deliver

    job = cases.fail_activation(checkout_tests.checkout(client, plan))
    assert job.case_id
    deliver(job.pk)
    deliver(job.pk)
    assert not PlanningEvent.objects.filter(
        destination__event_kind="purchase_fulfilled"
    ).exists()
    assert PlanningEvent.objects.filter(
        destination__event_kind="service_activation_update"
    ).exists()
    assert PaymentReceipt.objects.count() == AccountSubscription.objects.count() == 1


@pytest.mark.parametrize(
    "invalid",
    [
        {"workspace": "owner", "notification_workspace": "student"},
        {"workspace": "tenant", "notification_workspace": "owner"},
        {"workspace": "tenant", "notification_workspace": "company"},
    ],
)
def test_invoice_scope_cannot_be_forged(client, plan, invalid):
    response = client.post(
        ROOT + "billing/invoices/",
        {
            "purpose": "subscription",
            "plan_id": str(plan.id),
            "plan_revision": plan.revision,
            "request_key": str(uuid.uuid4()),
            **invalid,
        },
        format="json",
    )
    assert response.status_code == 400
    assert not PlanningEvent.objects.exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("workspace", "owner"),
        ("invoice_id", str(uuid.uuid4())),
        ("payment_attempt_id", str(uuid.uuid4())),
        ("payment_attempt_id", "bad"),
        ("company_id", str(uuid.uuid4())),
    ],
)
def test_event_identity_is_exact(client, buyer, plan, hosted, field, value):
    purchase(client, plan)
    event = PlanningEvent.objects.get()
    event.destination[field] = value
    with pytest.raises(NotFound):
        authorize(buyer, event.destination)
    event.save()
    deliver_planning_events()
    event.refresh_from_db()
    assert event.delivery_status == "stale_or_unauthorized"
    assert not Notification.objects.exists()


@pytest.mark.parametrize("when", ["before_queue", "after_failed_push"])
def test_company_recipients_and_retries_require_current_read_authority(
    client, buyer, plan, hosted, when
):
    _, payment = purchase(client, plan)
    payment.attempt.refresh_from_db()
    # Reuse a locally captured invoice to isolate recipient authorization from
    # company payment-mandate tests, covered by hosted_checkout_all_products.
    PlanningEvent.objects.all().delete()
    company = Company.objects.create(
        name="Local", registration_number="local", contact_email="org@example.test"
    )
    reviewer = get_user_model().objects.create_user(
        email="reviewer@example.test", password="local"
    )
    outsider = get_user_model().objects.create_user(
        email="outsider@example.test", password="local"
    )
    member = CompanyMembership.objects.create(
        company=company, user=buyer, can_execute_payments=True
    )
    CompanyMembership.objects.create(company=company, user=reviewer, is_admin=True)
    CompanyMembership.objects.create(company=company, user=outsider)
    invoice = payment.attempt.invoice
    invoice.organization = company
    invoice.purchase_snapshot["notification_workspace"] = "company"
    invoice.save()
    record_fulfilled(invoice, payment.attempt)
    record_fulfilled(invoice, payment.attempt)
    assert set(PlanningEvent.objects.values_list("recipient_id", flat=True)) == {
        buyer.pk,
        reviewer.pk,
    }
    DeviceToken.objects.create(
        user=buyer, token="company-device", device_type="android"
    )
    if when == "after_failed_push":
        deliver_planning_events()
        with patch(SEND, return_value=False):
            assert dispatch() == 0
    member.is_active = False
    member.save()
    with patch(SEND) as send:
        deliver_planning_events()
        PushDelivery.objects.update(
            next_attempt_at=timezone.now() - timedelta(seconds=1)
        )
        assert dispatch() == 0
        send.assert_not_called()
    if when == "before_queue":
        assert not Notification.objects.filter(user=buyer).exists()
    else:
        assert PushDelivery.objects.get().suppressed
    assert PaymentReceipt.objects.count() == 1
