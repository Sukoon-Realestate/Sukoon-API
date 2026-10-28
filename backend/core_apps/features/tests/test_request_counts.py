"""Pending inbox badges use account-scoped totals, never a page length."""

from datetime import timedelta
import uuid

import pytest
from django.urls import reverse
from django.utils import timezone

from core_apps.features.company_models import (
    Company,
    CompanyBookingItem,
    CompanyHousingRequest,
    CompanyMembership,
    PortfolioOffer,
)
from core_apps.features.models import (
    Lease,
    RentalInterest,
    TenancyInvitation,
    TermsProposal,
)
from core_apps.features.planning_models import (
    GroupProcess,
    HousingGroup,
    HousingOffer,
    HousingRequest,
    RoommateConnection,
    TenancyTransition,
)
from core_apps.features.services.request_counts import (
    company_approval_counts,
    pending_request_counts,
)
from core_apps.features.tests.test_rental_phase2 import (
    authenticated,
    rental_participants,
)
from core_apps.users.models import User

pytestmark = pytest.mark.django_db


def connect(first, second, *, requester, status="pending"):
    first, second = sorted((first, second), key=lambda user: user.pk)
    return RoommateConnection.objects.create(
        first=first,
        second=second,
        requester=requester,
        status=status,
    )


def interest(prop, tenant, **kwargs):
    return RentalInterest.objects.create(
        property=prop,
        tenant=tenant,
        offer_id="offer",
        offer_revision=1,
        offer_snapshot={},
        desired_start=timezone.localdate(),
        months=1,
        **kwargs,
    )


def test_roommate_count_is_incoming_and_not_limited_to_one_page(rental_participants):
    owner, tenant, stranger, _, _ = rental_participants
    for index in range(27):
        sender = User.objects.create_user(email=f"roommate-{index}@example.com")
        connect(sender, tenant, requester=sender)
    connect(owner, tenant, requester=tenant)
    connect(stranger, owner, requester=stranger)
    assert pending_request_counts(tenant)["roommate_connections"] == 27
    client = authenticated(tenant)
    response = client.get("/api/v1/features/v1/workspace-summary/")
    assert response.status_code == 200, response.data
    assert response.json()["data"]["request_counts"]["roommate_connections"] == 27
    assert response["Cache-Control"] == "private, no-store"
    # Reading the inbox summary must not mark a pending request as handled.
    assert (
        client.get(reverse("tenant-unread-counts")).json()["data"]["request_counts"][
            "roommate_connections"
        ]
        == 27
    )


@pytest.mark.parametrize(
    "status",
    ["accepted", "declined", "withdrawn", "expired", "disconnected", "blocked"],
)
def test_resolved_roommate_request_disappears(rental_participants, status):
    owner, tenant, _, _, _ = rental_participants
    connection = connect(owner, tenant, requester=owner)
    assert pending_request_counts(tenant)["roommate_connections"] == 1
    connection.status = status
    connection.save(update_fields=["status"])
    assert pending_request_counts(tenant)["roommate_connections"] == 0


def test_invitation_count_excludes_expired_consumed_outgoing_and_other_users(
    rental_participants,
):
    owner, tenant, stranger, prop, _ = rental_participants
    now = timezone.now()
    for extra in [
        {},
        {"expires_at": now - timedelta(seconds=1)},
        {"consumed_at": now},
        {"status": "accepted"},
        {"status": "rejected"},
        {"status": "revoked"},
        {"tenant": stranger},
    ]:
        values = dict(
            property=prop,
            owner=owner,
            tenant=tenant,
            initiated_by=owner,
            expires_at=now + timedelta(days=1),
            offer_snapshot={},
            offer_id=str(uuid.uuid4()),
        )
        TenancyInvitation.objects.create(**(values | extra))
    assert pending_request_counts(tenant)["tenancy_invitations"] == 1
    assert pending_request_counts(owner)["tenancy_invitations"] == 0


def test_interest_count_follows_whose_response_is_due(rental_participants):
    owner, tenant, stranger, prop, _ = rental_participants
    waiting_owner = interest(prop, tenant)
    waiting_tenant = interest(prop, tenant, waiting_for="tenant", status="under_review")
    interest(prop, tenant, status="withdrawn")
    proposed = interest(prop, tenant, status="proposed")
    proposal = TermsProposal.objects.create(
        interest=proposed, owner=owner, terms={}, offer_snapshot={}
    )
    assert pending_request_counts(owner, owner=True)["rental_interests"] == 1
    assert pending_request_counts(tenant)["rental_interests"] == 2
    assert pending_request_counts(stranger, owner=True)["rental_interests"] == 0
    waiting_owner.waiting_for = "tenant"
    waiting_owner.save(update_fields=["waiting_for"])
    proposal.status = "changes_requested"
    proposal.save(update_fields=["status"])
    assert pending_request_counts(owner, owner=True)["rental_interests"] == 1
    assert pending_request_counts(tenant)["rental_interests"] == 2
    # Only the latest terms revision contributes, even when an old row remains proposed.
    TermsProposal.objects.create(
        interest=proposed, owner=owner, terms={}, offer_snapshot={}, status="accepted"
    )
    assert pending_request_counts(owner, owner=True)["rental_interests"] == 0


def test_group_application_count_is_owner_review_only(rental_participants):
    owner, tenant, stranger, prop, _ = rental_participants
    group = HousingGroup.objects.create(name="Students")
    for state in ["under_review", "collecting_consent", "approved", "declined"]:
        GroupProcess.objects.create(
            group=group,
            initiated_by=tenant,
            property=prop,
            kind="application",
            roster_revision=1,
            status=state,
        )
    assert pending_request_counts(owner, owner=True)["group_applications"] == 1
    assert pending_request_counts(stranger, owner=True)["group_applications"] == 0
    response = authenticated(owner).get(reverse("owner-unread-counts"))
    assert response.json()["data"]["request_counts"]["group_applications"] == 1
    group.status = "archived"
    group.save(update_fields=["status"])
    assert pending_request_counts(owner, owner=True)["group_applications"] == 0


def test_offer_count_excludes_answered_expired_and_stale_request_versions(
    rental_participants,
):
    owner, tenant, stranger, prop, _ = rental_participants
    request = HousingRequest.objects.create(
        user=tenant, title="Housing", expires_at=timezone.now() + timedelta(days=1)
    )
    for status, revision in [
        ("sent", 1),
        ("viewed", 1),
        ("shortlisted", 1),
        ("declined", 1),
        ("sent", 2),
    ]:
        HousingOffer.objects.create(
            request=request,
            owner=owner,
            property=prop,
            rent_minor=100,
            price_period="monthly",
            status=status,
            request_revision=revision,
            reviewed_content_revision=revision,
        )
    assert pending_request_counts(tenant)["housing_offers"] == 3
    assert pending_request_counts(stranger)["housing_offers"] == 0
    request.expires_at = timezone.now() - timedelta(seconds=1)
    request.save(update_fields=["expires_at"])
    assert pending_request_counts(tenant)["housing_offers"] == 0


def test_replacement_count_requires_current_candidate_and_pending_consent(
    rental_participants,
):
    owner, tenant, stranger, prop, _ = rental_participants
    candidate = interest(prop, tenant)
    lease = Lease.objects.create(
        property=prop,
        owner=owner,
        tenant=stranger,
        start_date=timezone.localdate(),
        end_date=timezone.localdate() + timedelta(days=30),
        rent_amount_minor=100,
    )
    transition = TenancyTransition.objects.create(
        lease=lease,
        author=stranger,
        candidate=candidate,
        candidate_revision=1,
        kind="replacement",
        status="candidate_pending",
        requested_on=timezone.localdate(),
    )
    assert pending_request_counts(tenant)["replacement_invitations"] == 1
    assert pending_request_counts(stranger)["replacement_invitations"] == 0
    candidate.revision += 1
    candidate.save(update_fields=["revision"])
    assert pending_request_counts(tenant)["replacement_invitations"] == 0
    transition.candidate_revision = candidate.revision
    transition.status = "declined"
    transition.save(update_fields=["candidate_revision", "status"])
    assert pending_request_counts(tenant)["replacement_invitations"] == 0


def test_company_counts_are_assigned_to_active_approvers_and_company(
    rental_participants,
):
    owner, tenant, stranger, _, _ = rental_participants
    offer = PortfolioOffer.objects.create(
        owner=owner, scope="selected_units", monthly_rent_minor=100
    )
    companies = []
    for count in [2, 3]:
        company = Company.objects.create(name=f"Company {count}")
        member = CompanyMembership.objects.create(
            company=company, user=tenant, is_approver=True
        )
        request = CompanyHousingRequest.objects.create(
            company=company,
            requester=owner,
            coordinator=owner,
            starts_on=timezone.localdate(),
            ends_on_exclusive=timezone.localdate() + timedelta(days=30),
            headcount=1,
            commitment_ceiling_minor=100,
            deposit_limit_minor=0,
        )
        for status in ["approval_pending"] * count + ["approved", "rejected"]:
            CompanyBookingItem.objects.create(
                request=request,
                offer=offer,
                snapshot={},
                snapshot_digest=str(uuid.uuid4()),
                quote_expires_at=timezone.now() + timedelta(days=1),
                full_term_rent_minor=100,
                deposit_minor=0,
                assigned_approver=member,
                status=status,
            )
        companies.append((company, member))
    expected = {
        str(company.id): count for (company, _), count in zip(companies, [2, 3])
    }
    assert company_approval_counts(tenant) == expected
    assert company_approval_counts(stranger) == {}
    response = authenticated(tenant).get("/api/v1/features/v1/workspace-summary/")
    assert response.json()["data"]["company_approval_counts"] == {}
    for company, _ in companies:
        response = authenticated(tenant).get(
            "/api/v1/features/v1/workspace-summary/",
            HTTP_X_SUKOON_COMPANY_ID=str(company.id),
            HTTP_X_SUKOON_COMPANY_ROLE="approver",
        )
        assert response.json()["data"]["company_approval_counts"] == {
            str(company.id): expected[str(company.id)]
        }
    companies[0][1].is_active = False
    companies[0][1].save(update_fields=["is_active"])
    assert company_approval_counts(tenant) == {str(companies[1][0].id): 3}
    companies[1][1].is_approver = False
    companies[1][1].save(update_fields=["is_approver"])
    assert company_approval_counts(tenant) == {}


def test_unverified_account_has_no_private_request_totals(rental_participants):
    owner, tenant, _, _, _ = rental_participants
    connect(owner, tenant, requester=owner)
    tenant.is_verified = False
    assert pending_request_counts(tenant) == {}
    assert company_approval_counts(tenant) == {}
