"""Confirmed capture survives activation failure; follow-up never repeats money."""

import uuid
from unittest.mock import patch
import pytest
from django.contrib.auth import get_user_model
from django.db import connections
from concurrent.futures import ThreadPoolExecutor
from core_apps.features.models import (
    PaymentFulfillment,
    PaymentReceipt,
    InvoicePaymentAllocation,
    RentalOperationalCase,
    AccountSubscription,
)
from core_apps.features.planning_models import PlanningEvent
from core_apps.features.services.paymob_payments import reconcile
from core_apps.features.services.payment_fulfillment import deliver
from core_apps.features.services.fulfillment_cases import blocker
from core_apps.features.services.rental_lifecycle.cases import (
    case_payload,
    case_queryset,
)
from core_apps.features.services.billing_projection import (
    invoice_payload,
    purchase_attempt_payload,
)
from core_apps.features.tests.test_hosted_checkout_all_products import (
    buyer,
    client,
    plan,
    hosted,
    paymob,
    checkout,
    snapshot,
)
from core_apps.features.tests.test_company_housing import (
    company_setup,
    rental_participants,
    policy,
)

pytestmark = pytest.mark.django_db
ROOT = "/api/v1/features/v1/"


def fail_activation(payment):
    with patch(
        "core_apps.features.services.paymob_client.inquiry",
        return_value=snapshot(payment),
    ), patch(
        "core_apps.features.services.billing_settlement.fulfill_purchase",
        side_effect=RuntimeError("private failure detail"),
    ):
        reconcile(payment)
    return PaymentFulfillment.objects.get(attempt=payment.attempt)


def test_activation_failure_keeps_receipt_and_one_visible_case(
    client, buyer, plan, hosted
):
    job = fail_activation(checkout(client, plan))
    for _ in range(2):
        with patch(
            "core_apps.features.services.billing_settlement.fulfill_purchase",
            side_effect=RuntimeError("temporary error"),
        ):
            deliver(job.pk)
    job.refresh_from_db()
    assert job.case_id and RentalOperationalCase.objects.count() == 1
    assert (
        PaymentReceipt.objects.count() == InvoicePaymentAllocation.objects.count() == 1
    )
    assert not AccountSubscription.objects.exists()
    case = job.case
    assert case.team == "support" and case.payment_attempt_id == job.attempt_id
    response = client.get(ROOT + f"rental-cases/{case.id}/")
    assert response.status_code == 200, response.data
    assert response.data["service_activation"]["invoice_id"] == str(job.invoice.id)
    assert b"private failure detail" not in response.content
    assert "link_remedy" not in response.data["allowed_actions"]
    assert blocker(case)
    events = PlanningEvent.objects.filter(destination__case_id=str(case.id))
    assert events.count() == 1 and events.get().destination["workspace"] == "individual"
    assert purchase_attempt_payload(job.attempt)["activation_case_id"] == str(case.id)
    invoice = client.get(
        ROOT
        + f"billing/invoices/{job.invoice.id}/?projection=mobile_v1&platform=android"
    )
    assert invoice.status_code == 200, invoice.data
    assert invoice.json()["data"]["activation_case_id"] == str(case.id)
    assert "pay" not in invoice.json()["data"]["allowed_actions"]
    deliver(job.pk)
    deliver(job.pk)
    job.refresh_from_db()
    case.refresh_from_db()
    assert job.status == "fulfilled" and not blocker(case)
    assert (
        PaymentReceipt.objects.count()
        == InvoicePaymentAllocation.objects.count()
        == AccountSubscription.objects.count()
        == 1
    )
    assert case.status == "open" and case.revision == 2
    assert events.count() == 2


def test_activation_case_never_opens_without_confirmed_capture_or_for_another_account(
    client, buyer, plan, hosted
):
    payment = checkout(client, plan)
    assert not RentalOperationalCase.objects.exists()
    job = fail_activation(payment)
    stranger = get_user_model().objects.create_user(
        email="other-activation@example.test", password="local-only"
    )
    client.force_authenticate(stranger)
    assert client.get(ROOT + f"rental-cases/{job.case.id}/").status_code == 404
    assert not case_queryset(stranger).filter(pk=job.case_id).exists()


def test_company_activation_visibility_rechecks_current_billing_membership(
    client, buyer, plan, hosted, company_setup
):
    job = fail_activation(checkout(client, plan))
    _, coordinator, approver, company, *_ = company_setup
    job.invoice.organization = company
    job.invoice.workspace = "company"
    job.invoice.save()
    # Original payer gains no permanent company access through opened_by.
    assert not case_queryset(buyer).filter(pk=job.case_id).exists()
    member = company.memberships.get(user=coordinator)
    member.is_admin = True
    member.save()
    assert case_queryset(coordinator).filter(pk=job.case_id).exists()
    member.is_active = False
    member.save()
    assert not case_queryset(coordinator).filter(pk=job.case_id).exists()


def test_activation_follow_up_reply_recovers_without_another_payment(
    client, buyer, plan, hosted
):
    job = fail_activation(checkout(client, plan))
    buyer.is_verified = True
    buyer.save(update_fields=["is_verified"])
    command = {
        "request_key": str(uuid.uuid4()),
        "expected_revision": job.case.revision,
        "action": "reply",
        "reason": "Please check the original service activation.",
    }
    url = ROOT + f"rental-cases/{job.case.id}/"
    response = client.post(url, command, format="json")
    assert response.status_code == 200, response.data
    repeated = client.post(url, command, format="json")
    assert repeated.status_code == 200 and repeated.data == response.data
    assert len(client.get(url).data["replies"]) == 1
    assert (
        PaymentReceipt.objects.count() == InvoicePaymentAllocation.objects.count() == 1
    )
    job.refresh_from_db()
    assert job.status == "pending" and not AccountSubscription.objects.exists()


def test_support_follow_up_does_not_grant_invoice_access_or_financial_actions(
    client, buyer, plan, hosted
):
    from core_apps.admin_api.models import StaffProfile

    job = fail_activation(checkout(client, plan))
    support = get_user_model().objects.create_user(
        email="activation-support@example.test", password="local-only", is_verified=True
    )
    profile = StaffProfile.objects.create(user=support, role_name="support")
    client.force_authenticate(support)
    url = ROOT + f"rental-cases/{job.case.id}/"
    response = client.get(url)
    assert response.status_code == 200, response.data
    assert response.data["service_activation"]["can_open_invoice"] is False
    assert "link_remedy" not in response.data["allowed_actions"]
    command = {
        "request_key": str(uuid.uuid4()),
        "expected_revision": job.case.revision,
        "action": "reply",
        "reason": "Reviewing the original activation.",
    }
    assert client.post(url, command, format="json").status_code == 200
    profile.is_active = False
    profile.save(update_fields=["is_active"])
    assert client.post(url, command, format="json").status_code == 404
    assert PaymentReceipt.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_concurrent_activation_workers_do_not_duplicate_case_or_service(
    client, buyer, plan, hosted
):
    job = fail_activation(checkout(client, plan))

    def run(_):
        connections.close_all()
        try:
            return deliver(job.pk).status
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(run, range(2))) == ["fulfilled", "fulfilled"]
    assert (
        RentalOperationalCase.objects.count()
        == AccountSubscription.objects.count()
        == PaymentReceipt.objects.count()
        == 1
    )
