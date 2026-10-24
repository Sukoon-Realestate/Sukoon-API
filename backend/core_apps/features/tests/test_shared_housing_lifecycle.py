"""Local canonical API integration using the configured test-only fake provider."""

import pytest
from .test_shared_housing import pair, accepted, proposal_act, post, API
from .test_rental_phase2 import rental_participants, authenticated
from .test_funded_settlement import command
from core_apps.features.shared_housing_models import SharedHousingAllocation
from core_apps.features.models import Lease, PaymentAttempt

pytestmark = pytest.mark.django_db


def handoff(pair):
    owner, first, second, _, _ = pair
    plan = accepted(pair)
    for user in [first, second]:
        plan = proposal_act(user, plan, "consent_terms", independent_consent=True)
    return proposal_act(owner, plan, "send_invitations")


def create_lease(row):
    invitation = row.invitation
    owner, tenant = invitation.owner, row.tenant
    result = post(
        tenant,
        f"tenancy-invitations/{invitation.id}/respond/",
        {**command(decision="accepted"), "revision": invitation.revision},
    )
    lease = post(
        owner,
        "leases/",
        command(
            invitation_id=str(invitation.id),
            invitation_revision=result["revision"],
            property_id=str(invitation.property.id),
            tenant_id=str(tenant.id),
            offer_id=str(invitation.offer_id),
            offer_revision=row.selection["offer_revision"],
            terms=row.terms.terms,
        ),
        201,
    )
    return lease


def finish_rental(row, lease):
    owner, tenant = row.invitation.owner, row.tenant
    for user in [owner, tenant]:
        lease = post(
            user,
            f"leases/{lease['id']}/review/",
            command(lease["revision"], decision="accept_review"),
        )
    lease = post(
        owner,
        f"leases/{lease['id']}/submit-for-signature/",
        command(lease["revision"], decision="submit_for_signature"),
    )
    sessions = []
    for user in [owner, tenant]:
        session = post(
            user,
            f"leases/{lease['id']}/signing-session/",
            command(
                lease["revision"],
                document_id=lease["document_id"],
                document_hash=lease["document_hash"],
            ),
            201,
        )
        sessions.append((user, session["session_id"]))
    for user, sid in sessions:
        post(
            user,
            f"mock-provider/signing-sessions/{sid}/complete/",
            command(lease["revision"]),
        )
    record = Lease.objects.get(id=lease["id"])
    invoice = record.invoices.get()
    quote = post(
        tenant,
        f"rent-invoices/{invoice.id}/quote/",
        command(invoice.revision, decision="quote"),
        201,
    )
    checkout = post(
        tenant,
        f"rent-invoices/{invoice.id}/checkout/",
        command(
            invoice.revision, invoice_id=str(invoice.id), quote_id=quote["quote_id"]
        ),
        201,
    )
    attempt = PaymentAttempt.objects.get(id=checkout["payment_attempt_id"])
    captured = post(
        tenant,
        f"mock-provider/payment-attempts/{attempt.id}/events/",
        command(attempt.revision, event="captured"),
    )
    post(
        tenant,
        f"mock-provider/payment-attempts/{attempt.id}/events/",
        command(captured["revision"], event="settled"),
    )
    handover = post(
        owner,
        f"leases/{record.id}/handovers/",
        command(
            kind="move_in",
            possession_on=str(record.start_date),
            condition={"summary": "good"},
            keys={"count": 2},
            meters={},
            inventory=[],
            evidence_ids=[],
        ),
        201,
    )
    for user in [owner, tenant]:
        handover = post(
            user,
            f"handovers/{handover['id']}/respond/",
            command(handover["revision"], decision="accept"),
        )
    record.refresh_from_db()
    assert record.status == "active" and record.occupancy_status == "occupied"
    return record


def test_both_finish_canonical_independent_contract_payment_and_handover(pair):
    plan = handoff(pair)
    records = []
    for tenant in pair[1:3]:
        row = SharedHousingAllocation.objects.select_related("invitation", "terms").get(
            tenant=tenant
        )
        records.append(finish_rental(row, create_lease(row)))
    assert records[0].id != records[1].id
    assert not set(
        records[0].inventory_day_locks.values_list("unit_id", flat=True)
    ) & set(records[1].inventory_day_locks.values_list("unit_id", flat=True))
    result = (
        authenticated(pair[1]).get(API + f"shared-housing-plans/{plan['id']}/").data
    )
    assert result["status"] == "completed"
    assert all(
        a["progress"] == "received" for a in result["proposals"][0]["allocations"]
    )
    # Completing together does not grant access to the partner's agreement.
    assert (
        authenticated(pair[1]).get(API + f"leases/{records[1].id}/").status_code == 404
    )


def test_other_invitation_decline_does_not_change_existing_lease(pair):
    plan = handoff(pair)
    first = SharedHousingAllocation.objects.select_related("invitation", "terms").get(
        tenant=pair[1]
    )
    second = SharedHousingAllocation.objects.select_related("invitation", "terms").get(
        tenant=pair[2]
    )
    lease = create_lease(first)
    original_terms = Lease.objects.get(id=lease["id"]).terms
    post(
        pair[2],
        f"tenancy-invitations/{second.invitation.id}/respond/",
        {**command(decision="rejected"), "revision": second.invitation.revision},
    )
    record = Lease.objects.get(id=lease["id"])
    assert record.status == lease["status"]
    assert record.terms == original_terms
    result = (
        authenticated(pair[1]).get(API + f"shared-housing-plans/{plan['id']}/").data
    )
    assert result["status"] == "partial"
