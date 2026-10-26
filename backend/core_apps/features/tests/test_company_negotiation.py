"""Corporate private terms pass through existing independent approvals and contracts."""

# flake8: noqa: F401,F811
import copy
import uuid
from datetime import timedelta
import pytest
from django.utils import timezone
from rest_framework.exceptions import NotFound
from .test_company_contract_preparation import (
    cycle,
    company_setup,
    rental_participants,
    policy,
    command,
    authenticated,
    API,
    create as prepare,
    respond,
    person,
)
from core_apps.features.models import (
    CompanyTermsNegotiation,
    CompanyBudgetReservation,
    Lease,
    RentalInventoryDayLock,
)
from core_apps.features.services.company import bookings, approval_routing, negotiation
from core_apps.features.services.company.negotiation_projection import authorize
from core_apps.features.planning_models import PlanningEvent

pytestmark = pytest.mark.django_db


def start(cycle):
    item = cycle["item"]
    s = item.snapshot
    terms = {
        "monthly_rent_minor": s["monthly_rent"]["amount_minor"] - 1000,
        "deposit_minor": 0,
        "starts_on": s["starts_on"],
        "ends_on_exclusive": s["ends_on_exclusive"],
        "occupants": 2,
        "included_services": ["Agreed cleaning"],
        "excluded_services": ["Electricity"],
    }
    body = command(
        expected_revision=item.revision,
        terms=terms,
        expires_at=(timezone.now() + timedelta(hours=12)).isoformat(),
    )
    path = API + f"company-booking-items/{item.id}/negotiation/"
    result = authenticated(cycle["coordinator"]).post(path, body, format="json")
    assert result.status_code == 201, result.data
    return CompanyTermsNegotiation.objects.get(booking=item), body, path


def act(cycle, item, who, action, **extra):
    item.refresh_from_db()
    return authenticated(cycle[who]).post(
        API + f"company-terms-negotiations/{item.id}/{action}/",
        command(
            expected_revision=item.revision, terms_digest=item.terms_digest, **extra
        ),
        format="json",
    )


def reapprove(cycle):
    item = cycle["item"]
    item.refresh_from_db()
    item = approval_routing.submit(
        cycle["coordinator"], item.id, {"expected_revision": item.revision}
    )
    item = bookings.decide(
        cycle["approver"],
        item.id,
        {
            "expected_revision": item.revision,
            "snapshot_digest": item.snapshot_digest,
            "decision": "approved",
        },
    )
    cycle["item"] = item
    cycle["body"] = {
        **cycle["body"],
        "expected_revision": item.revision,
        "request_key": str(uuid.uuid4()),
    }
    return item


def test_counter_invalidates_budget_without_holding_and_reaches_same_contract(cycle):
    item, body, path = start(cycle)
    previous = cycle["item"].approvals.get()
    assert CompanyBudgetReservation.objects.get(approval=previous).status == "released"
    assert not RentalInventoryDayLock.objects.exists() and not Lease.objects.exists()
    assert authenticated(cycle["coordinator"]).post(path, body, format="json").data[
        "resource"
    ]["id"] == str(item.id)
    assert act(cycle, item, "coordinator", "accept").status_code == 403
    terms = {
        **item.terms,
        "monthly_rent_minor": item.terms["monthly_rent_minor"] - 1000,
    }
    counter = act(cycle, item, "owner", "counter", terms=terms)
    assert counter.status_code == 200, counter.data
    item.refresh_from_db()
    assert item.content_revision == 2 and item.versions.count() == 2
    assert item.expires_at.isoformat() == body["expires_at"]
    assert act(cycle, item, "coordinator", "accept").status_code == 200
    assert not RentalInventoryDayLock.objects.exists() and not Lease.objects.exists()
    booking = reapprove(cycle)
    assert booking.approvals.count() == 2
    assert (
        previous.snapshot["monthly_rent"]["amount_minor"]
        != booking.snapshot["monthly_rent"]["amount_minor"]
    )
    # Public price edits do not rewrite or invalidate the accepted private terms.
    booking.offer.monthly_rent_minor += 50000
    booking.offer.revision += 1
    booking.offer.save()
    reviewer = person("negotiation-execution-reviewer")
    reviewer.is_staff = reviewer.is_superuser = True
    reviewer.save()
    for mandate in cycle["mandates"]:
        response = authenticated(reviewer).post(
            API + f"company-mandates/{mandate.id}/execution-review/",
            command(
                expected_revision=mandate.revision,
                evidence_reference="synthetic-negotiation-evidence",
                verified_until=(timezone.now() + timedelta(days=20)).isoformat(),
                reason="Synthetic authority review",
            ),
            format="json",
        )
        assert response.status_code == 200, response.data
    prep = prepare(cycle)
    assert (
        prep.snapshot["inventory"]["monthly_rent"]["amount_minor"]
        == terms["monthly_rent_minor"]
    )
    for who in ["owner", "signer", "payer", "employee", "colleague"]:
        result = respond(cycle, prep, who)
        assert result.status_code == 200, result.data
    prep.refresh_from_db()
    result = authenticated(cycle["coordinator"]).post(
        API + f"company-contract-preparations/{prep.id}/reserve/",
        command(expected_revision=prep.revision),
        format="json",
    )
    assert result.status_code == 200, result.data
    item.refresh_from_db()
    assert item.followed_at is not None
    assert act(cycle, item, "owner", "withdraw", reason="Too late").status_code == 409
    prep.refresh_from_db()
    result = authenticated(cycle["coordinator"]).post(
        API + f"company-contract-preparations/{prep.id}/agreement/",
        command(expected_revision=prep.revision),
        format="json",
    )
    assert result.status_code == 201, result.data
    lease = Lease.objects.get(renter_company=cycle["company"])
    assert lease.rent_amount_minor == terms["monthly_rent_minor"]
    assert lease.terms["portfolio"]["negotiation"]["digest"] == item.terms_digest
    from core_apps.features.services.rental_phase3 import generate_billing_schedule

    assert (
        list(generate_billing_schedule(lease))[0].invoice.amount_minor
        == terms["monthly_rent_minor"]
    )
    assert lease.terms["portfolio"]["included_services"] == terms["included_services"]


def test_reviewer_privacy_authority_expiry_and_original_notification(cycle):
    item, _, _ = start(cycle)
    path = API + f"company-terms-negotiations/{item.id}/"
    assert authenticated(cycle["employee"]).get(path).status_code == 404
    owner = authenticated(cycle["owner"]).get(path)
    assert owner["Cache-Control"] == "private, no-store"
    assert "planned_staff" not in str(owner.data) and "occupant_ids" not in str(
        owner.data
    )
    assert owner.data["workspace"] == "owner"
    assert act(cycle, item, "approver", "accept").status_code == 403
    notice = PlanningEvent.objects.get(
        recipient=cycle["owner"], destination__target_id=str(item.id)
    )
    assert (
        act(
            cycle, item, "owner", "request-changes", reason="Review services"
        ).status_code
        == 200
    )
    assert authorize(notice)  # Old notice opens current state.
    from core_apps.features.services.planning_notifications import (
        deliver_planning_events,
    )

    assert deliver_planning_events(event_kinds=["company_terms_updated"]) > 0
    notice.refresh_from_db()
    assert notice.notification_id and notice.notification.scope == "owner"
    assert (
        act(
            cycle, item, "coordinator", "edit", terms={**item.terms, "commission": 0}
        ).status_code
        == 400
    )
    item.expires_at = timezone.now() - timedelta(seconds=1)
    item.save(update_fields=["expires_at"])
    assert act(cycle, item, "owner", "accept").status_code == 409
    assert negotiation.expire_due() == 1 and negotiation.expire_due() == 0
    item.refresh_from_db()
    assert item.status == "expired" and item.booking.status == "withdrawn"
    member = cycle["company"].memberships.get(user=cycle["coordinator"])
    member.is_active = False
    member.save()
    assert authenticated(cycle["coordinator"]).get(path).status_code == 404
    assert (
        authenticated(cycle["coordinator"])
        .get(API + "company-terms-negotiations/", {"workspace": "company"})
        .data["results"]
        == []
    )


def test_inventory_change_cannot_reuse_private_acceptance(cycle):
    item, _, _ = start(cycle)
    assert act(cycle, item, "owner", "accept").status_code == 200
    unit = cycle["units"][0]
    unit.occupancy_capacity += 1
    unit.save()
    item.refresh_from_db()
    result = authenticated(cycle["coordinator"]).get(
        API + f"company-terms-negotiations/{item.id}/"
    )
    assert "offer_changed" in result.data["blocking_reasons"]
    assert result.data["allowed_actions"] == ["withdraw"]
    booking = cycle["item"]
    booking.refresh_from_db()
    result = authenticated(cycle["coordinator"]).post(
        API + f"company-booking-items/{booking.id}/submit/",
        command(expected_revision=booking.revision),
        format="json",
    )
    assert result.status_code == 409, result.data


@pytest.mark.django_db(transaction=True)
def test_two_decisions_cannot_accept_different_versions(cycle):
    from .test_cycle_concurrency import parallel_calls

    item, _, _ = start(cycle)
    terms = copy.deepcopy(item.terms)
    body = command(expected_revision=item.revision, terms_digest=item.terms_digest)

    def call(index):
        action = "accept" if index == 0 else "counter"
        values = {**body, "request_key": str(uuid.uuid4())}
        if index:
            values["terms"] = terms
        return authenticated(cycle["owner"]).post(
            API + f"company-terms-negotiations/{item.id}/{action}/",
            values,
            format="json",
        )

    results = parallel_calls(call)
    assert sorted(r.status_code for r in results) == [200, 409]
