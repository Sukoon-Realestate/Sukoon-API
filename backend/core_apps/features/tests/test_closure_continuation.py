import pytest
from core_apps.features.models import PaymentAttempt, Lease
from core_apps.support.models import Ticket
from core_apps.support.services.ticket_service_parts.create_ticket import create_ticket
from core_apps.features.tests.test_rental_phase3 import phase3_lease, client_for
from core_apps.features.tests.test_rental_lifecycle_safety import checkout

pytestmark = pytest.mark.django_db
URL = "/api/v1/features/v1/continuation-items/"


def test_device_without_local_key_finds_original_attempt_during_disable(
    phase3_lease, settings
):
    owner, tenant, lease = phase3_lease
    attempt = checkout(tenant, lease)
    settings.RENTAL_FAKE_PROVIDER_ALLOWED = False
    settings.RENTAL_PROVIDER_BACKEND = "disabled"
    response = client_for(tenant).get(URL, {"workspace": "tenant"})
    assert response.status_code == 200, response.data
    assert response["Cache-Control"] == "private, no-store"
    row = response.data["results"][0]
    assert row["resource_id"] == str(attempt.id)
    assert row["subject_id"] == str(attempt.invoice.id)
    assert row["resource_kind"] == "rent_payment"
    assert "request_key" not in row and "amount" not in row
    assert client_for(owner).get(URL, {"workspace": "tenant"}).data["count"] == 0
    assert client_for(tenant).get(URL, {"workspace": "owner"}).data["count"] == 0
    assert PaymentAttempt.objects.count() == 1
    attempt.refresh_from_db()
    assert attempt.payment_status in {"created", "pending"}


def test_server_pagination_and_support_workspace_are_not_local_drafts(phase3_lease):
    owner, tenant, lease = phase3_lease
    for index in range(23):
        create_ticket(
            user=tenant,
            workspace="tenant",
            category="other",
            subject=f"Inquiry {index}",
            description="Please review my inquiry.",
        )
    private = create_ticket(
        user=tenant,
        workspace="owner",
        category="other",
        subject="Owner inquiry",
        description="Owner workspace only.",
    )
    lease.status = Lease.Status.PENDING_SIGNATURES
    lease.save()
    first = client_for(tenant).get(URL, {"workspace": "tenant", "page_size": 10}).data
    second = (
        client_for(tenant)
        .get(URL, {"workspace": "tenant", "page_size": 10, "page": 2})
        .data
    )
    assert first["count"] == 24 and first["total_pages"] == 3
    assert len(first["results"]) == 10 and len(second["results"]) == 10
    assert not {row["resource_id"] for row in first["results"]} & {
        row["resource_id"] for row in second["results"]
    }
    assert str(private.id) not in {
        row["resource_id"] for row in first["results"] + second["results"]
    }
    owner_rows = client_for(tenant).get(URL, {"workspace": "owner"}).data["results"]
    assert [row["resource_id"] for row in owner_rows] == [str(private.id)]
    private.status = Ticket.Status.CLOSED
    private.save()
    assert client_for(tenant).get(URL, {"workspace": "owner"}).data["count"] == 0
    assert client_for(tenant).get(URL, {"workspace": "arbitrary"}).status_code == 400


def test_protected_deletion_keeps_obligations_and_one_review_request(phase3_lease):
    from django.urls import reverse
    from core_apps.users.models import User

    owner, tenant, lease = phase3_lease
    attempt = checkout(tenant, lease)
    url = reverse("user-delete")
    for _ in range(2):
        response = client_for(tenant).delete(url)
        assert response.status_code == 409, response.data
        assert response.data["status"] == "awaiting_policy"
        assert not response.cookies
    assert User.objects.filter(pk=tenant.pk, is_active=True).exists()
    assert Lease.objects.filter(pk=lease.pk).exists()
    assert PaymentAttempt.objects.filter(pk=attempt.pk).exists()
    assert (
        Ticket.objects.filter(user=tenant, reference__startswith="PRIVACY-").count()
        == 1
    )


from core_apps.features.tests.test_company_housing import (
    company_setup,
    proposed,
    rental_participants,
    policy,
)
from core_apps.features.company_models import CompanyMembership


def test_company_continuation_requires_current_membership_and_assigned_authority(
    company_setup,
):
    owner, coordinator, approver, company, *_ = company_setup
    item = proposed(company_setup)

    def work(user):
        return [
            row
            for row in client_for(user)
            .get(URL, {"workspace": "tenant"})
            .data["results"]
            if row["resource_kind"] == "company_work"
        ]

    assert work(coordinator)[0]["resource_id"] == str(item.id)
    assert work(approver)[0]["subject_id"] == str(company.id)
    assert work(owner) == []
    member = CompanyMembership.objects.get(company=company, user=coordinator)
    member.is_admin = member.is_coordinator = False
    member.is_employee = True
    member.save()
    assert work(coordinator) == []
    CompanyMembership.objects.filter(company=company, user=approver).update(
        is_active=False
    )
    assert work(approver) == []
