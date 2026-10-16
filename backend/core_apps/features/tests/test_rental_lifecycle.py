"""Gap closure contract, privacy and real PostgreSQL allocation tests."""

import copy
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from django.db import IntegrityError, connection, connections, transaction
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from core_apps.features.models import (
    ApplicationProfileVersion,
    ApplicationAccessGrant,
    RentalCommercialPolicy,
    RentalInterest,
    TermsProposal,
    RentalAvailabilityConfirmation,
    ReservationHold,
    RentalInventoryDayLock,
    RentalInventoryUnit,
    Lease,
    RentalOperationalCase,
    RentalConsentRecord,
    LedgerEntry,
    LedgerTransaction,
)
from core_apps.features.services.rental_phase2 import fingerprint, RentalConflict
from core_apps.features.services.rental_lifecycle.inventory import (
    allocate_days,
    unit_keys,
    guard_topology_update,
    expire_property_holds,
)
from core_apps.features.services.rental_lifecycle.reservations import transfer_hold
from core_apps.features.services.rental_phase3 import post_ledger_transaction
from core_apps.features.tests.test_rental_phase2 import (
    rental_participants,
    authenticated,
    agreement_terms,
)
from core_apps.properties.models import Property

PREFIX = "/api/v1/features/v1/"
RULES = dict(
    approved=True,
    reservations=True,
    application_sharing=True,
    independent_group_booking=True,
    hold_minutes=30,
    max_extensions=1,
    max_active_holds=2,
    availability_hours=24,
    turnover_days=0,
    reconciliation_minutes=30,
    max_booking_days=365,
    share_days=7,
    case_hours=24,
)


@pytest.fixture
def policy(db, settings):
    settings.RENTAL_LIFECYCLE_POLICY_VERSION = "test-lifecycle-v1"
    return RentalCommercialPolicy.objects.create(
        version="test-lifecycle-v1", lifecycle_rules=RULES
    )


def command(revision=0, **data):
    return dict(request_key=str(uuid.uuid4()), expected_revision=revision, **data)


def post(user, path, body):
    return authenticated(user).post(PREFIX + path, body, format="json")


def proposal_for(tenant, prop, offer_id):
    from core_apps.features.services.tenancy_invitations import resolve_offer_snapshot

    offer = next(
        item for item in prop.rental_inventory["offers"] if item["id"] == offer_id
    )
    _, snapshot = resolve_offer_snapshot(prop, offer_id, offer["revision"])
    start = timezone.localdate() + timedelta(days=3)
    end = start + timedelta(days=30)
    interest = RentalInterest.objects.create(
        property=prop,
        tenant=tenant,
        offer_id=offer_id,
        offer_revision=offer["revision"],
        offer_snapshot=snapshot,
        desired_start=start,
        months=1,
        occupants=1,
    )
    return TermsProposal.objects.create(
        interest=interest,
        owner=prop.owner,
        terms=agreement_terms(start, end),
        offer_snapshot=snapshot,
        status="accepted",
        accepted_by=[str(prop.owner.id), str(tenant.id)],
    )


def hold_body(proposal):
    prop = proposal.interest.property
    return command(
        property_id=str(prop.id),
        inventory_revision=prop.rental_inventory["revision"],
        offer_id=proposal.interest.offer_id,
        offer_revision=proposal.interest.offer_revision,
        proposal_id=str(proposal.id),
        proposal_revision=proposal.revision,
        terms_digest=fingerprint(proposal.terms),
        starts_on=proposal.terms["starts_on"],
        ends_on_exclusive=proposal.terms["ends_on_exclusive"],
    )


def confirm(prop):
    RentalAvailabilityConfirmation.objects.update_or_create(
        property=prop,
        defaults=dict(
            confirmed_by=prop.owner,
            inventory_revision=prop.rental_inventory["revision"],
            confirmed_at=timezone.now(),
        ),
    )


@pytest.mark.django_db
def test_application_versions_sharing_privacy_revocation_and_recovery(
    rental_participants, policy
):
    owner, tenant, stranger, prop, _ = rental_participants
    body = command(
        desired_start=str(timezone.localdate() + timedelta(days=4)),
        months=3,
        occupants=1,
        introduction="My chosen introduction",
    )
    result = authenticated(tenant).patch(
        PREFIX + "application-profile/", body, format="json"
    )
    assert result.status_code == 200, result.data
    profile = result.data["resource"]
    assert profile["revision"] == 1
    assert set(result.json()) == {"message", "data"}
    assert "no-store" in result["Cache-Control"]
    assert (
        authenticated(tenant)
        .patch(PREFIX + "application-profile/", body, format="json")
        .data
        == result.data
    )
    changed = {**body, "months": 4}
    assert (
        authenticated(tenant)
        .patch(PREFIX + "application-profile/", changed, format="json")
        .status_code
        == 409
    )
    version = post(tenant, "application-profile/versions/", command(1)).data["resource"]
    expires = (timezone.now() + timedelta(days=1)).isoformat()
    preview_body = dict(
        version_id=version["id"],
        property_id=str(prop.id),
        categories=["rental_preferences", "introduction"],
        expires_at=expires,
    )
    preview = post(tenant, "application-shares/preview/", preview_body)
    assert preview.status_code == 200, preview.data
    share = post(
        tenant,
        "application-shares/",
        command(1, **preview_body, consent_digest=preview.data["consent_digest"]),
    )
    assert share.status_code == 201, share.data
    grant = share.data["resource"]
    assert (
        authenticated(owner)
        .get(PREFIX + f"application-shares/{grant['id']}/")
        .data["snapshot"]["months"]
        == 3
    )
    assert (
        authenticated(stranger)
        .get(PREFIX + f"application-shares/{grant['id']}/")
        .status_code
        == 404
    )
    edited = authenticated(tenant).patch(
        PREFIX + "application-profile/", command(1, months=9), format="json"
    )
    assert edited.status_code == 200
    assert (
        ApplicationProfileVersion.objects.get(id=version["id"]).snapshot["months"] == 3
    )
    assert (
        post(
            tenant, f"application-shares/{grant['id']}/revoke/", command(1)
        ).status_code
        == 200
    )
    assert (
        authenticated(owner)
        .get(PREFIX + f"application-shares/{grant['id']}/")
        .status_code
        == 404
    )
    assert (
        authenticated(tenant)
        .get(
            PREFIX
            + f"rental-operations/{share.data['operation_receipt']['request_key']}/?subject_id={version['id']}"
        )
        .status_code
        == 200
    )


@pytest.mark.django_db
def test_share_is_disabled_without_reviewed_policy_and_rejects_extra_private_fields(
    rental_participants,
):
    _, tenant, _, _, _ = rental_participants
    body = command(is_verified=True, identity_document="private")
    assert (
        authenticated(tenant)
        .patch(PREFIX + "application-profile/", body, format="json")
        .status_code
        == 400
    )


@pytest.mark.django_db
def test_application_followup_and_durable_outbox(rental_participants):
    owner, tenant, stranger, prop, offer = rental_participants
    result = post(
        tenant,
        "rental-interests/",
        command(
            property_id=str(prop.id),
            offer_id=offer,
            offer_revision=2,
            desired_start=str(timezone.localdate() + timedelta(days=3)),
            months=2,
            occupants=1,
        ),
    )
    assert result.status_code == 201, result.data
    interest = result.data["resource"]
    response = post(
        owner,
        f"rental-interests/{interest['id']}/respond/",
        command(1, decision="request_information", note="Confirm intended start."),
    )
    assert response.status_code == 200, response.data
    assert response.data["resource"]["waiting_for"] == "tenant"
    assert (
        post(
            stranger,
            f"rental-interests/{interest['id']}/respond/",
            command(2, decision="provide_information", note="No"),
        ).status_code
        == 404
    )
    response = post(
        tenant,
        f"rental-interests/{interest['id']}/respond/",
        command(2, decision="provide_information", note="Start as requested."),
    )
    assert response.status_code == 200, response.data
    assert response.data["resource"]["waiting_for"] == "owner"
    from core_apps.features.planning_models import PlanningEvent

    assert (
        PlanningEvent.objects.filter(destination__target_id=interest["id"]).count() == 3
    )
    queue = authenticated(owner).get(PREFIX + "owner-application-queue/")
    assert queue.status_code == 200
    deal = authenticated(tenant).get(PREFIX + f"deals/{interest['id']}/")
    assert deal.data["applicant_response"] == "Start as requested."
    assert (
        authenticated(stranger).get(PREFIX + f"deals/{interest['id']}/").status_code
        == 404
    )


@pytest.mark.django_db
def test_reservation_confirmation_policy_replay_overlap_extension_release(
    rental_participants, policy
):
    owner, tenant, stranger, prop, offer = rental_participants
    proposal = proposal_for(tenant, prop, offer)
    body = hold_body(proposal)
    assert post(tenant, "reservation-holds/", body).status_code == 409
    confirm(prop)
    result = post(tenant, "reservation-holds/", body)
    assert result.status_code == 201, result.data
    hold = result.data["resource"]
    assert hold["amount_due_now"]["amount_minor"] == 0
    assert post(tenant, "reservation-holds/", body).data == result.data
    assert (
        post(
            tenant, "reservation-holds/", {**body, "terms_digest": "0" * 64}
        ).status_code
        == 409
    )
    assert post(tenant, "reservation-holds/", hold_body(proposal)).status_code == 409
    assert (
        authenticated(stranger)
        .get(PREFIX + f"reservation-holds/{hold['id']}/")
        .status_code
        == 404
    )
    extended = post(tenant, f"reservation-holds/{hold['id']}/extend/", command(1))
    assert extended.status_code == 200, extended.data
    assert (
        post(tenant, f"reservation-holds/{hold['id']}/extend/", command(2)).status_code
        == 409
    )
    assert (
        post(tenant, f"reservation-holds/{hold['id']}/release/", command(2)).status_code
        == 200
    )
    assert not RentalInventoryDayLock.objects.exists()


@pytest.mark.django_db
def test_expired_hold_is_released_synchronously_and_topology_cannot_bypass_hold(
    rental_participants, policy
):
    _, tenant, _, prop, offer = rental_participants
    confirm(prop)
    proposal = proposal_for(tenant, prop, offer)
    result = post(tenant, "reservation-holds/", hold_body(proposal))
    assert result.status_code == 201, result.data
    replacement = copy.deepcopy(prop.rental_inventory)
    replacement["rooms"] = [{"id": str(uuid.uuid4()), "beds": []}]
    with pytest.raises(RentalConflict):
        guard_topology_update(prop, replacement)
    ReservationHold.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
    result = post(tenant, "reservation-holds/", hold_body(proposal))
    assert result.status_code == 201, result.data
    assert ReservationHold.objects.filter(status="expired").count() == 1


@pytest.mark.django_db
def test_hold_transfer_keeps_same_rows_and_half_open_buffer(
    rental_participants, policy
):
    owner, tenant, _, prop, offer = rental_participants
    confirm(prop)
    proposal = proposal_for(tenant, prop, offer)
    result = post(tenant, "reservation-holds/", hold_body(proposal))
    assert result.status_code == 201, result.data
    hold = ReservationHold.objects.get(id=result.data["resource"]["id"])
    before = set(hold.day_locks.values_list("id", flat=True))
    lease = Lease.objects.create(
        property=prop,
        owner=owner,
        tenant=tenant,
        start_date=hold.starts_on,
        end_date=hold.ends_on_exclusive,
        rent_amount_minor=1000000,
        offer_id=offer,
        offer_snapshot=hold.selection_snapshot,
        terms=proposal.terms,
        legacy_read_only=False,
    )
    with transaction.atomic():
        Property.objects.select_for_update().get(pk=prop.pk)
        assert transfer_hold(lease, proposal)
    assert set(lease.inventory_day_locks.values_list("id", flat=True)) == before
    assert not lease.inventory_day_locks.filter(stay_on=lease.end_date).exists()


@pytest.mark.parametrize(
    "scope,expected", [("entire_property", 2), ("room", 2), ("bed", 1)]
)
@pytest.mark.django_db
def test_canonical_units_expand_exclusive_scopes(rental_participants, scope, expected):
    _, _, _, prop, _ = rental_participants
    room = str(uuid.uuid4())
    beds = [str(uuid.uuid4()), str(uuid.uuid4())]
    prop.rental_inventory = {
        "rooms": [{"id": room, "beds": [{"id": bed} for bed in beds]}]
    }
    assert (
        len(
            unit_keys(
                prop, {"rental_scope": scope, "room_ids": [room], "bed_id": beds[0]}
            )
        )
        == expected
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("scope", ["entire_property", "bed"])
def test_two_postgres_connections_cannot_reserve_overlapping_accommodation(
    rental_participants, policy, scope
):
    if connection.vendor != "postgresql":
        pytest.skip("Real PostgreSQL race required")
    _, tenant, other, prop, offer = rental_participants
    if scope == "bed":
        room, bed = str(uuid.uuid4()), str(uuid.uuid4())
        prop.rental_inventory["mode"] = "partial"
        prop.rental_inventory["rooms"] = [
            {
                "id": room,
                "name": "Synthetic room",
                "beds": [{"id": bed, "name": "Synthetic bed"}],
            }
        ]
        prop.rental_inventory["offers"][0].update(
            rental_scope="bed", room_ids=[room], bed_id=bed, capacity=1
        )
        prop.save(update_fields=["rental_inventory"])
    confirm(prop)
    bodies = [hold_body(proposal_for(actor, prop, offer)) for actor in [tenant, other]]
    barrier = Barrier(2)

    def reserve(pair):
        actor, body = pair
        connections.close_all()
        try:
            barrier.wait(timeout=10)
            result = post(actor, "reservation-holds/", body)
            return result.status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(reserve, zip([tenant, other], bodies)))
    assert sorted(statuses) == [201, 409], statuses
    assert ReservationHold.objects.count() == 1


@pytest.mark.django_db
def test_physical_overlap_across_scopes_and_adjacent_half_open_dates(
    rental_participants,
):
    _, _, _, prop, _ = rental_participants
    rooms = [str(uuid.uuid4()) for _ in range(3)]
    beds = [str(uuid.uuid4()) for _ in range(3)]
    prop.rental_inventory["rooms"] = [
        {"id": room, "beds": [{"id": bed}]} for room, bed in zip(rooms, beds)
    ]
    prop.save(update_fields=["rental_inventory"])
    start = timezone.localdate() + timedelta(days=4)
    end = start + timedelta(days=4)
    room_snapshot = {"rental_scope": "room", "room_ids": [rooms[1]]}
    with transaction.atomic():
        prop = Property.objects.select_for_update().get(pk=prop.pk)
        allocate_days(
            prop=prop,
            snapshot=room_snapshot,
            offer_id="room",
            starts_on=start,
            ends_on=end,
            expires_at=None,
        )
        for snapshot in [
            {"rental_scope": "entire_property"},
            {"rental_scope": "room_group", "room_ids": rooms[:2]},
            {"rental_scope": "bed", "room_ids": [rooms[1]], "bed_id": beds[1]},
        ]:
            with pytest.raises(RentalConflict):
                allocate_days(
                    prop=prop,
                    snapshot=snapshot,
                    offer_id="alternative",
                    starts_on=start,
                    ends_on=end,
                    expires_at=None,
                )
        allocate_days(
            prop=prop,
            snapshot=room_snapshot,
            offer_id="adjacent",
            starts_on=end,
            ends_on=end + timedelta(days=2),
            expires_at=None,
        )
        allocate_days(
            prop=prop,
            snapshot=room_snapshot,
            offer_id="disjoint",
            starts_on=end + timedelta(days=4),
            ends_on=end + timedelta(days=5),
            expires_at=None,
        )
        assert not prop.rental_day_locks.filter(
            stay_on=end + timedelta(days=2)
        ).exists()


@pytest.mark.django_db
def test_database_backstop_and_ledger_identity_are_not_only_service_checks(
    rental_participants,
):
    _, _, _, prop, offer = rental_participants
    unit = RentalInventoryUnit.objects.create(
        property=prop, physical_key="bed:test", topology_digest="a" * 64
    )
    RentalInventoryDayLock.objects.create(
        property=prop,
        unit=unit,
        offer_id=offer,
        stay_on=timezone.localdate(),
        kind="occupied",
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        RentalInventoryDayLock.objects.create(
            property=prop,
            unit=unit,
            offer_id="other-offer",
            stay_on=timezone.localdate(),
            kind="occupied",
        )
    entries = [("cash", "debit", 100), ("liability", "credit", 100)]
    post_ledger_transaction(reference="source-1", kind="test", entries=entries)
    post_ledger_transaction(reference="source-1", kind="test", entries=entries)
    assert LedgerEntry.objects.count() == 2
    with pytest.raises(RentalConflict):
        post_ledger_transaction(
            reference="source-1",
            kind="test",
            entries=[("cash", "debit", 101), ("liability", "credit", 101)],
        )


@pytest.mark.django_db
def test_unknown_costs_are_not_zero_or_all_inclusive(rental_participants):
    _, tenant, _, prop, offer = rental_participants
    result = authenticated(tenant).get(
        PREFIX + f"properties/{prop.id}/decision-summary/",
        {"offer_id": offer, "offer_revision": 2},
    )
    assert result.status_code == 200, result.data
    assert result.data["complete_total"] is False
    lines = {line["code"]: line for line in result.data["lines"]}
    assert lines["utilities"]["amount"] is None
    assert lines["deposit"]["refundable"] is True
    assert result.data["property_claims"] == []
    assert result.data["owner_identity_claims"] == []


@pytest.mark.django_db
def test_decision_preserves_price_period_and_explicit_deposit_rules(
    rental_participants,
):
    _, tenant, _, prop, offer = rental_participants
    terms = prop.rental_inventory["offers"][0]["terms"]
    terms.update(price="1500.01", price_period="weekly", deposit="none")
    prop.save(update_fields=["rental_inventory"])
    result = authenticated(tenant).get(
        PREFIX + f"properties/{prop.id}/decision-summary/",
        {"offer_id": offer, "offer_revision": 2},
    )
    assert result.status_code == 200, result.data
    lines = {line["code"]: line for line in result.data["lines"]}
    assert lines["rent"]["amount"]["amount_minor"] == 150001
    assert lines["rent"]["recurrence"] == "weekly"
    assert result.data["known_monthly_subtotal_minor"] is None
    assert lines["deposit"]["amount"]["amount_minor"] == 0
    terms.update(price_period="monthly", deposit="half_month")
    prop.save(update_fields=["rental_inventory"])
    result = authenticated(tenant).get(
        PREFIX + f"properties/{prop.id}/decision-summary/",
        {"offer_id": offer, "offer_revision": 2},
    )
    deposit = next(line for line in result.data["lines"] if line["code"] == "deposit")
    assert deposit["amount"]["amount_minor"] == 75001
    assert deposit["refundable"] is True


@pytest.mark.parametrize(
    "path",
    [
        "application-profile/",
        "owner-application-queue/",
        "rental-cases/",
        "group-booking-proposals/",
    ],
)
@pytest.mark.django_db
def test_anonymous_private_reads_denied(path):
    assert APIClient().get(PREFIX + path).status_code in {401, 403}
