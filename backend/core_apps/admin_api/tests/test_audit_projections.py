import pytest
from rest_framework.exceptions import APIException, NotFound, PermissionDenied
from core_apps.admin_api.services.financials_service_parts.get_financial_summary import (
    get_financial_summary,
)
from core_apps.admin_api.services.financials_service_parts.get_transactions_list import (
    get_transactions_list,
)
from core_apps.admin_api.services.system_service_parts.get_system_health import (
    get_system_health,
    send_push_notification,
)
from core_apps.admin_api.services.system_service_parts.get_audit_logs import (
    get_audit_logs,
)
from core_apps.admin_api.services.property_service import approve_admin_property
from core_apps.features.tests.test_rental_phase6 import phase6_lease, captured_payment
from core_apps.features.models import LedgerTransaction, LedgerEntry, RentalAuditEvent
from core_apps.admin_api.models import StaffProfile

pytestmark = pytest.mark.django_db


def test_empty_financials_and_audit_do_not_invent_evidence():
    summary = get_financial_summary()
    assert summary["metrics"]["totalRevenueMonth"] == "0.00 EGP"
    assert summary["metrics"]["avgRent"] == "Unavailable"
    assert get_transactions_list() == [] and get_audit_logs() == []
    assert get_system_health()["metrics"]["uptime"] == "Unavailable"
    with pytest.raises(APIException):
        send_push_notification("Test", "No delivery configured")


def test_financial_revenue_excludes_deposits_and_unearned_commission(phase6_lease):
    _, tenant, lease = phase6_lease
    invoice, attempt, _ = captured_payment(lease, tenant)
    tx = LedgerTransaction.objects.create(
        lease=lease, invoice=invoice, reference="audit-revenue", kind="audit-test"
    )
    for account, amount, direction in [
        ("commission_revenue", 150, "credit"),
        ("commission_revenue", 50, "debit"),
        ("deposit_liability", 10000, "credit"),
        ("unearned_commission", 7000, "credit"),
    ]:
        LedgerEntry.objects.create(
            transaction=tx, account=account, amount_minor=amount, direction=direction
        )
    assert get_financial_summary()["metrics"]["totalRevenueMonth"] == "1.00 EGP"
    rows = get_transactions_list()
    assert len(rows) == 1 and rows[0]["id"] == str(attempt.id)


def test_property_alias_never_selects_another_listing(phase6_lease, superuser):
    _, _, lease = phase6_lease
    original = lease.property.updated_at
    with pytest.raises(NotFound):
        approve_admin_property("prop-1", reviewer=superuser)
    lease.property.refresh_from_db()
    assert lease.property.updated_at == original
    assert not RentalAuditEvent.objects.filter(subject_id=lease.property.id).exists()


def test_property_moderation_rechecks_current_role_and_records_actor(
    phase6_lease, superuser
):
    owner, _, lease = phase6_lease
    StaffProfile.objects.create(
        user=owner, role_name="property_reviewer", is_active=False
    )
    with pytest.raises(PermissionDenied):
        approve_admin_property(lease.property.id, reviewer=owner)
    approve_admin_property(lease.property.id, reviewer=superuser)
    event = RentalAuditEvent.objects.get(subject_id=lease.property.id)
    assert event.actor == superuser and event.action == "approve_admin_property"
    assert any(row["id"] == f"property-{event.id}" for row in get_audit_logs())


def test_profile_counts_use_attendance_and_actual_conversations(phase6_lease):
    import uuid
    from django.utils import timezone
    from core_apps.profiles.services import ProfileService
    from core_apps.properties.models import PropertyVisit, PropertyVisitDecision
    from core_apps.chat.services.message_service_parts.get_or_create_direct_conversation import (
        get_or_create_direct_conversation,
    )

    owner, tenant, lease = phase6_lease
    scheduled_at = timezone.now()
    visit = PropertyVisit.objects.create(
        property=lease.property,
        tenant=tenant,
        visit_date=scheduled_at.date(),
        visit_time=scheduled_at.time(),
        status="confirmed",
    )
    stats = ProfileService.get_account_summary_data(tenant)["stats"]
    assert stats["completed_visits_count"] == 0 and stats["active_chats_count"] == 0
    PropertyVisitDecision.objects.create(
        visit=visit,
        tenant=tenant,
        owner=owner,
        value="proceed",
        attended=True,
        attested_at=timezone.now(),
        visit_revision=1,
        request_key=uuid.uuid4(),
        property_id_snapshot=lease.property.id,
        scheduled_at=scheduled_at,
    )
    get_or_create_direct_conversation(user=owner, other_user=tenant)
    stats = ProfileService.get_account_summary_data(tenant)["stats"]
    assert stats["completed_visits_count"] == 1 and stats["active_chats_count"] == 1
