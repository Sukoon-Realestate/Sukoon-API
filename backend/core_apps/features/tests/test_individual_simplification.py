"""Ordinary rental guidance: real DB and authorization, without live providers."""

# flake8: noqa: F811 -- imported pytest fixtures are injected by name.

from datetime import timedelta
import uuid
import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from core_apps.properties.models import Property, PropertyVisit, OwnerAvailabilitySlot
from core_apps.properties.filters import PropertyFilter
from core_apps.features.models import (
    FinalSettlement,
    RentalInterest,
    TermsProposal,
    TenancyInvitation,
    PrivateAccessRevocation,
    RentalInventoryDayLock,
    RentalInventoryUnit,
)
from core_apps.features.services.rental_lifecycle.journey import (
    lease_journey,
    participant_reasons,
    application_journey,
)
from .test_rental_phase2 import rental_participants
from .test_rental_phase6 import phase6_lease, client_for, captured_payment

pytestmark = pytest.mark.django_db


def test_ordinary_budget_is_offer_total_not_per_person(rental_participants):
    _, _, _, prop, _ = rental_participants
    prop.price = 1
    prop.save(update_fields=["price"])
    args = {"rental_search_version": "1", "price_period": "monthly", "occupants": 2}
    assert not PropertyFilter(
        {**args, "price_max": 6000}, queryset=Property.objects.all()
    ).qs.exists()
    assert PropertyFilter(
        {**args, "price_max": 10000}, queryset=Property.objects.all()
    ).qs.exists()
    response = APIClient().get(reverse("property-list"), args)
    assert response.status_code == 200
    assert response.data["rental_search_version"] == 1


@pytest.mark.parametrize(
    "extra",
    [
        {"available_from": "2030-01-01"},
        {"available_from": "2030-01-01", "available_until": "2029-12-31"},
        {"occupants": 0},
        {"occupants": 21},
        {"rental_search_version": 2},
        {"student_search": "true"},
    ],
)
def test_invalid_stay_context_is_not_silently_ignored(rental_participants, extra):
    response = APIClient().get(
        reverse("property-list"), {"rental_search_version": 1, **extra}
    )
    assert response.status_code == 400, response.data


def test_stay_search_checks_half_open_inventory_without_reserving(rental_participants):
    _, _, _, prop, _ = rental_participants
    start = timezone.localdate() + timedelta(days=10)
    end = start + timedelta(days=40)
    args = {
        "rental_search_version": "1",
        "available_from": str(start),
        "available_until": str(end),
    }
    unit = RentalInventoryUnit.objects.create(
        property=prop, physical_key=f"property:{prop.id}", topology_digest="test"
    )
    RentalInventoryDayLock.objects.create(
        property=prop, unit=unit, stay_on=end, kind="occupied"
    )
    assert PropertyFilter(args, queryset=Property.objects.all()).qs.exists()
    RentalInventoryDayLock.objects.update(stay_on=start)
    assert not PropertyFilter(args, queryset=Property.objects.all()).qs.exists()
    assert RentalInventoryDayLock.objects.count() == 1


def test_visit_discloses_only_reviewed_stay_and_replay_preserves_it(
    rental_participants,
):
    owner, tenant, stranger, prop, offer = rental_participants
    day = timezone.localdate() + timedelta(days=3)
    OwnerAvailabilitySlot.objects.create(
        property=prop, owner=owner, date=day, time="14:00", is_enabled=True
    )
    stay = {
        "starts_on": str(day + timedelta(days=5)),
        "ends_on_exclusive": str(day + timedelta(days=45)),
        "occupants": 1,
    }
    body = {
        "visit_date": str(day),
        "visit_time": "14:00",
        "offer_id": offer,
        "expected_offer_revision": prop.rental_inventory["offers"][0]["revision"],
        "request_key": str(uuid.uuid4()),
        "stay_preferences": stay,
    }
    path = reverse("property-visit-create", kwargs={"property_id": prop.id})
    client = client_for(tenant)
    client.credentials(HTTP_IDEMPOTENCY_KEY=body["request_key"])
    rejected = client.post(
        path, {**body, "stay_preferences": {**stay, "budget": 999}}, format="json"
    )
    assert rejected.status_code == 400, rejected.data
    response = client.post(path, body, format="json")
    assert response.status_code == 201, response.data
    visit = PropertyVisit.objects.get(tenant=tenant)
    assert visit.stay_preferences == stay
    replay = client.post(path, body, format="json")
    assert replay.status_code in {200, 201}, replay.data
    assert PropertyVisit.objects.filter(tenant=tenant).count() == 1
    detail = reverse("owner-visit-request-detail", kwargs={"id": visit.id})
    assert client_for(owner).get(detail).data["stay_preferences"] == stay
    assert client_for(stranger).get(detail).status_code in {403, 404}


def test_journey_get_does_not_create_settlement_or_close_lease(phase6_lease):
    owner, tenant, lease = phase6_lease
    before = lease.revision
    response = client_for(tenant).get(
        f"/api/v1/features/v1/leases/{lease.id}/rental-center/"
    )
    assert response.status_code == 200, response.data
    summary = response.data["journey_summary"]
    assert summary["stage"] == "closure"
    assert not summary["complete"]
    assert next(x for x in summary["closure_items"] if x["code"] == "settlement")[
        "blocked"
    ]
    assert not FinalSettlement.objects.filter(lease=lease).exists()
    lease.refresh_from_db()
    assert lease.revision == before
    assert response["Cache-Control"] == "private, no-store"


def test_unknown_payment_precedes_signing_and_owner_gets_no_pay_action(phase6_lease):
    owner, tenant, lease = phase6_lease
    _, attempt, _ = captured_payment(lease, tenant)
    attempt.payment_status = "pending"
    attempt.save(update_fields=["payment_status"])
    lease.status = "pending_signatures"
    lease.save(update_fields=["status"])
    for actor in (owner, tenant):
        summary = lease_journey(lease, actor)
        assert summary["stage"] == "payment_reconciliation"
        assert summary["next_actor"] == "provider"
        assert summary["next_action"]["action"] == "reconcile_payment"
    assert not any("pay" == x for x in lease_journey(lease, owner)["allowed_actions"])


def test_closed_projection_cannot_hide_actual_open_obligations(phase6_lease):
    owner, tenant, lease = phase6_lease
    lease.financial_closure_status = "closed"
    lease.save(update_fields=["financial_closure_status"])
    assert not lease_journey(lease, tenant)["complete"]  # missing accepted settlement
    current = client_for(tenant).get(
        "/api/v1/features/v1/leases/",
        {"workspace": "tenant", "housing_bucket": "current"},
    )
    assert current.status_code == 200, current.data
    assert current.data["housing_bucket_version"] == 1
    assert str(lease.id) in str(current.data)
    history = client_for(tenant).get(
        "/api/v1/features/v1/leases/",
        {"workspace": "tenant", "housing_bucket": "history"},
    )
    assert str(lease.id) not in str(history.data)


def test_tenant_financial_wait_does_not_reveal_owner_recovery_details(phase6_lease):
    owner, tenant, lease = phase6_lease
    reasons = [
        "An owner payable or payout is unresolved.",
        "Owner funds must be recovered after a refunded payout.",
    ]
    assert participant_reasons(lease, tenant, reasons) == [
        "Financial processing remains open."
    ]
    assert participant_reasons(lease, owner, reasons) == reasons


def test_revoked_private_access_cannot_reenter_through_housing_or_application(
    phase6_lease,
):
    owner, tenant, lease = phase6_lease
    interest = RentalInterest.objects.create(
        property=lease.property,
        tenant=tenant,
        offer_id=lease.offer_id,
        offer_revision=1,
        offer_snapshot={},
        desired_start=lease.start_date,
        months=1,
    )
    TenancyInvitation.objects.create(
        property=lease.property,
        owner=owner,
        tenant=tenant,
        initiated_by=owner,
        interest=interest,
        lease=lease,
        status="accepted",
        expires_at=timezone.now() + timedelta(days=1),
    )
    PrivateAccessRevocation.objects.create(lease=lease, user=tenant, reason="Revoked")
    client = client_for(tenant)
    path = "/api/v1/features/v1/leases/"
    for bucket in ("current", "history"):
        response = client.get(path, {"workspace": "tenant", "housing_bucket": bucket})
        assert response.status_code == 200
        assert str(lease.id) not in str(response.data)
    assert client.get(f"{path}{lease.id}/").status_code == 404
    assert client.get(f"{path}{lease.id}/rental-center/").status_code == 404
    assert client.get(f"/api/v1/features/v1/deals/{interest.id}/").status_code == 404
    assert client_for(owner).get(f"{path}{lease.id}/rental-center/").status_code == 200


@pytest.mark.parametrize(
    "state,stage,actor",
    [
        ("draft", "agreement", "self"),
        ("pending_signatures", "agreement", "provider"),
        ("signed", "activation", "provider"),
        ("expired", "expired", "operator"),
        ("active", "handover", "provider"),
    ],
)
def test_provider_disabled_guidance_is_not_false_completion(
    phase6_lease, settings, state, stage, actor
):
    settings.RENTAL_PROVIDER_BACKEND = "disabled"
    settings.RENTAL_FAKE_PROVIDER_ALLOWED = False
    owner, tenant, lease = phase6_lease
    lease.status = state
    lease.occupancy_status = "not_started"
    lease.save(update_fields=["status", "occupancy_status"])
    lease.handovers.all().delete()
    for user in (owner, tenant):
        summary = lease_journey(lease, user)
        assert summary["stage"] == stage
        expected = (
            ("owner" if user == owner else "tenant") if actor == "self" else actor
        )
        assert summary["next_actor"] == expected
        assert not summary["complete"]
        assert summary["next_action"]["kind"] in {"lease_review", "handovers"}


def test_clean_cancelled_closure_enters_history_without_creating_settlement(
    phase6_lease,
):
    _, tenant, lease = phase6_lease
    lease.status = "cancelled"
    lease.occupancy_status = "not_started"
    lease.financial_closure_status = "closed"
    lease.save(update_fields=["status", "occupancy_status", "financial_closure_status"])
    assert lease_journey(lease, tenant)["complete"]
    client = client_for(tenant)
    path = "/api/v1/features/v1/leases/"
    history = client.get(path, {"workspace": "tenant", "housing_bucket": "history"})
    current = client.get(path, {"workspace": "tenant", "housing_bucket": "current"})
    assert str(lease.id) in str(history.data)
    assert str(lease.id) not in str(current.data)
    assert not FinalSettlement.objects.filter(lease=lease).exists()


def test_period_search_and_authority_filters_remain_effective(
    phase6_lease, rental_participants
):
    owner, tenant, lease = phase6_lease
    _, _, stranger, _, _ = rental_participants
    client = client_for(tenant)
    path = "/api/v1/features/v1/leases/"
    assert str(lease.id) in str(
        client.get(path, {"workspace": "tenant", "period": "ended"}).data
    )
    assert str(lease.id) in str(
        client.get(path, {"workspace": "tenant", "period": "pending_settlement"}).data
    )
    assert str(lease.id) not in str(
        client.get(path, {"workspace": "tenant", "period": "current"}).data
    )
    assert str(lease.id) not in str(
        client.get(path, {"workspace": "tenant", "search": "another home"}).data
    )
    assert (
        client.get(path, {"workspace": "tenant", "period": "invalid"}).status_code
        == 400
    )
    assert (
        client.get(
            path, {"workspace": "tenant", "housing_bucket": "invalid"}
        ).status_code
        == 400
    )
    assert str(lease.id) not in str(
        client_for(stranger)
        .get(path, {"workspace": "tenant", "housing_bucket": "current"})
        .data
    )
    assert (
        client_for(stranger).get(f"{path}{lease.id}/rental-center/").status_code == 404
    )
    lease.status = "active"
    lease.start_date = timezone.localdate()
    lease.end_date = timezone.localdate() + timedelta(days=30)
    lease.save(update_fields=["status", "start_date", "end_date"])
    assert str(lease.id) in str(
        client.get(path, {"workspace": "tenant", "period": "current"}).data
    )
    lease.start_date += timedelta(days=1)
    lease.save(update_fields=["start_date"])
    assert str(lease.id) in str(
        client_for(owner).get(path, {"workspace": "owner", "period": "upcoming"}).data
    )


def test_proposal_and_invitation_guidance_uses_effective_state_without_mutation(
    rental_participants, settings
):
    owner, tenant, _, prop, offer = rental_participants
    settings.RENTAL_PROVIDER_BACKEND = "disabled"
    settings.RENTAL_FAKE_PROVIDER_ALLOWED = False
    interest = RentalInterest.objects.create(
        property=prop,
        tenant=tenant,
        offer_id=offer,
        offer_revision=2,
        offer_snapshot={},
        desired_start=timezone.localdate(),
        months=1,
    )
    proposal = TermsProposal.objects.create(
        interest=interest,
        owner=owner,
        terms={},
        offer_snapshot={},
        status="accepted",
        accepted_by=[str(owner.id), str(tenant.id)],
    )
    for user in (owner, tenant):
        assert (
            application_journey(interest, proposal, None, user)["next_actor"]
            == "provider"
        )
    proposal.status = "rejected"
    proposal.save(update_fields=["status"])
    summary = application_journey(interest, proposal, None, tenant)
    assert summary["stage"] == "application"
    assert summary["next_actor"] == "owner"
    invitation = TenancyInvitation.objects.create(
        property=prop,
        owner=owner,
        tenant=tenant,
        initiated_by=owner,
        interest=interest,
        terms_proposal=proposal,
        offer_id=offer,
        expires_at=timezone.now() - timedelta(seconds=1),
    )
    summary = application_journey(interest, proposal, invitation, tenant)
    assert summary["stage"] == "stopped" and summary["next_action"] is None
    invitation.refresh_from_db()
    assert invitation.status == "pending"
