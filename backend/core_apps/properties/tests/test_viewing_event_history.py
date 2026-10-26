"""Durable viewing events retain identity and current recipient authority."""

# flake8: noqa: F401,F811 -- pytest fixtures are injected by name.
import uuid
from datetime import timedelta
import pytest
from django.utils import timezone
from core_apps.features.planning_models import PlanningEvent
from core_apps.features.company_models import CompanyMembership
from core_apps.features.services.planning_notifications import deliver_planning_events
from core_apps.features.tests.test_rental_phase2 import (
    authenticated,
    rental_participants,
)
from core_apps.features.tests.test_planning_cycles import configured_planning_offer
from core_apps.features.tests.test_group_process_history import reviewed_visit
from core_apps.properties.models import PropertyVisit
from core_apps.properties.services.visit import PropertyVisitService
from core_apps.properties.services.viewing_commands import notify, command
from core_apps.properties.services.viewing_access import context_payload
from .test_contextual_viewings import API, booking, company_for

pytestmark = pytest.mark.django_db


def request_visit(parties, kind="personal"):
    owner, actor, other, prop, _ = parties
    data = booking(prop)
    if kind == "company":
        company, _ = company_for(actor)
        employee = CompanyMembership.objects.create(
            company=company, user=other, is_employee=True
        )
        data = booking(prop, company, employee)
    else:
        data["viewing_context"] = {"kind": kind}
    response = authenticated(actor).post(
        API + f"{prop.id}/visits/",
        data,
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
    )
    assert response.status_code == 201, response.data
    return PropertyVisit.objects.get()


@pytest.mark.parametrize(
    "kind,scope",
    [("personal", "individual"), ("student", "student"), ("company", "company")],
)
def test_request_recipient_scope_is_explicit_and_owner_stays_owner(
    rental_participants, kind, scope
):
    owner, actor, other, _, _ = rental_participants
    visit = request_visit(rental_participants, kind)
    rows = PlanningEvent.objects.filter(destination__visit_id=str(visit.id))
    expected = {owner.pk: "owner", actor.pk: scope}
    if kind == "company":
        expected[other.pk] = scope
    assert {row.recipient_id: row.destination["workspace"] for row in rows} == expected
    assert all(row.destination["target_id"] == str(visit.id) for row in rows)
    deliver_planning_events(event_kinds=["viewing_changed"])
    assert {row.recipient_id: row.notification.scope for row in rows.all()} == expected


def test_old_queued_request_survives_accept_and_cancel_with_current_history(
    rental_participants,
):
    owner, tenant, _, _, _ = rental_participants
    visit = request_visit(rental_participants)
    event = PlanningEvent.objects.get(
        recipient=owner, destination__visit_id=str(visit.id)
    )
    receipt = event.notification_id
    PropertyVisitService.accept_visit(owner, visit)
    PropertyVisitService.update_visit_status(tenant, visit, "canceled")
    visit.refresh_from_db()
    assert visit.revision == 3
    assert [row["to_status"] for row in visit.change_history] == [
        "pending",
        "confirmed",
        "canceled",
    ]
    deliver_planning_events(event_kinds=["viewing_changed"])
    event.refresh_from_db()
    assert event.notification_id == receipt and event.delivered_at is not None
    assert event.delivery_status != "stale_or_unauthorized"
    assert event.notification.data["target_id"] == str(visit.id)
    current = authenticated(tenant).get(API + f"visits/requests/{visit.id}/").data
    assert current["status"] == "canceled"
    assert current["viewing_context"]["history"][-1]["to_status"] == "canceled"
    before = PlanningEvent.objects.count()
    notify(visit, "canceled")
    assert PlanningEvent.objects.count() == before


def test_group_request_notifies_all_consented_participants_after_link(
    rental_participants,
):
    owner, tenant, member, _, _ = rental_participants
    _, process = reviewed_visit(rental_participants)
    rows = PlanningEvent.objects.filter(
        destination__event_kind="viewing_changed",
        destination__visit_id=str(process.visit.id),
    )
    assert {row.recipient_id: row.destination["workspace"] for row in rows} == {
        owner.pk: "owner",
        tenant.pk: "student",
        member.pk: "student",
    }


def test_reassigned_attendee_cannot_receive_old_event_or_private_identifiers(
    rental_participants,
):
    owner, coordinator, former, _, _ = rental_participants
    visit = request_visit(rental_participants, "company")
    event = PlanningEvent.objects.get(
        recipient=former, destination__visit_id=str(visit.id)
    )
    membership = visit.company.memberships.get(user=coordinator)
    command(
        coordinator,
        visit.id,
        {
            "expected_revision": visit.revision,
            "action": "reassign",
            "representative_membership_id": membership.id,
        },
    )
    deliver_planning_events(event_kinds=["viewing_changed"])
    event.refresh_from_db()
    assert (
        event.delivery_status == "stale_or_unauthorized"
        and event.notification_id is None
    )
    visit.refresh_from_db()
    assert visit.change_history[-1]["changed_fields"] == ["tenant_id"]
    assert str(former.id) not in str(context_payload(visit, coordinator)["history"])


def test_stale_partial_save_preserves_intervening_status_and_history(
    rental_participants,
):
    owner, _, _, _, _ = rental_participants
    stale = request_visit(rental_participants)
    PropertyVisitService.accept_visit(owner, stale)
    stale.visit_date = timezone.localdate() + timedelta(days=4)
    stale.save(update_fields=["visit_date", "updated_at"])
    stale.refresh_from_db()
    assert stale.status == "confirmed" and stale.revision == 3
    assert len(stale.change_history) == 3
    assert stale.change_history[-1]["to_status"] == "confirmed"
    assert stale.change_history[-1]["changed_fields"] == ["visit_date"]
