"""Corporate closure notices retain the exact company and current recipient authority."""

# flake8: noqa: F401,F811
import uuid
import pytest
from django.db import transaction
from rest_framework.exceptions import NotFound

from .test_company_tenancy import (
    active_agreement,
    signed_agreement,
    agreement,
    cycle,
    company_setup,
    rental_participants,
    policy,
    authenticated,
    API,
)
from core_apps.features.models import (
    PrivateAccessRevocation,
    RefundRequest,
    CompanyMembership,
)
from core_apps.features.planning_models import PlanningEvent
from core_apps.features.services.company import tenancy_access, tenancy_projection
from core_apps.features.services.company.tenancy_events import authorize
from core_apps.features.services.refund_notifications import record
from core_apps.features.services.planning_notifications import deliver_planning_events

pytestmark = pytest.mark.django_db


def test_exact_context_history_and_removed_role_on_old_notification(active_agreement):
    data, item = active_agreement
    with transaction.atomic():
        tenancy_access.changed(
            item,
            data["coordinator"],
            "company_tenancy_reconciled",
            "Private internal note",
        )
    event = PlanningEvent.objects.get(
        recipient=data["payer"],
        event_key=f"company.tenancy:{item.id}:{item.revision}:payer",
    )
    assert event.destination["workspace"] == "company"
    assert event.destination["company_id"] == str(data["company"].id)
    assert event.destination["lease_id"] == str(item.lease.id)
    owner = PlanningEvent.objects.get(
        recipient=data["owner"],
        event_key=f"company.tenancy:{item.id}:{item.revision}:owner",
    )
    assert owner.destination["workspace"] == "owner"
    with transaction.atomic():
        tenancy_access.changed(item, data["coordinator"], "company_tenancy_reconciled")
    assert authorize(event)  # An older revision opens the current record.
    projected = tenancy_projection.payload(item, data["payer"])
    assert projected["history"][-1]["revision"] == item.revision
    assert "Private internal note" not in str(projected["history"])
    assert deliver_planning_events(event_kinds=["company_tenancy_updated"]) > 0
    event.refresh_from_db()
    assert event.notification_id, (event.delivery_status, event.attempts)
    assert event.notification.scope == "company"
    CompanyMembership.objects.filter(
        company=data["company"], user=data["payer"]
    ).update(is_active=False)
    with pytest.raises(NotFound):
        authorize(event)


def test_revocation_and_mismatched_company_prevent_future_notice(active_agreement):
    data, item = active_agreement
    with transaction.atomic():
        tenancy_access.changed(item, data["coordinator"], "company_tenancy_reconciled")
    event = PlanningEvent.objects.get(
        recipient=data["owner"],
        event_key=f"company.tenancy:{item.id}:{item.revision}:owner",
    )
    event.destination["company_id"] = str(data["owner"].id)
    with pytest.raises(NotFound):
        authorize(event)
    PrivateAccessRevocation.objects.create(
        lease=item.lease, user=data["payer"], reason="Access ended"
    )
    with transaction.atomic():
        tenancy_access.changed(item, data["coordinator"], "company_tenancy_reconciled")
    assert not PlanningEvent.objects.filter(
        recipient=data["payer"],
        event_key=f"company.tenancy:{item.id}:{item.revision}:payer",
    ).exists()


def test_company_refund_history_is_commercial_only_and_retains_pending_state(
    active_agreement,
):
    data, item = active_agreement
    attempt = (
        item.lease.invoices.first()
        .payment_attempts.filter(payment_status="captured")
        .first()
    )
    refund = RefundRequest.objects.create(
        lease=item.lease,
        payment_attempt=attempt,
        requester=data["payer"],
        amount_minor=100,
        refundable_balance_snapshot_minor=100,
        status="processing",
        reason="Private operational note",
        request_key=uuid.uuid4(),
    )
    with transaction.atomic():
        record(refund, "submitted", data["payer"])
    manager = (
        authenticated(data["payer"]).get(API + f"company-tenancies/{item.id}/").data
    )
    entry = next(row for row in manager["refunds"] if row["id"] == str(refund.id))
    assert entry["state"] == "processing"
    assert entry["history"][0]["action"] == "submitted"
    employee = (
        authenticated(data["employee"]).get(API + f"company-tenancies/{item.id}/").data
    )
    assert "refunds" not in employee
    assert "Private operational note" not in str(manager)
    assert "submitted" not in str(employee)
