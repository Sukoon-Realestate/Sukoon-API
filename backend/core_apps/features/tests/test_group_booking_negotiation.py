"""Independent student commitments following versioned representative negotiation."""

# flake8: noqa: F811
import copy
import uuid
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import connections
from django.utils import timezone

from core_apps.features.models import (
    GroupBookingProposal,
    GroupBookingParticipant,
    GroupBookingTermsVersion,
    ReservationHold,
    Lease,
    PaymentAttempt,
    TermsProposal,
)
from core_apps.features.planning_models import PlanningEvent
from .test_rental_phase2 import rental_participants, authenticated
from .test_rental_lifecycle import policy, command, post, PREFIX
from .test_rental_lifecycle_safety import booking_setup

pytestmark = pytest.mark.django_db


def setup(participants):
    owner, *_ = participants
    application, body = booking_setup(participants)
    response = post(owner, "group-booking-proposals/", body)
    assert response.status_code == 201, response.data
    state = response.data["resource"]
    return GroupBookingProposal.objects.get(id=state["id"]), body, state


def act(actor, item, action, **data):
    item.refresh_from_db()
    return post(
        actor,
        f"group-booking-proposals/{item.id}/{action}/",
        command(
            item.revision,
            **(
                {"terms_digest": item.terms_digest}
                if action.startswith("terms/")
                else {}
            ),
            **data,
        ),
    )


def test_counter_version_keeps_deadline_and_each_commitment_independent(
    rental_participants, policy
):
    owner, rep, member, prop, _ = rental_participants
    item, source, initial = setup(rental_participants)
    assert act(owner, item, "submit").status_code == 200
    allocations = copy.deepcopy(source["participants"])
    rows = [
        {"tenant_id": row["tenant_id"], "terms": row["terms"]} for row in allocations
    ]
    rows[0]["terms"]["monthly_rent"]["amount_minor"] = 850000
    counter = act(rep, item, "terms/counter", participants=rows)
    assert counter.status_code == 200, counter.data
    current = counter.data["resource"]
    assert current["terms_revision"] == 2 and datetime.fromisoformat(
        current["deadline"]
    ) == datetime.fromisoformat(initial["deadline"])
    assert not ReservationHold.objects.exists() and not Lease.objects.exists()
    assert not PaymentAttempt.objects.exists() and not TermsProposal.objects.exists()
    versions = list(item.terms_versions.order_by("version"))
    assert (
        versions[0].participants[0]["terms"]["monthly_rent"]["amount_minor"] == 1000000
    )
    assert (
        versions[1].participants[0]["terms"]["monthly_rent"]["amount_minor"] == 850000
    )
    assert act(rep, item, "terms/accept").status_code == 409
    assert act(member, item, "terms/accept").status_code == 409
    accepted = act(owner, item, "terms/accept")
    assert accepted.status_code == 200, accepted.data
    assert accepted.data["resource"]["status"] == "awaiting_participants"
    assert not item.participants.filter(invitation__isnull=False).exists()
    item.refresh_from_db()
    old = post(
        rep,
        f"group-booking-proposals/{item.id}/consents/",
        command(
            item.revision,
            decision="accept",
            terms_digest=initial["terms_digest"],
        ),
    )
    assert old.status_code == 409
    # A changed public price neither replaces the negotiated amount nor unit identity.
    inventory = copy.deepcopy(prop.rental_inventory)
    inventory["offers"][0]["revision"] += 1
    inventory["offers"][0]["terms"]["price"] = "12000"
    prop.rental_inventory = inventory
    prop.save(update_fields=["rental_inventory"])
    committed = act(
        rep, item, "consents", decision="accept", terms_digest=item.terms_digest
    )
    assert committed.status_code == 200, committed.data
    first = item.participants.get(tenant=rep)
    second = item.participants.get(tenant=member)
    assert first.invitation_id and not second.invitation_id
    assert (
        first.invitation.terms_proposal.terms["monthly_rent"]["amount_minor"] == 850000
    )
    assert first.invitation.terms_proposal.expires_at == item.deadline
    assert first.invitation.terms_proposal.versions.count() == 1
    assert not Lease.objects.exists() and not PaymentAttempt.objects.exists()
    assert act(rep, item, "terms/edit", participants=rows).status_code == 409
    assert act(owner, item, "terms/withdraw", reason="Changed mind").status_code == 409
    events = PlanningEvent.objects.filter(destination__target_id=str(item.id))
    assert set(
        events.filter(recipient=rep).values_list("destination__workspace", flat=True)
    ) == {"student"}
    assert set(
        events.filter(recipient=owner).values_list("destination__workspace", flat=True)
    ) == {"owner"}
    # The same private terms reach the individual lease and its actual invoice.
    invite = first.invitation
    response = authenticated(rep).post(
        PREFIX + f"tenancy-invitations/{invite.id}/respond/",
        {
            "decision": "accepted",
            "revision": invite.revision,
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert response.status_code == 200, response.data
    lease_result = authenticated(owner).post(
        PREFIX + "leases/",
        {
            "invitation_id": str(invite.id),
            "invitation_revision": response.data["revision"],
            "property_id": str(prop.id),
            "offer_id": first.offer_id,
            "offer_revision": 2,
            "tenant_id": str(rep.id),
            "terms": first.terms,
            "request_key": str(uuid.uuid4()),
            "expected_revision": 0,
        },
        format="json",
    )
    assert lease_result.status_code == 201, lease_result.data
    from core_apps.features.services.rental_phase3 import generate_billing_schedule

    lease = Lease.objects.get(id=lease_result.data["resource"]["id"])
    assert lease.rent_amount_minor == 850000
    assert list(generate_billing_schedule(lease))[0].invoice.amount_minor == 850000
    assert item.participants.get(tenant=member).invitation_id is None


def test_change_request_edit_expiry_and_private_history(rental_participants, policy):
    owner, rep, member, _, _ = rental_participants
    item, source, initial = setup(rental_participants)
    act(owner, item, "submit")
    assert (
        act(
            rep, item, "terms/request-changes", reason="Lower deposit please"
        ).status_code
        == 200
    )
    rows = [
        {"tenant_id": r["tenant_id"], "terms": copy.deepcopy(r["terms"])}
        for r in source["participants"]
    ]
    rows[0]["terms"]["deposit"]["amount_minor"] = 500000
    edited = act(owner, item, "terms/edit", participants=rows)
    assert edited.status_code == 200, edited.data
    assert act(rep, item, "terms/accept").status_code == 200
    private = (
        authenticated(member).get(PREFIX + f"group-booking-proposals/{item.id}/").data
    )
    assert all(
        len(v["participants"]) == 1
        and v["participants"][0]["tenant_id"] == str(member.id)
        for v in private["terms_versions"]
    )
    assert "Lower deposit please" in str(private["history"])
    assert not private["participants"][0]["terms"]
    GroupBookingProposal.objects.filter(pk=item.pk).update(
        deadline=timezone.now() - timedelta(seconds=1)
    )
    item.refresh_from_db()
    assert (
        act(
            member, item, "consents", decision="accept", terms_digest=item.terms_digest
        ).status_code
        == 409
    )
    assert (
        authenticated(rep)
        .get(PREFIX + f"group-booking-proposals/{item.id}/")
        .data["status"]
        == "expired"
    )


@pytest.mark.parametrize("action", ["terms/reject", "terms/withdraw"])
def test_reasoned_terminal_decision_and_lost_response_replay(
    rental_participants, policy, action
):
    owner, rep, *_ = rental_participants
    item, _, _ = setup(rental_participants)
    act(owner, item, "submit")
    assert act(rep, item, action).status_code == 400
    item.refresh_from_db()
    data = command(
        item.revision,
        terms_digest=item.terms_digest,
        reason="The dates no longer suit us",
    )
    url = f"group-booking-proposals/{item.id}/{action}/"
    first = post(rep, url, data)
    assert first.status_code == 200, first.data
    repeated = post(rep, url, data)
    assert repeated.status_code == 200, repeated.data
    assert (
        first.data["operation_receipt"]["id"]
        == repeated.data["operation_receipt"]["id"]
    )
    assert not item.participants.filter(invitation__isnull=False).exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("commission_rate_bps", 50),
        ("termination_policy", {"notice_days": 0}),
        ("occupants", 2),
    ],
)
def test_nonnegotiable_rules_and_capacity_rejected(
    rental_participants, policy, field, value
):
    owner, rep, *_ = rental_participants
    item, source, _ = setup(rental_participants)
    act(owner, item, "submit")
    rows = [
        {"tenant_id": r["tenant_id"], "terms": copy.deepcopy(r["terms"])}
        for r in source["participants"]
    ]
    rows[0]["terms"][field] = value
    assert act(rep, item, "terms/counter", participants=rows).status_code in {400, 409}
    assert GroupBookingTermsVersion.objects.filter(proposal=item).count() == 1


def test_changed_roster_or_ownership_blocks_old_actor(rental_participants, policy):
    owner, rep, member, prop, _ = rental_participants
    item, _, _ = setup(rental_participants)
    act(owner, item, "submit")
    item.group.memberships.filter(user=rep).update(status="left")
    assert act(rep, item, "terms/accept").status_code == 409
    item.group.memberships.filter(user=rep).update(status="active", joined_revision=50)
    assert act(rep, item, "terms/accept").status_code == 409
    prop.owner = member
    prop.save(update_fields=["owner"])
    assert (
        act(owner, item, "terms/withdraw", reason="Not current owner").status_code
        == 409
    )


def test_expiry_preserves_started_independent_invitation_and_emits_once(
    rental_participants, policy
):
    from core_apps.features.services.rental_lifecycle.group_terms import expire_due

    owner, rep, member, *_ = rental_participants
    item, _, _ = setup(rental_participants)
    act(owner, item, "submit")
    act(rep, item, "terms/accept")
    item.refresh_from_db()
    assert (
        act(
            rep, item, "consents", decision="accept", terms_digest=item.terms_digest
        ).status_code
        == 200
    )
    row = item.participants.get(tenant=rep)
    invitation = row.invitation_id
    GroupBookingProposal.objects.filter(pk=item.pk).update(
        deadline=timezone.now() - timedelta(seconds=1)
    )
    assert expire_due() == 1 and expire_due() == 0
    row.refresh_from_db()
    assert row.invitation_id == invitation and row.consent_status == "accepted"
    assert item.participants.get(tenant=member).consent_status == "expired"
    assert (
        PlanningEvent.objects.filter(
            event_key__startswith=f"group_terms_expired:{item.id}:"
        ).count()
        == 3
    )


def test_old_notification_reads_current_history_but_retry_loses_membership(
    rental_participants, policy
):
    from core_apps.features.services.planning_notifications import (
        deliver_planning_events,
    )
    from core_apps.features.services.planning_notifications_parts.event_copy import (
        event_copy,
    )
    from rest_framework.exceptions import NotFound

    owner, rep, *_ = rental_participants
    item, _, _ = setup(rental_participants)
    act(owner, item, "submit")
    event = PlanningEvent.objects.get(
        recipient=rep, destination__target_id=str(item.id)
    )
    act(rep, item, "terms/request-changes", reason="Review the deposit")
    assert event_copy(event)
    assert deliver_planning_events() >= 3
    event.refresh_from_db()
    assert event.notification.scope == "student"
    item.group.memberships.filter(user=rep).update(status="left")
    with pytest.raises(NotFound):
        event_copy(event)


def test_stale_appropriate_action_visible_disabled_but_other_actor_action_hidden(
    rental_participants, policy
):
    owner, rep, member, *_ = rental_participants
    item, _, _ = setup(rental_participants)
    act(owner, item, "submit")
    item.group.roster_revision += 1
    item.group.save()
    response = (
        authenticated(rep).get(PREFIX + f"group-booking-proposals/{item.id}/").data
    )
    assert "accept_group_terms" in response["available_actions"]
    assert "accept_group_terms" not in response["allowed_actions"]
    assert response["blocking_reasons"]
    other = (
        authenticated(member).get(PREFIX + f"group-booking-proposals/{item.id}/").data
    )
    assert "accept_group_terms" not in other["available_actions"]


@pytest.mark.django_db(transaction=True)
def test_concurrent_accept_and_counter_have_one_winner(rental_participants, policy):
    owner, rep, *_ = rental_participants
    item, source, _ = setup(rental_participants)
    act(owner, item, "submit")
    item.refresh_from_db()
    revision, digest = item.revision, item.terms_digest
    rows = [
        {"tenant_id": r["tenant_id"], "terms": copy.deepcopy(r["terms"])}
        for r in source["participants"]
    ]
    rows[0]["terms"]["monthly_rent"]["amount_minor"] = 900000
    barrier = Barrier(2)

    def send(action, extra):
        connections.close_all()
        barrier.wait(timeout=10)
        try:
            return post(
                rep,
                f"group-booking-proposals/{item.id}/terms/{action}/",
                command(
                    revision,
                    terms_digest=digest,
                    **extra,
                ),
            ).status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(send, "accept", {})
        second = pool.submit(send, "counter", {"participants": rows})
        assert sorted([first.result(), second.result()]) == [200, 409]
    assert not GroupBookingParticipant.objects.filter(invitation__isnull=False).exists()
