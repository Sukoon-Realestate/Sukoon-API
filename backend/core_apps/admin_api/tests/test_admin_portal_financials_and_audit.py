import uuid
from datetime import timedelta
import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from core_apps.admin_api.services.financials_service_parts.get_transactions_list import (
    get_transactions_list,
)
from core_apps.admin_api.services.system_service_parts.get_audit_logs import (
    get_audit_logs,
)
from core_apps.admin_api.models import (
    KYCSubmission,
    UserReport,
    StaffAuthorityAudit,
    PlatformPreferenceAudit,
)
from core_apps.features.models import (
    PaymentAttempt,
    PaymentQuote,
    RefundRequest,
    RentalAuditEvent,
    Lease,
    RentInvoice,
)
from core_apps.properties.models import Property
from core_apps.support.models import Ticket, TicketTransition

User = get_user_model()
pytestmark = pytest.mark.django_db


class TestAdminPortalFinancialsAndAudit:
    def test_transactions_filtering_by_status_and_search(self, make_property):
        landlord = User.objects.create_user(
            email="landlord_tx@test.com", password="Password123!", first_name="Hassan", last_name="Landlord"
        )
        tenant = User.objects.create_user(
            email="tenant_tx@test.com", password="Password123!", first_name="Tarek", last_name="Tenant"
        )
        prop = make_property(owner=landlord, title="Sunny Flat", price=10000)
        lease = Lease.objects.create(
            property=prop,
            owner=landlord,
            tenant=tenant,
            template_id="tpl-standard",
            template_version="1.0",
            start_date="2026-01-01",
            end_date="2026-12-31",
            rent_amount_minor=1000000,
        )
        invoice = RentInvoice.objects.create(
            lease=lease,
            payer=tenant,
            purpose="rent",
            reference="INV-2026-001",
            amount_minor=1000000,
            due_date="2026-01-05",
        )

        # 1. Quote
        quote = PaymentQuote.objects.create(
            invoice=invoice,
            request_key=uuid.uuid4(),
            invoice_revision=1,
            payer_amount_minor=1000000,
            policy_version="1.0",
            fingerprint="fp-test-quote",
            expires_at=timezone.now() + timedelta(days=1),
        )

        # 2. Captured payment
        p1 = PaymentAttempt.objects.create(
            invoice=invoice,
            payer=tenant,
            quote=quote,
            request_key=uuid.uuid4(),
            invoice_revision=1,
            amount_minor=1000000,
            payment_status="captured",
        )

        # 3. Pending payment
        p2 = PaymentAttempt.objects.create(
            invoice=invoice,
            payer=tenant,
            quote=quote,
            request_key=uuid.uuid4(),
            invoice_revision=1,
            amount_minor=1000000,
            payment_status="pending",
        )

        # 4. Succeeded refund
        r1 = RefundRequest.objects.create(
            lease=lease,
            payment_attempt=p1,
            request_key=uuid.uuid4(),
            requester=tenant,
            refundable_balance_snapshot_minor=1000000,
            amount_minor=50000,
            status="succeeded",
            reason="Deposit partial return",
        )

        # Test filter "paid"
        paid_rows = get_transactions_list(status_filter="paid")
        paid_ids = [r["id"] for r in paid_rows]
        assert str(p1.id) in paid_ids
        assert str(p2.id) not in paid_ids
        assert str(r1.id) not in paid_ids

        # Test filter "pending"
        pending_rows = get_transactions_list(status_filter="pending")
        pending_ids = [r["id"] for r in pending_rows]
        assert str(p2.id) in pending_ids
        assert str(p1.id) not in pending_ids
        assert str(r1.id) not in pending_ids

        # Test filter "refunded"
        refund_rows = get_transactions_list(status_filter="refunded")
        refund_ids = [r["id"] for r in refund_rows]
        assert str(r1.id) in refund_ids
        assert str(p1.id) not in refund_ids

        # Test search filter by invoice reference
        search_inv = get_transactions_list(search="INV-2026-001")
        assert len(search_inv) >= 2

        # Test search filter by landlord name
        search_landlord = get_transactions_list(search="Hassan")
        assert len(search_landlord) >= 3

    def test_audit_logs_filtering_across_all_badges(self, make_property):
        admin = User.objects.create_user(email="admin_aud@test.com", password="Password123!")
        target_user = User.objects.create_user(email="target_aud@test.com", password="Password123!")

        # 1. KYC
        k = KYCSubmission.objects.create(
            profile=target_user.profile,
            status="approved",
            reviewer=admin,
            reviewed_at="2026-11-01T10:00:00Z",
        )

        # 2. Staff roles
        s = StaffAuthorityAudit.objects.create(
            actor=admin,
            target=target_user,
            action="grant",
            reason="Granted staff",
        )

        # 3. System
        p = PlatformPreferenceAudit.objects.create(
            actor=admin,
            revision=1,
            before={},
            after={"service_fee_rate": 0.05},
        )

        # 4. Reports
        r = UserReport.objects.create(
            reported_user=target_user,
            reviewed_by=admin,
            reason="Spam listing",
            status="dismissed",
        )

        # 5. Props
        prop = make_property(owner=target_user, title="Flat", price=5000)
        e = RentalAuditEvent.objects.create(
            actor=admin,
            subject_kind="property",
            subject_id=prop.id,
            subject_revision=1,
            action="property.moderation.approve",
        )

        # 6. Users suspension
        u_rep = UserReport.objects.create(
            reported_user=target_user,
            reviewed_by=admin,
            reason="Violated policies",
            status=UserReport.Status.SUSPENDED,
        )

        # 7. Support
        t = Ticket.objects.create(user=target_user, subject="Payment query", reference="TCK-100")
        tr = TicketTransition.objects.create(
            ticket=t,
            actor=admin,
            revision=1,
            action="reply",
            reason="Replied to user",
        )

        # Verify type_filter=kyc
        kyc_logs = get_audit_logs(type_filter="kyc")
        assert any(row["id"] == f"kyc-{k.id}" for row in kyc_logs)
        assert all(row["typeBadge"] == "KYC" for row in kyc_logs)

        # Verify type_filter=roles
        role_logs = get_audit_logs(type_filter="roles")
        assert any(row["id"] == f"staff-{s.pk}" for row in role_logs)
        assert all(row["typeBadge"] == "دور" for row in role_logs)

        # Verify type_filter=system
        sys_logs = get_audit_logs(type_filter="system")
        assert any(row["id"] == f"settings-{p.pk}" for row in sys_logs)
        assert all(row["typeBadge"] == "نظام" for row in sys_logs)

        # Verify type_filter=reports
        rep_logs = get_audit_logs(type_filter="reports")
        assert any(row["id"] == f"report-{r.id}" for row in rep_logs)
        assert all(row["typeBadge"] == "بلاغ" for row in rep_logs)

        # Verify type_filter=props
        prop_logs = get_audit_logs(type_filter="props")
        assert any(row["id"] == f"property-{e.id}" for row in prop_logs)
        assert all(row["typeBadge"] == "عقار" for row in prop_logs)

        # Verify type_filter=users
        user_logs = get_audit_logs(type_filter="users")
        assert any(row["id"] == f"user-suspend-{u_rep.id}" for row in user_logs)
        assert all(row["typeBadge"] == "مستخدم" for row in user_logs)

        # Verify type_filter=support
        sup_logs = get_audit_logs(type_filter="support")
        assert any(row["id"] == f"support-{tr.id}" for row in sup_logs)
        assert all(row["typeBadge"] == "دعم" for row in sup_logs)

        # Verify search filter
        search_logs = get_audit_logs(search="TCK-100")
        assert any(row["id"] == f"support-{tr.id}" for row in search_logs)
