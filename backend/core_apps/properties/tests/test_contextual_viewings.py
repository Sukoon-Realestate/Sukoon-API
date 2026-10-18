"""A12 source-backed appointments; no provider or native-device claims."""

import uuid
from datetime import timedelta, time
import pytest
from django.utils import timezone
from core_apps.features.company_models import Company, CompanyMembership
from core_apps.features.planning_models import (
    HousingGroup,
    GroupMembership,
    GroupProcess,
)
from core_apps.features.models import (
    Lease,
    ReservationHold,
    RentInvoice,
    TenancyInvitation,
)
from core_apps.features.tests.test_rental_phase2 import (
    rental_participants,
    authenticated,
)
from core_apps.features.tests.test_cycle_concurrency import parallel_calls
from core_apps.properties.models import PropertyVisit, OwnerAvailabilitySlot
from core_apps.properties.services.viewing_access import participant
from core_apps.properties.services.viewing_commands import command
from core_apps.properties.services.post_visit_decision import (
    submit_decision,
    visit_context,
)
from core_apps.properties.phone_disclosure import is_phone_disclosed
from .test_post_visit_decision import visit, path, body, invite_body

pytestmark = pytest.mark.django_db
API = "/api/v1/properties/"


def company_for(user, representative=None):
    company = Company.objects.create(
        name="Synthetic company",
        registration_number="LOCAL-ONLY",
        contact_email="synthetic@example.com",
        review_status="verified",
    )
    coordinator = CompanyMembership.objects.create(
        company=company, user=user, is_active=True, is_coordinator=True
    )
    return company, coordinator


def booking(prop, company=None, member=None):
    date = timezone.localdate() + timedelta(days=2)
    OwnerAvailabilitySlot.objects.get_or_create(
        property=prop, owner=prop.owner, date=date, time=time(13)
    )
    offer = prop.rental_inventory["offers"][0]
    data = {
        "visit_date": str(date),
        "visit_time": "13:00:00",
        "offer_id": offer["id"],
        "expected_offer_revision": offer["revision"],
        "note": "",
    }
    if company:
        data["viewing_context"] = {
            "kind": "company",
            "company_id": str(company.id),
            "representative_membership_id": str(member.id),
        }
    return data


def test_solo_student_books_without_a_group_or_company(rental_participants):
    _, student, _, prop, _ = rental_participants
    payload = {**booking(prop), "viewing_context": {"kind": "student"}}
    response = authenticated(student).post(
        API + f"{prop.id}/visits/",
        payload,
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
    )
    assert response.status_code == 201, response.data
    visit = PropertyVisit.objects.get()
    assert visit.context_kind == "student" and visit.status == "pending"
    assert visit.tenant == student and visit.company_id is None
    assert not GroupProcess.objects.exists()
    assert not Lease.objects.exists() and not ReservationHold.objects.exists()


def test_company_books_without_simulator_budget_or_personal_obligation_and_recovers(
    rental_participants,
):
    owner, actor, other, prop, _ = rental_participants
    company, member = company_for(actor)
    payload = booking(prop, company, member)
    key = str(uuid.uuid4())
    client = authenticated(actor)
    response = client.post(
        API + f"{prop.id}/visits/", payload, format="json", HTTP_IDEMPOTENCY_KEY=key
    )
    assert response.status_code == 201, response.data
    appointment = PropertyVisit.objects.get()
    assert appointment.company == company and appointment.requested_by == actor
    assert (
        not Lease.objects.exists()
        and not ReservationHold.objects.exists()
        and not RentInvoice.objects.exists()
    )
    recovered = client.get(API + "visits/creation-receipt/", {"request_key": key})
    assert recovered.status_code == 200 and recovered.data["visit"]["id"] == str(
        appointment.id
    )
    assert recovered.data["visit"]["viewing_context"]["contract_party"] == "company"
    assert (
        client.post(
            API + f"{prop.id}/visits/", payload, format="json", HTTP_IDEMPOTENCY_KEY=key
        ).status_code
        == 201
    )
    assert PropertyVisit.objects.count() == 1


def test_employee_cannot_book_on_company_behalf_and_revoked_representative_loses_access(
    rental_participants, visit
):
    owner, actor, other, prop, _ = rental_participants
    company, coordinator = company_for(actor)
    employee = CompanyMembership.objects.create(
        company=company, user=other, is_employee=True
    )
    rejected = authenticated(other).post(
        API + f"{prop.id}/visits/",
        booking(prop, company, employee),
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
    )
    assert rejected.status_code == 403
    visit.company, visit.context_kind, visit.tenant = company, "company", other
    visit.save()
    assert authenticated(other).get(path(visit)).status_code == 200
    employee.is_active = False
    employee.save()
    assert authenticated(other).get(path(visit)).status_code == 404
    assert (
        authenticated(other).post(path(visit), body(visit), format="json").status_code
        == 404
    )
    assert not is_phone_disclosed(other, owner, visit=visit)
    assert authenticated(actor).get(path(visit)).status_code == 200
    assert (
        authenticated(actor).post(path(visit), body(visit), format="json").status_code
        == 404
    )


def test_company_proceed_cannot_become_a_personal_invitation(
    rental_participants, visit
):
    owner, actor, other, prop, _ = rental_participants
    company, member = company_for(actor)
    visit.company, visit.context_kind = company, "company"
    visit.save()
    response = authenticated(actor).post(path(visit), body(visit), format="json")
    assert response.status_code == 200
    visit.refresh_from_db()
    assert (
        response.data["rental_continuation"]["blocked_reason"]
        == "corporate_contract_policy_required"
    )
    denied = authenticated(owner).post(
        "/api/v1/features/v1/tenancy-invitations/", invite_body(visit), format="json"
    )
    assert denied.status_code == 409 and not TenancyInvitation.objects.exists()


def test_one_group_appointment_records_each_attendee_independently(
    rental_participants, visit
):
    owner, actor, other, prop, _ = rental_participants
    group = HousingGroup.objects.create(name="Synthetic group")
    for user in [actor, other]:
        GroupMembership.objects.create(
            group=group,
            user=user,
            status="active",
            role="admin" if user == actor else "member",
        )
    process = GroupProcess.objects.create(
        group=group,
        initiated_by=actor,
        property=prop,
        kind="visit",
        roster_revision=1,
        participant_ids=[str(actor.id), str(other.id)],
        consented_ids=[str(actor.id), str(other.id)],
        visit=visit,
        status="submitted",
    )
    assert (
        authenticated(other).get(API + f"visits/requests/{visit.id}/").status_code
        == 200
    )
    first = authenticated(actor).post(path(visit), body(visit), format="json")
    assert first.status_code == 200
    visit.refresh_from_db()
    second = authenticated(other).post(
        path(visit),
        body(visit, decision="decline", reason="Private personal reason"),
        format="json",
    )
    assert second.status_code == 200 and visit.participant_decisions.count() == 2
    assert PropertyVisit.objects.count() == 1
    own = authenticated(actor).get(path(visit)).data
    owner_read = authenticated(owner).get(path(visit)).data
    assert "Private personal reason" not in str(
        own
    ) and "Private personal reason" not in str(owner_read)
    assert own["post_visit_decision"]["value"] == "proceed"
    assert {row["decision"] for row in owner_read["viewing_context"]["attendees"]} == {
        "proceed",
        "decline",
    }
    GroupMembership.objects.filter(group=group, user=other).update(status="left")
    from core_apps.features.planning_group_views_parts.process_payload import (
        invalidate_process,
    )

    invalidate_process(process)
    assert visit.participant_decisions.count() == 2 and participant(visit, actor)
    assert authenticated(other).get(path(visit)).status_code == 404
    assert (
        authenticated(owner)
        .post(
            "/api/v1/features/v1/tenancy-invitations/",
            invite_body(visit),
            format="json",
        )
        .status_code
        == 201
    )


def test_reassignment_is_audited_and_not_signing_authority(rental_participants, visit):
    owner, actor, other, prop, _ = rental_participants
    company, member = company_for(actor)
    representative = CompanyMembership.objects.create(
        company=company, user=other, is_employee=True
    )
    visit.company, visit.context_kind = company, "company"
    visit.save()
    result = command(
        actor,
        visit.id,
        {
            "action": "reassign",
            "expected_revision": visit.revision,
            "representative_membership_id": representative.id,
        },
    )
    assert (
        result.tenant == other
        and not representative.can_execute_payments
        and representative.signing_verified_until is None
    )
    assert not participant(result, actor)
    assert result.participant_decisions.count() == 0


@pytest.mark.django_db(transaction=True)
def test_reschedule_race_has_one_winner_and_keeps_owner_confirmation_required(
    rental_participants, visit
):
    owner, actor, other, prop, _ = rental_participants
    date = timezone.localdate() + timedelta(days=4)
    for hour in [10, 11]:
        OwnerAvailabilitySlot.objects.create(
            property=prop, owner=owner, date=date, time=time(hour)
        )

    def move(hour):
        try:
            command(
                actor,
                visit.id,
                {
                    "action": "reschedule",
                    "expected_revision": visit.revision,
                    "visit_date": date,
                    "visit_time": time(hour),
                },
            )
            return "changed"
        except Exception as error:
            return type(error).__name__

    results = parallel_calls(lambda index: move(10 + index))
    assert results.count("changed") == 1, results
    visit.refresh_from_db()
    assert visit.status == "pending" and visit.accepted_at is None


def test_reschedule_receipt_is_read_only_and_role_scoped(rental_participants, visit):
    owner, actor, other, prop, _ = rental_participants
    date = timezone.localdate() + timedelta(days=4)
    OwnerAvailabilitySlot.objects.create(
        property=prop, owner=owner, date=date, time=time(15)
    )
    key = str(uuid.uuid4())
    uri = API + f"visits/{visit.id}/commands/"
    response = authenticated(actor).post(
        uri,
        {
            "request_key": key,
            "expected_revision": visit.revision,
            "action": "reschedule",
            "visit_date": str(date),
            "visit_time": "15:00",
            "note": "Confirmed new time",
        },
        format="json",
    )
    assert response.status_code == 200, response.data
    assert response.data["visit"]["id"] == str(visit.id)
    receipt = authenticated(actor).get(uri, {"request_key": key})
    assert receipt.status_code == 200 and receipt.data["status"] == "confirmed"
    assert authenticated(other).get(uri, {"request_key": key}).status_code == 404
    visit.refresh_from_db()
    assert visit.status == "pending" and visit.note == "Confirmed new time"
    assert PropertyVisit.objects.count() == 1


def test_representatives_only_current_coordinator_can_list(rental_participants):
    owner, actor, other, prop, _ = rental_participants
    company, member = company_for(actor)
    person = CompanyMembership.objects.create(
        company=company, user=other, is_employee=True
    )
    uri = API + f"viewing-companies/{company.id}/representatives/"
    response = authenticated(actor).get(uri)
    assert response.status_code == 200
    assert str(person.id) in {row["id"] for row in response.data["results"]}
    assert not any("email" in row or "phone" in row for row in response.data["results"])
    assert authenticated(other).get(uri).status_code == 403
    person.is_active = False
    person.save()
    assert str(person.id) not in {
        row["id"] for row in authenticated(actor).get(uri).data["results"]
    }
