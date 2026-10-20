"""No report or operational closure can become money, custody or consent."""

import pytest
import uuid
from django.urls import reverse
from django.utils import timezone
from core_apps.admin_api.models import StaffProfile
from core_apps.features.models import (
    LedgerTransaction,
    RentalChange,
    RentalOperationalCase,
    RentInvoice,
)
from core_apps.features.services.rental_lifecycle.cases import case_queryset
from core_apps.features.services.rental_lifecycle.case_commands import act_on_case
from core_apps.support.models import Ticket
from core_apps.support.services.payment_reports import can_read_ticket
from core_apps.features.tests.test_rental_phase5 import phase5_lease, client_for
from core_apps.features.tests.test_company_tenancy import (
    signed_agreement,
    agreement,
    cycle,
    company_setup,
    rental_participants,
    policy,
)
from .test_creation_recovery import create, lookup, BODY

pytestmark = pytest.mark.django_db


def report(client, context, key="report"):
    return create(client, key, {**BODY, "rental_context": context})


def test_direct_retired_commands_are_rejected_without_provider_or_financial_effect(
    phase5_lease, settings
):
    owner, tenant, lease = phase5_lease
    settings.RENTAL_PROVIDER_BACKEND = "disabled"
    invoice = RentInvoice.objects.create(
        lease=lease,
        reference="EXTERNAL-REJECT",
        amount_minor=10000,
        charges_minor=10000,
        status="due",
        due_date=timezone.localdate(),
    )
    response = client_for(tenant).post(
        f"/api/v1/features/v1/rent-invoices/{invoice.id}/external-payment-claims/",
        {},
        format="json",
    )
    assert response.status_code == 409
    assert response.data["code"] == "external_payment_not_supported"
    assert not RentalChange.objects.exists() and not LedgerTransaction.objects.exists()
    invoice.refresh_from_db()
    assert invoice.applied_minor == 0 and invoice.status == "due"
    from core_apps.features.models import PrivateAccessRevocation

    PrivateAccessRevocation.objects.create(lease=lease, user=tenant, reason="Revoked")
    response = client_for(tenant).post(
        f"/api/v1/features/v1/rent-invoices/{invoice.id}/external-payment-claims/",
        {},
        format="json",
    )
    assert response.status_code == 404


def test_report_recovers_original_case_and_private_evidence_without_settling(
    phase5_lease, superuser
):
    superuser.is_verified = True
    superuser.save()
    owner, tenant, lease = phase5_lease
    invoice = RentInvoice.objects.create(
        lease=lease,
        reference="REPORT",
        amount_minor=10000,
        charges_minor=10000,
        status="due",
        due_date=timezone.localdate(),
    )
    client = client_for(tenant)
    context = {
        "issue_code": "off_platform_payment",
        "lease_id": str(lease.id),
        "invoice_id": str(invoice.id),
    }
    response = report(client, context)
    assert response.status_code == 201, response.data
    ticket = Ticket.objects.get()
    item = RentalOperationalCase.objects.get()
    assert item.team == "finance" and str(item.id) == ticket.rental_context["case_id"]
    assert report(client, context).json()["data"]["id"] == str(ticket.id)
    assert lookup(client, "report").json()["data"]["ticket"]["rental_context"][
        "case_id"
    ] == str(item.id)
    assert Ticket.objects.count() == RentalOperationalCase.objects.count() == 1
    assert not case_queryset(owner).filter(pk=item.pk).exists()
    StaffProfile.objects.create(user=owner, role_name="financial_approver")
    assert not case_queryset(owner).filter(pk=item.pk).exists()
    assert case_queryset(tenant).filter(pk=item.pk).exists()
    assert not can_read_ticket(owner, ticket)
    item.assigned_to = superuser
    item.save()
    assert can_read_ticket(superuser, ticket)
    result = act_on_case(
        superuser,
        item.id,
        {
            "action": "resolve",
            "expected_revision": item.revision,
            "request_key": str(uuid.uuid4()),
            "reason": "Explained collection channel; report review only. Invoice remains unpaid.",
            "resolution_code": "no_action_required",
        },
    )
    ticket.refresh_from_db()
    invoice.refresh_from_db()
    assert ticket.status == "resolved"
    assert invoice.status == "due" and invoice.applied_minor == 0
    assert not LedgerTransaction.objects.exists()
    assert result[1] == 200


def test_issue_only_report_is_supported_but_client_cannot_link_operator_case(
    auth_client,
):
    first = report(auth_client, {"issue_code": "off_platform_request"})
    assert first.status_code == 201
    assert "case_id" not in first.json()["data"]["rental_context"]
    assert RentalOperationalCase.objects.get().lease_id is None
    response = report(
        auth_client,
        {
            "issue_code": "off_platform_payment",
            "case_id": "invented",
        },
        key="untrusted",
    )
    assert response.status_code == 400
    assert Ticket.objects.count() == 1


def test_company_employee_cannot_attach_financial_invoice_but_can_report(
    signed_agreement,
):
    people, item = signed_agreement
    invoice = item.lease.invoices.get()
    client = client_for(people["employee"])
    blocked = report(
        client, {"issue_code": "off_platform_payment", "invoice_id": str(invoice.id)}
    )
    assert blocked.status_code == 404
    assert (
        report(
            client, {"issue_code": "off_platform_request"}, key="general"
        ).status_code
        == 201
    )


def test_assigned_finance_reader_does_not_gain_other_tickets_or_keep_revoked_role(
    user, another_user
):
    from core_apps.support.services import create_ticket

    profile = StaffProfile.objects.create(
        user=another_user, role_name="financial_approver"
    )
    first = create_ticket(
        user,
        "tenant",
        "payment",
        "Private report",
        "Review this report only.",
        rental_context={"issue_code": "off_platform_request"},
    )
    second = create_ticket(
        user, "tenant", "other", "Other inquiry", "Unrelated private information."
    )
    item = RentalOperationalCase.objects.get()
    assert not can_read_ticket(another_user, first)
    item.assigned_to = another_user
    item.save()
    assert can_read_ticket(another_user, first)
    assert not can_read_ticket(another_user, second)
    profile.is_active = False
    profile.save()
    another_user.refresh_from_db()
    assert not can_read_ticket(another_user, first)


def test_assigned_finance_console_has_reachable_read_only_report(
    client, user, another_user, settings
):
    from django.contrib import admin
    from core_apps.features.case_admin import RentalCaseAdmin
    from core_apps.support.services import create_ticket

    # Render the real admin view without requiring a production collectstatic
    # manifest in this isolated test environment.
    settings.STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.StaticFilesStorage"
    )
    another_user.is_staff = another_user.is_verified = True
    another_user.save()
    StaffProfile.objects.create(user=another_user, role_name="financial_approver")
    ticket = create_ticket(
        user,
        "tenant",
        "payment",
        "Private finance report",
        "Private evidence belongs only to this review.",
        rental_context={"issue_code": "off_platform_request"},
    )
    item = RentalOperationalCase.objects.get()
    item.assigned_to = another_user
    item.save()
    target = reverse("admin:support_ticket_change", args=[ticket.pk])
    assert target in str(
        RentalCaseAdmin(RentalOperationalCase, admin.site).support_report(item)
    )
    client.force_login(another_user)
    response = client.get(target)
    assert response.status_code == 200
    assert b"Private evidence belongs only" in response.content
    assert b'name="reply"' not in response.content


def test_anonymous_admin_login_does_not_query_assigned_private_reports(
    client, settings
):
    from django.contrib.auth.models import AnonymousUser
    from core_apps.support.services.payment_reports import readable_tickets

    settings.STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.StaticFilesStorage"
    )
    assert not readable_tickets(AnonymousUser()).exists()
    response = client.get(reverse("admin:login"))
    assert response.status_code == 200
    assert b'name="username"' in response.content
