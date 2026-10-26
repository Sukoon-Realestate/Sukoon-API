"""A representative's viewing is provenance, never company contract consent."""

from datetime import timedelta
import uuid
import pytest
from django.utils import timezone
from core_apps.features.tests.test_company_housing import (
    company_setup,
    rental_participants,
    policy,
    authenticated,
    API,
    command,
)
from core_apps.features.company_models import CompanyHousingRequest, CompanyMembership
from core_apps.features.models import Lease, ReservationHold
from core_apps.features.planning_models import PlanningEvent
from core_apps.features.services.company import bookings
from core_apps.features.services.company.viewing_handoff import filter_offers
from core_apps.features.services.rental_phase2 import RentalConflict
from core_apps.features.services.tenancy_invitations import resolve_offer_snapshot
from core_apps.properties.models import PropertyVisit
from core_apps.properties.services.post_visit_decision import (
    submit_decision,
    visit_context,
)


@pytest.fixture
def viewed(company_setup):
    owner, coordinator, representative, company, _, props, offer, request = (
        company_setup
    )
    prop = props[0]
    offer_id = prop.rental_inventory["offers"][0]["id"]
    _, snapshot = resolve_offer_snapshot(prop, offer_id, 2)
    yesterday = timezone.localtime() - timedelta(days=1)
    visit = PropertyVisit.objects.create(
        property=prop,
        tenant=representative,
        requested_by=coordinator,
        company=company,
        context_kind="company",
        status="confirmed",
        visit_date=yesterday.date(),
        visit_time=yesterday.time().replace(tzinfo=None),
        accepted_at=yesterday - timedelta(days=1),
        offer_id=offer_id,
        offer_snapshot=snapshot,
    )
    submit_decision(
        representative,
        visit.id,
        {
            "decision": "proceed",
            "attended": True,
            "expected_revision": visit.revision,
            "request_key": str(uuid.uuid4()),
        },
    )
    visit.refresh_from_db()
    decision = visit.participant_decisions.get(tenant=representative)
    body = {key: getattr(request, key) for key in bookings.REQUEST_FIELDS}
    body.update(
        source_visit_id=str(visit.id),
        source_visit_revision=visit.revision,
        source_decision_id=str(decision.id),
    )
    return company_setup, visit, decision, body


@pytest.mark.django_db
@pytest.mark.parametrize("decision_value", ["proceed", "decline"])
def test_company_representative_can_reach_first_post_visit_decision(
    company_setup, decision_value
):
    owner, coordinator, representative, company, _, props, _, _ = company_setup
    yesterday = timezone.localtime() - timedelta(days=1)
    visit = PropertyVisit.objects.create(
        property=props[0],
        tenant=representative,
        requested_by=coordinator,
        company=company,
        context_kind="company",
        status="confirmed",
        visit_date=yesterday.date(),
        visit_time=yesterday.time().replace(tzinfo=None),
        accepted_at=yesterday - timedelta(days=1),
    )
    before = visit_context(visit, representative)
    assert before["post_visit_actions"]["can_submit"] is True
    assert before["rental_continuation"]["next_actor"] == "tenant"
    assert before["rental_continuation"]["next_action"] == "submit_post_visit_decision"
    for observer in [owner, coordinator]:
        projection = visit_context(visit, observer)
        assert projection["post_visit_actions"]["can_submit"] is False
        assert projection["rental_continuation"]["next_action"] is None
    submit_decision(
        representative,
        visit.id,
        {
            "decision": decision_value,
            "attended": True,
            "reason": "Private reason" if decision_value == "decline" else "",
            "expected_revision": visit.revision,
            "request_key": str(uuid.uuid4()),
        },
    )
    visit.refresh_from_db()
    after = visit_context(visit, coordinator)["rental_continuation"]
    if decision_value == "proceed":
        assert after["status"] == "company_request_available"
        assert after["next_action"] == "create_company_request"
    else:
        assert after["status"] == "declined"
        assert after["next_action"] is None and after["next_actor"] is None
    assert not CompanyHousingRequest.objects.filter(source_visit=visit).exists()
    assert not Lease.objects.exists() and not ReservationHold.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("status,future", [("pending", False)])
def test_company_viewing_cannot_offer_decision_before_eligibility(
    company_setup, status, future
):
    _, coordinator, representative, company, _, props, _, _ = company_setup
    day = timezone.localtime() + timedelta(days=1 if future else -1)
    visit = PropertyVisit.objects.create(
        property=props[0],
        tenant=representative,
        requested_by=coordinator,
        company=company,
        context_kind="company",
        status=status,
        visit_date=day.date(),
        visit_time=day.time().replace(tzinfo=None),
    )
    projection = visit_context(visit, representative)
    assert projection["post_visit_actions"]["can_submit"] is False
    assert projection["rental_continuation"]["status"] == "visit_not_eligible"
    assert projection["rental_continuation"]["next_action"] is None


@pytest.mark.django_db
def test_company_viewing_command_replay_and_real_package_handoff(viewed):
    setup, visit, decision, body = viewed
    owner, coordinator, representative, company, _, _, offer, _ = setup
    client = authenticated(coordinator)
    endpoint = API + f"companies/{company.id}/housing-requests/"
    body = command(**body)
    response = client.post(endpoint, body, format="json")
    assert response.status_code == 201, response.data
    replay = client.post(endpoint, body, format="json")
    assert replay.status_code in {200, 201}, replay.data
    request = CompanyHousingRequest.objects.get(source_visit=visit)
    assert request.source_viewing_snapshot["decision_id"] == str(decision.id)
    assert not Lease.objects.exists() and not ReservationHold.objects.exists()
    assert visit_context(visit, coordinator)["rental_continuation"][
        "company_request_id"
    ] == str(request.id)
    assert (
        visit_context(visit, representative)["rental_continuation"][
            "company_request_id"
        ]
        is None
    )
    item = bookings.select_offer(
        coordinator,
        request.id,
        {
            "expected_revision": request.revision,
            "offer_id": offer.id,
            "offer_revision": offer.revision,
            "occupant_ids": [],
        },
    )
    assert item.snapshot["source_viewing"]["visit_id"] == str(visit.id)
    assert item.status == "proposed"
    assert not ReservationHold.objects.exists()
    assert (
        filter_offers(type(offer).objects.all(), request).filter(pk=offer.pk).exists()
    )


@pytest.mark.django_db
def test_company_viewing_discovers_coordinator_without_disclosing_private_reason(
    viewed,
):
    setup, visit, _, _ = viewed
    result = visit_context(visit, setup[1])["rental_continuation"]
    assert result["next_action"] == "create_company_request"
    assert visit_context(visit, setup[2])["rental_continuation"]["next_action"] is None
    task = PlanningEvent.objects.get(
        recipient=setup[1], event_key__startswith="company.viewing_decision:"
    )
    assert task.destination["visit_id"] == str(visit.id)
    assert "reason" not in task.destination
    assert task.notification_id


@pytest.mark.django_db
@pytest.mark.parametrize(
    "change", ["revision", "representative", "ownership", "retired"]
)
def test_company_viewing_rechecks_source_before_creation(viewed, change):
    setup, visit, _, body = viewed
    if change == "revision":
        visit.revision += 1
        visit.save()
    elif change == "representative":
        CompanyMembership.objects.filter(company=setup[3], user=setup[2]).update(
            is_active=False
        )
    elif change == "ownership":
        visit.property.owner = setup[2]
        visit.property.save()
    else:
        visit.property.retired_at = timezone.now()
        visit.property.status = "hidden"
        visit.property.is_verified = False
        visit.property.save()
    with pytest.raises(RentalConflict):
        bookings.save_request(setup[1], setup[3], body)
    assert not CompanyHousingRequest.objects.filter(source_visit=visit).exists()


@pytest.mark.django_db
def test_company_viewing_rechecks_source_before_selection_and_rejects_duplicate(viewed):
    setup, visit, _, body = viewed
    request = bookings.save_request(setup[1], setup[3], body)
    with pytest.raises(RentalConflict):
        bookings.save_request(setup[1], setup[3], body)
    CompanyMembership.objects.filter(company=setup[3], user=setup[2]).update(
        is_active=False
    )
    with pytest.raises(RentalConflict):
        bookings.select_offer(
            setup[1],
            request.id,
            {
                "expected_revision": request.revision,
                "offer_id": setup[6].id,
                "offer_revision": setup[6].revision,
                "occupant_ids": [],
            },
        )
    assert not request.items.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("revoked", [False, True])
def test_company_viewing_delivery_reauthorizes_current_coordinator(
    viewed, monkeypatch, revoked
):
    from core_apps.features.services.planning_notifications import (
        deliver_planning_events,
    )
    from core_apps.notifications.services.fcm_service import FCMService
    from core_apps.notifications.models import DeviceToken
    from core_apps.notifications.services.push_delivery import dispatch

    setup, _, _, _ = viewed
    DeviceToken.objects.create(user=setup[1], token="synthetic-coordinator-device")
    sent = []
    monkeypatch.setattr(
        FCMService,
        "send_push_to_device",
        lambda **kwargs: sent.append(kwargs["token"]) or True,
    )
    if revoked:
        CompanyMembership.objects.filter(company=setup[3], user=setup[1]).update(
            is_coordinator=False
        )
    deliver_planning_events()
    dispatch()
    task = PlanningEvent.objects.get(
        recipient=setup[1], event_key__startswith="company.viewing_decision:"
    )
    if revoked:
        assert (
            task.delivery_status == "stale_or_unauthorized"
            and "synthetic-coordinator-device" not in sent
        )
    else:
        assert "synthetic-coordinator-device" in sent
