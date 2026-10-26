"""Account deletion stops new negotiations without cancelling existing obligations."""

# flake8: noqa: F401,F811
import pytest
from datetime import timedelta
from django.utils import timezone
from core_apps.users.models import AccountClosureRequest
from core_apps.features.models import GroupBookingProposal
from .test_company_negotiation import (
    cycle,
    company_setup,
    rental_participants,
    policy,
    start,
    act,
    authenticated,
    API,
    command,
)
from .test_group_booking_negotiation import setup as group_setup, act as group_act
from .test_rental_lifecycle_safety import booking_setup
from .test_rental_lifecycle import post
from .test_cycle_concurrency import parallel_calls
from core_apps.users.tests.test_account_closure import submit

pytestmark = pytest.mark.django_db


def close(user):
    return AccountClosureRequest.objects.create(
        user=user, reason="Local pending closure", active=True
    )


@pytest.mark.parametrize("index", [0, 1, 2])
def test_group_creation_rechecks_every_allocation_account(
    rental_participants, policy, index
):
    owner, *_ = rental_participants
    _, body = booking_setup(rental_participants)
    close(rental_participants[index])
    result = post(owner, "group-booking-proposals/", body)
    assert result.status_code == 403, result.data
    assert not GroupBookingProposal.objects.exists()


def test_group_terms_block_pending_member_but_preserve_rejection_and_withdrawal(
    rental_participants, policy
):
    owner, representative, member, *_ = rental_participants
    proposal, _, _ = group_setup(rental_participants)
    assert group_act(owner, proposal, "submit").status_code == 200
    close(member)
    blocked = group_act(representative, proposal, "terms/accept")
    assert blocked.status_code == 403, blocked.data
    proposal.refresh_from_db()
    assert proposal.status == "negotiating"
    rejected = group_act(
        representative, proposal, "terms/reject", reason="Cannot proceed"
    )
    assert rejected.status_code == 200, rejected.data


def test_closure_affects_only_independent_pending_allocation(
    rental_participants, policy
):
    owner, representative, member, *_ = rental_participants
    proposal, _, _ = group_setup(rental_participants)
    assert group_act(owner, proposal, "submit").status_code == 200
    assert group_act(representative, proposal, "terms/accept").status_code == 200
    close(member)
    accepted = group_act(
        representative,
        proposal,
        "consents",
        decision="accept",
        terms_digest=proposal.terms_digest,
    )
    assert accepted.status_code == 200, accepted.data
    blocked = group_act(
        member,
        proposal,
        "consents",
        decision="accept",
        terms_digest=proposal.terms_digest,
    )
    assert blocked.status_code == 403, blocked.data
    assert proposal.participants.get(tenant=representative).invitation_id
    assert not proposal.participants.get(tenant=member).invitation_id
    withdrawn = group_act(member, proposal, "withdraw")
    assert withdrawn.status_code == 200, withdrawn.data


@pytest.mark.parametrize("who", ["owner", "coordinator"])
def test_company_accept_rechecks_closure_and_withdraw_stays_available(cycle, who):
    negotiation, _, _ = start(cycle)
    close(cycle[who])
    result = act(cycle, negotiation, "owner", "accept")
    assert result.status_code == 403, result.data
    current = authenticated(cycle["owner"]).get(
        API + f"company-terms-negotiations/{negotiation.id}/"
    )
    assert "accept" in current.data["available_actions"]
    assert "accept" not in current.data["allowed_actions"]
    assert "account_closure_pending" in current.data["blocking_reasons"]
    assert (
        act(
            cycle, negotiation, "owner", "withdraw", reason="No new business"
        ).status_code
        == 200
    )


def test_company_original_receipt_and_rejection_remain_available(cycle):
    item, body, path = start(cycle)
    close(cycle["owner"])
    replay = authenticated(cycle["coordinator"]).post(path, body, format="json")
    assert replay.status_code == 201 and replay.data["resource"]["id"] == str(item.id)
    assert (
        act(cycle, item, "owner", "reject", reason="Cannot proceed").status_code == 200
    )


def test_company_start_cannot_create_new_terms_for_pending_owner(cycle):
    item = cycle["item"]
    snapshot = item.snapshot
    close(cycle["owner"])
    response = authenticated(cycle["coordinator"]).post(
        API + f"company-booking-items/{item.id}/negotiation/",
        command(
            expected_revision=item.revision,
            expires_at=(timezone.now() + timedelta(hours=12)).isoformat(),
            terms={
                "monthly_rent_minor": snapshot["monthly_rent"]["amount_minor"],
                "deposit_minor": 0,
                "starts_on": snapshot["starts_on"],
                "ends_on_exclusive": snapshot["ends_on_exclusive"],
                "occupants": 2,
                "included_services": [],
                "excluded_services": [],
            },
        ),
        format="json",
    )
    assert response.status_code == 403, response.data
    assert not hasattr(item, "negotiation")


@pytest.mark.django_db(transaction=True)
def test_group_acceptance_and_account_closure_serialize_without_partial_consent(
    rental_participants, policy
):
    owner, representative, member, *_ = rental_participants
    proposal, _, _ = group_setup(rental_participants)
    assert group_act(owner, proposal, "submit").status_code == 200
    accepted, _ = parallel_calls(
        lambda index: (
            group_act(representative, proposal, "terms/accept")
            if index == 0
            else submit(member)
        )
    )
    proposal.refresh_from_db()
    closure = AccountClosureRequest.objects.get(user=member, active=True)
    if accepted.status_code == 200:
        assert proposal.status == "awaiting_participants"
        assert proposal.updated_at <= closure.created_at
    else:
        assert accepted.status_code == 403, accepted.data
        assert proposal.status == "negotiating"
    assert not proposal.participants.filter(invitation__isnull=False).exists()
