"""An old pending negotiation cannot create new obligations after restriction."""

import pytest
from django.utils import timezone

from core_apps.chat.models import RentalChatContext, ChatPolicyConsent, ChatPolicyNotice
from core_apps.chat.moderation.policy import VERSION
from core_apps.chat.moderation.decisions import acknowledge
from core_apps.chat.services.message_service import get_or_create_direct_conversation
from core_apps.chat.tests.test_rental_moderation import send, run
from core_apps.features.models import Lease, TenancyInvitation, GroupBookingProposal
from core_apps.features.tests.test_rental_phase2 import (
    rental_participants, complete_owner_onboarding,
)
from core_apps.features.tests.test_rental_lifecycle import (
    policy, proposal_for, post, command,
)
from core_apps.features.tests.test_rental_lifecycle_safety import booking_setup, checkout
from core_apps.features.tests.test_rental_phase3 import phase3_lease

pytestmark = pytest.mark.django_db


def restrict(subject, other, settings):
    settings.CHAT_MODERATION_MODE = "enforce"
    chat = get_or_create_direct_conversation(user=subject, other_user=other)
    RentalChatContext.objects.get_or_create(conversation=chat, defaults={"owner": subject})
    for person in (subject, other):
        ChatPolicyConsent.objects.get_or_create(user=person, version=VERSION)
    send(chat, subject)
    run()
    notice = ChatPolicyNotice.objects.get(user=subject, kind="warning")
    acknowledge(subject, chat, {"policy_version": VERSION, "notice_id": notice.id})
    send(chat, subject)
    run()


@pytest.mark.parametrize("target", ["owner", "tenant"])
def test_rental_policy_acceptance_rejected_but_rejection_allowed(
    rental_participants, settings, target,
):
    owner, tenant, _, prop, offer = rental_participants
    proposal = proposal_for(tenant, prop, offer)
    proposal.status, proposal.accepted_by = "proposed", [str(owner.id)]
    proposal.save()
    restrict(owner if target == "owner" else tenant, tenant if target == "owner" else owner, settings)
    base = f"terms-proposals/{proposal.id}/respond/"
    denied = post(tenant, base, command(proposal.revision, decision="accept"))
    assert denied.status_code == 403, denied.data
    proposal.refresh_from_db()
    assert proposal.status == "proposed"
    rejected = post(tenant, base, command(proposal.revision, decision="reject"))
    assert rejected.status_code == 200, rejected.data


def test_rental_policy_old_terms_cannot_create_invitation_or_submit_draft(
    rental_participants, settings,
):
    owner, tenant, _, prop, offer = rental_participants
    complete_owner_onboarding(owner)
    proposal = proposal_for(tenant, prop, offer)
    restrict(tenant, owner, settings)
    denied = post(owner, "tenancy-invitations/", command(
        interest_id=str(proposal.interest.id), interest_revision=proposal.interest.revision,
        terms_proposal_id=str(proposal.id), property_id=str(prop.id),
        offer_id=offer, offer_revision=2, tenant_id=str(tenant.id),
    ))
    assert denied.status_code == 403, denied.data
    assert not TenancyInvitation.objects.exists()
    lease = Lease.objects.create(
        owner=owner, tenant=tenant, property=prop, status="draft",
        start_date=timezone.localdate(), end_date=timezone.localdate(),
        rent_amount_minor=1_000_000, legacy_read_only=False,
    )
    result = post(owner, f"leases/{lease.id}/submit-for-signature/", command(
        lease.revision, decision="submit_for_signature",
    ))
    assert result.status_code == 403, result.data
    lease.refresh_from_db()
    assert lease.status == "draft" and not lease.document_id


def test_rental_policy_old_group_application_cannot_create_booking(
    rental_participants, policy, settings,
):
    owner, tenant, _, _, _ = rental_participants
    _, body = booking_setup(rental_participants)
    restrict(tenant, owner, settings)
    result = post(owner, "group-booking-proposals/", body)
    assert result.status_code == 403, result.data
    assert not GroupBookingProposal.objects.exists()


def test_rental_policy_group_acceptance_cannot_create_invitation_but_can_decline(
    rental_participants, policy, settings,
):
    owner, tenant, _, _, _ = rental_participants
    _, body = booking_setup(rental_participants)
    created = post(owner, "group-booking-proposals/", body)
    assert created.status_code == 201, created.data
    proposal = created.data["resource"]
    base = f"group-booking-proposals/{proposal['id']}/"
    assert post(owner, base + "submit/", command(1)).status_code == 200
    restrict(owner, tenant, settings)
    result = post(tenant, base + "consents/", command(
        2, decision="accept", terms_digest=proposal["terms_digest"],
    ))
    assert result.status_code == 403, result.data
    assert not TenancyInvitation.objects.exists()
    declined = post(tenant, base + "consents/", command(
        2, decision="decline", terms_digest=proposal["terms_digest"],
    ))
    assert declined.status_code == 200, declined.data


@pytest.mark.parametrize("target", ["owner", "tenant"])
def test_rental_policy_existing_invoice_checkout_remains_available(phase3_lease, settings, target):
    owner, tenant, lease = phase3_lease
    restrict(owner if target == "owner" else tenant, tenant if target == "owner" else owner, settings)
    attempt = checkout(tenant, lease)
    assert attempt.invoice.lease_id == lease.pk
    tenant.refresh_from_db()
    assert tenant.is_active
