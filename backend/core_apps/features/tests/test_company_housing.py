"""Synthetic corporate inventory, authorization, budget and PostgreSQL races."""

import uuid
from datetime import date, timedelta
import pytest
from django.db import transaction, connection
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from core_apps.users.models import User
from core_apps.users.journey import canonical_user
from core_apps.properties.models import (
    Property,
    ResidentialBuilding,
    ResidentialComplex,
)
from core_apps.features.models import (
    RentalInventoryDayLock,
    ReservationHold,
    Lease,
    RentalAvailabilityConfirmation,
    OwnerPaymentProfile,
)
from core_apps.features.company_models import (
    Company,
    CompanyMembership,
    CompanyBookingItem,
    CompanyApproval,
    CompanyBudgetReservation,
)
from core_apps.features.services.company import (
    membership,
    portfolio,
    offers,
    bookings,
    approval_routing,
)
from core_apps.features.services.rental_lifecycle.inventory import (
    allocate_days,
    assert_available,
    expire_property_holds,
)
from core_apps.features.services.rental_phase2 import (
    RentalConflict,
    reserve_inventory_days,
)
from core_apps.features.tests.test_rental_phase2 import (
    rental_participants,
    authenticated,
)
from core_apps.features.tests.test_rental_lifecycle import policy
from core_apps.features.tests.test_cycle_concurrency import parallel_calls

API = "/api/v1/features/v1/"
FUTURE_YEAR = timezone.localdate().year + 1


def command(**values):
    return {"request_key": str(uuid.uuid4()), "expected_revision": 0, **values}


@pytest.fixture
def company_setup(rental_participants, policy, settings):
    settings.COMPANY_HOUSING_ENABLED = True
    owner, coordinator, approver, prop, _ = rental_participants
    company = membership.create_company(
        coordinator,
        {
            "name": "Synthetic company",
            "registration_number": "TEST-ONLY",
            "contact_email": "test@example.com",
        },
    )
    company.review_status = "verified"
    company.reviewed_by = owner
    company.review_reference = "synthetic-company-review"
    company.save()
    OwnerPaymentProfile.objects.update_or_create(
        owner=owner,
        defaults={
            "status": "ready",
            "payout_ready": True,
            "accepted_policy_versions": ["rental-policy-v1"],
        },
    )
    CompanyMembership.objects.filter(company=company, user=coordinator).update(
        is_coordinator=True
    )
    company.default_approver = CompanyMembership.objects.create(
        company=company, user=approver, is_approver=True
    )
    company.save()
    building = ResidentialBuilding.objects.create(
        manager=owner,
        name="Synthetic building",
        code="A",
        address="Synthetic Cairo",
        declared_units=2,
        authority_status="verified",
        authority_reviewed_by=owner,
        authority_reference="synthetic-review",
    )
    prop.building = building
    prop.unit_code = "101"
    prop.occupancy_capacity = 4
    prop.save()
    second = Property.objects.create(
        **{k: getattr(prop, k) for k in portfolio.TEMPLATE_FIELDS},
        owner=owner,
        building=building,
        unit_code="102",
        occupancy_capacity=4,
        status="verified",
        is_verified=True,
        is_ownership_verified=True,
    )
    for unit in (prop, second):
        RentalAvailabilityConfirmation.objects.create(
            property=unit,
            confirmed_by=owner,
            inventory_revision=(unit.rental_inventory or {}).get("revision", 0),
            confirmed_at=timezone.now(),
        )
    offer = offers.create_offer(
        owner,
        {
            "scope": "entire_building",
            "building_id": building.id,
            "monthly_rent_minor": 100000,
            "deposit_minor": 20000,
            "publish": True,
            "occupancy_policy": "reserve_capacity_with_notice",
        },
    )
    request = bookings.save_request(
        coordinator,
        company,
        {
            "title": "Synthetic team",
            "purpose": "Local verification",
            "location": "Cairo",
            "starts_on": date(FUTURE_YEAR, 1, 1),
            "ends_on_exclusive": date(FUTURE_YEAR, 2, 1),
            "headcount": 6,
            "commitment_ceiling_minor": 1000000,
            "deposit_limit_minor": 1000000,
        },
    )
    return (
        owner,
        coordinator,
        approver,
        company,
        building,
        [prop, second],
        offer,
        request,
    )


def proposed(setup):
    _, coordinator, _, _, _, _, offer, request = setup
    request.refresh_from_db()
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

    return approval_routing.submit(
        coordinator, item.id, {"expected_revision": item.revision}
    )


def approved(setup):
    item = proposed(setup)
    return bookings.decide(
        setup[2],
        item.id,
        {
            "expected_revision": item.revision,
            "snapshot_digest": item.snapshot_digest,
            "decision": "approved",
        },
    )


def held(setup):
    item = approved(setup)
    return bookings.hold_item(setup[1], item.id, {"expected_revision": item.revision})


@pytest.mark.django_db
def test_company_is_not_a_fake_user_and_admin_does_not_gain_financial_authority(
    company_setup,
):
    _, user, _, company, *_ = company_setup
    identity = canonical_user(user)
    assert identity["account_kind"] == "company"
    assert identity["id"] == str(user.id)
    member = CompanyMembership.objects.get(company=company, user=user)
    assert not member.can_execute_payments
    assert member.signing_verified_until is None
    with pytest.raises(PermissionDenied):
        from core_apps.features.services.company.access import member_for

        member_for(user, company, "pay")


@pytest.mark.django_db
def test_invitations_are_exact_recipient_expiring_and_single_use(company_setup):
    _, coordinator, approver, company, *_ = company_setup
    invite, token = membership.invite(
        coordinator, company.id, "employee@example.com", ["employee"]
    )
    employee = User.objects.create_user(
        email="employee@example.com", password="pass", is_verified=True
    )
    with pytest.raises(PermissionDenied):
        membership.accept_invitation(approver, token)
    assert not CompanyMembership.objects.filter(company=company, user=employee).exists()
    membership.accept_invitation(employee, token)
    with pytest.raises(RentalConflict):
        membership.accept_invitation(employee, token)
    invite.refresh_from_db()
    assert invite.accepted_by == employee
    expired, token2 = membership.invite(
        coordinator, company.id, "late@example.com", ["employee"]
    )
    expired.expires_at = timezone.now() - timedelta(seconds=1)
    expired.save()
    late = User.objects.create_user(
        email="late@example.com", password="pass", is_verified=True
    )
    with pytest.raises(RentalConflict):
        membership.accept_invitation(late, token2)


@pytest.mark.django_db
def test_last_admin_and_company_privacy(company_setup):
    owner, coordinator, _, company, *_ = company_setup
    member = CompanyMembership.objects.get(company=company, user=coordinator)
    with pytest.raises(RentalConflict):
        membership.update_member(
            coordinator,
            company.id,
            member.id,
            {
                "expected_revision": member.revision,
                "roles": ["coordinator"],
                "is_active": True,
            },
        )
    assert authenticated(owner).get(API + f"companies/{company.id}/").status_code == 404
    assert (
        authenticated(owner)
        .get(API + f"companies/{company.id}/housing-requests/")
        .status_code
        == 404
    )


@pytest.mark.django_db
def test_batch_retry_partial_results_distinct_inventory_and_no_verified_state(
    company_setup,
):
    owner, _, _, _, building, props, *_ = company_setup
    body = {
        "batch_key": uuid.uuid4(),
        "template_id": props[0].id,
        "parent_kind": "building",
        "parent_id": building.id,
        "units": [
            {"item_key": uuid.uuid4(), "unit_code": "201", "occupancy_capacity": 4},
            {"item_key": uuid.uuid4(), "unit_code": "101", "occupancy_capacity": 4},
        ],
    }
    first = portfolio.create_batch(owner, body)
    assert first["complete"] is False
    assert [r["status"] for r in first["results"]] == ["created", "failed"]
    created = Property.objects.get(id=first["results"][0]["property_id"])
    assert not created.is_ownership_verified and not created.is_verified
    assert (
        created.status == "under_review"
        and not created.ownership_proof
        and not created.main_image
    )
    assert (
        created.rental_inventory["offers"][0]["id"]
        != props[0].rental_inventory["offers"][0]["id"]
    )
    assert created.rental_inventory["offers"][0]["availability"] == "unavailable"
    body["units"][1]["unit_code"] = "202"
    second = portfolio.create_batch(owner, body)
    assert second["complete"] is True
    assert second["results"][0]["property_id"] == first["results"][0]["property_id"]
    assert building.units.count() == 4


@pytest.mark.django_db
def test_incomplete_or_partially_controlled_building_cannot_resolve(company_setup):
    _, _, _, _, building, props, offer, _ = company_setup
    building.declared_units = 3
    building.save()
    with pytest.raises(RentalConflict):
        offers.resolve_scope(offer)
    building.declared_units = 2
    building.authority_status = "pending"
    building.save()
    with pytest.raises(RentalConflict):
        offers.resolve_scope(offer)


@pytest.mark.django_db
def test_approval_does_not_allocate_and_is_commercially_immutable(company_setup):
    item = proposed(company_setup)
    before = item.snapshot_digest
    original = item.commercial_revision
    with pytest.raises(PermissionDenied):
        CompanyMembership.objects.filter(
            company=company_setup[3], user=company_setup[1]
        ).update(is_approver=True)
        bookings.decide(
            company_setup[1],
            item.id,
            {
                "expected_revision": item.revision,
                "snapshot_digest": before,
                "decision": "approved",
            },
        )
    item = bookings.decide(
        company_setup[2],
        item.id,
        {
            "expected_revision": item.revision,
            "snapshot_digest": before,
            "decision": "approved",
        },
    )
    assert item.snapshot_digest == before and item.commercial_revision == original
    assert not RentalInventoryDayLock.objects.exists()
    assert not Lease.objects.exists()
    assert CompanyBudgetReservation.objects.get(item=item).rent_minor == 100000


@pytest.mark.django_db
def test_funded_occupant_cannot_be_sole_approver(company_setup):
    item = proposed(company_setup)
    item.occupants.add(company_setup[2])
    with pytest.raises(PermissionDenied):
        bookings.decide(
            company_setup[2],
            item.id,
            {
                "expected_revision": item.revision,
                "snapshot_digest": item.snapshot_digest,
                "decision": "approved",
            },
        )


@pytest.mark.django_db
def test_whole_building_hold_blocks_each_unit_including_unassigned_capacity(
    company_setup,
):
    item = held(company_setup)
    assert item.snapshot["capacity"] == 8 and item.snapshot["reserve_places"] == 8
    assert item.hold.day_locks.count() == 62
    assert item.hold.day_locks.values("property").distinct().count() == 2
    for prop in company_setup[5]:
        with pytest.raises(RentalConflict):
            assert_available(
                prop,
                {"rental_scope": "entire_property"},
                date(FUTURE_YEAR, 1, 1),
                date(FUTURE_YEAR, 2, 1),
            )
        assert_available(
            prop,
            {"rental_scope": "entire_property"},
            date(FUTURE_YEAR, 2, 1),
            date(FUTURE_YEAR, 3, 1),
        )
    assert not item.assignments.exists()


@pytest.mark.django_db
def test_conflict_rolls_back_entire_aggregate_item(company_setup):
    item = approved(company_setup)
    with transaction.atomic():
        prop = Property.objects.select_for_update().get(pk=company_setup[5][1].pk)
        allocate_days(
            prop=prop,
            snapshot={"rental_scope": "entire_property"},
            offer_id="existing",
            starts_on=date(FUTURE_YEAR, 1, 15),
            ends_on=date(FUTURE_YEAR, 1, 16),
            expires_at=None,
        )
    with pytest.raises(RentalConflict):
        bookings.hold_item(
            company_setup[1], item.id, {"expected_revision": item.revision}
        )
    assert RentalInventoryDayLock.objects.count() == 1
    assert not ReservationHold.objects.exists()


@pytest.mark.django_db
def test_parent_commitment_prevents_new_unit_and_child_expiry_releases_all(
    company_setup,
):
    item = held(company_setup)
    body = {
        "batch_key": uuid.uuid4(),
        "template_id": company_setup[5][0].id,
        "parent_kind": "building",
        "parent_id": company_setup[4].id,
        "units": [
            {"item_key": uuid.uuid4(), "unit_code": "new", "occupancy_capacity": 4}
        ],
    }
    assert portfolio.create_batch(company_setup[0], body)["complete"] is False
    snapshot = item.snapshot.copy()
    item.hold.expires_at = timezone.now() - timedelta(seconds=1)
    item.hold.save()
    item.hold.day_locks.update(expires_at=item.hold.expires_at)
    with transaction.atomic():
        prop = Property.objects.select_for_update().get(pk=company_setup[5][1].pk)
        expire_property_holds(prop)
    assert not RentalInventoryDayLock.objects.exists()
    item.refresh_from_db()
    assert item.snapshot == snapshot


@pytest.mark.django_db
def test_disabled_new_bookings_preserve_existing_reads(company_setup, settings):
    item = held(company_setup)
    settings.COMPANY_HOUSING_ENABLED = False
    client = authenticated(company_setup[1])
    assert (
        client.get(API + f"company-housing-requests/{item.request.id}/").status_code
        == 200
    )
    with pytest.raises(RentalConflict):
        proposed(company_setup)


@pytest.mark.django_db
def test_dynamic_container_rejects_hidden_fields_and_envelopes(company_setup):
    owner = company_setup[0]
    body = command(
        kind="building",
        name="Test",
        code="B",
        address="Test",
        declared_units=12,
        declared_buildings=2,
    )
    assert (
        authenticated(owner)
        .post(API + "residential-assets/", body, format="json")
        .status_code
        == 400
    )
    body.pop("declared_buildings")
    response = authenticated(owner).post(
        API + "residential-assets/", body, format="json"
    )
    assert response.status_code == 201
    wire = response.json()
    assert wire["message"] and wire["data"]["resource"]["registered_units"] == 0
    repeated = authenticated(owner).post(
        API + "residential-assets/", body, format="json"
    )
    assert repeated.json()["data"] == wire["data"]


@pytest.mark.django_db(transaction=True)
def test_concurrent_parent_and_personal_unit_cannot_both_allocate(company_setup):
    if connection.vendor != "postgresql":
        pytest.skip("Real row-lock proof requires PostgreSQL")
    item = approved(company_setup)
    owner, coordinator, _, _, _, props, _, request = company_setup
    lease = Lease.objects.create(
        property=props[1],
        owner=owner,
        tenant=coordinator,
        template_id="synthetic",
        template_version="1",
        start_date=request.starts_on,
        end_date=request.ends_on_exclusive,
        rent_amount_minor=100,
        legacy_read_only=False,
        offer_id="personal",
        offer_snapshot={"rental_scope": "entire_property"},
    )

    def allocate(index):
        try:
            if index == 0:
                bookings.hold_item(
                    coordinator, item.id, {"expected_revision": item.revision}
                )
            else:
                reserve_inventory_days(
                    lease,
                    request.starts_on,
                    request.ends_on_exclusive,
                    timezone.now() + timedelta(hours=1),
                )
            return "reserved"
        except RentalConflict:
            return "conflict"

    assert sorted(parallel_calls(allocate)) == ["conflict", "reserved"]


@pytest.mark.django_db(transaction=True)
def test_concurrent_approvals_cannot_overspend_shared_budget(company_setup):
    if connection.vendor != "postgresql":
        pytest.skip("Real row-lock proof requires PostgreSQL")
    first = proposed(company_setup)
    second = proposed(company_setup)
    company = company_setup[3]
    company.budget_limit_minor = first.full_term_rent_minor
    company.save()
    items = [first, second]

    def decide(index):
        item = items[index]
        try:
            bookings.decide(
                company_setup[2],
                item.id,
                {
                    "expected_revision": item.revision,
                    "snapshot_digest": item.snapshot_digest,
                    "decision": "approved",
                },
            )
            return "approved"
        except RentalConflict:
            return "conflict"

    assert sorted(parallel_calls(decide)) == ["approved", "conflict"]
    assert CompanyBudgetReservation.objects.filter(status="reserved").count() == 1


@pytest.mark.django_db
def test_batch_receipt_recovery_and_retry_preserve_successful_ids(company_setup):
    owner, _, _, _, building, props, *_ = company_setup
    body = command(
        batch_key=str(uuid.uuid4()),
        template_id=str(props[0].id),
        parent_kind="building",
        parent_id=str(building.id),
        units=[
            {
                "item_key": str(uuid.uuid4()),
                "unit_code": "201",
                "occupancy_capacity": 4,
            },
            {
                "item_key": str(uuid.uuid4()),
                "unit_code": "101",
                "occupancy_capacity": 4,
            },
        ],
    )
    client = authenticated(owner)
    first = client.post(API + "residential-unit-batches/", body, format="json")
    assert first.status_code == 200, first.data
    first_data = first.json()["data"]["resource"]
    assert first_data["complete"] is False
    assert (
        client.post(API + "residential-unit-batches/", body, format="json").json()
        == first.json()
    )
    second = {
        **body,
        "request_key": str(uuid.uuid4()),
        "expected_revision": first_data["revision"],
        "units": [{**body["units"][1], "unit_code": "202"}],
    }
    saved = client.post(
        API + "residential-unit-batches/", second, format="json"
    ).json()["data"]["resource"]
    assert saved["complete"] and len(saved["results"]) == 2
    assert saved["results"][0]["property_id"] == first_data["results"][0]["property_id"]
    changed = {
        **body,
        "request_key": str(uuid.uuid4()),
        "expected_revision": saved["revision"],
        "units": [{**body["units"][0], "unit_code": "203"}],
    }
    assert (
        client.post(
            API + "residential-unit-batches/", changed, format="json"
        ).status_code
        == 409
    )
    current = client.get(API + f'residential-unit-batches/{body["batch_key"]}/').json()[
        "data"
    ]
    assert current == saved
    assert building.units.count() == 4


@pytest.mark.django_db
def test_invitation_recovery_is_private_and_never_remints_token(company_setup):
    owner, coordinator, _, company, *_ = company_setup
    body = command(email="invitee@example.com", roles=["employee"])
    client = authenticated(coordinator)
    result = client.post(
        API + f"companies/{company.id}/invitations/", body, format="json"
    )
    assert result.status_code == 201
    invitation = result.json()["data"]["resource"]
    path = API + f'company-invitations/{invitation["id"]}/'
    assert client.get(path).json()["data"]["token"] == invitation["token"]
    assert authenticated(owner).get(path).status_code == 404
    employee = User.objects.create_user(
        email="invitee@example.com", password="pass", is_verified=True
    )
    membership.accept_invitation(employee, invitation["token"])
    assert client.get(path).json()["data"]["token"] == ""


@pytest.mark.django_db
def test_company_holds_are_not_exposed_through_personal_reservation_api(company_setup):
    item = held(company_setup)
    for user in company_setup[:3]:
        assert (
            authenticated(user)
            .get(API + f"reservation-holds/{item.hold.id}/")
            .status_code
            == 404
        )
        data = authenticated(user).get(API + "reservation-holds/").json()["data"]
        assert data == []


@pytest.mark.django_db
def test_withdraw_releases_uncommitted_budget_and_inventory_with_flag_disabled(
    company_setup, settings
):
    item = held(company_setup)
    settings.COMPANY_HOUSING_ENABLED = False
    result = bookings.withdraw_item(
        company_setup[1], item.id, {"expected_revision": item.revision}
    )
    assert result.status == "withdrawn" and not RentalInventoryDayLock.objects.exists()
    assert CompanyBudgetReservation.objects.get(item=item).status == "released"
    settings.COMPANY_HOUSING_ENABLED = True
    with pytest.raises(RentalConflict):
        bookings.decide(
            company_setup[2],
            item.id,
            {
                "expected_revision": result.revision,
                "snapshot_digest": item.snapshot_digest,
                "decision": "approved",
            },
        )


@pytest.mark.django_db
def test_publishing_and_pausing_preserve_exact_existing_package(company_setup):
    item = approved(company_setup)
    snapshot = item.snapshot.copy()
    owner, coordinator, _, _, _, _, offer, _ = company_setup
    result = authenticated(owner).post(
        API + f"portfolio-offers/{offer.id}/pause/",
        command(expected_revision=offer.revision),
        format="json",
    )
    assert result.status_code == 200
    with pytest.raises(RentalConflict):
        bookings.hold_item(coordinator, item.id, {"expected_revision": item.revision})
    item.refresh_from_db()
    assert item.snapshot == snapshot and item.status == "approved"


@pytest.mark.django_db
def test_read_checks_the_entire_date_range_and_turnover(company_setup, policy):
    _, _, _, _, _, props, offer, request = company_setup
    with transaction.atomic():
        allocate_days(
            prop=props[1],
            snapshot={"rental_scope": "entire_property"},
            offer_id="other",
            starts_on=date(FUTURE_YEAR, 1, 31),
            ends_on=date(FUTURE_YEAR, 2, 1),
            expires_at=None,
        )
    payload = offers.offer_payload(
        offer, starts_on=request.starts_on, ends_on=request.ends_on_exclusive
    )
    assert payload["available_for_dates"] is False
    assert "tenant" not in str(payload).lower()


@pytest.mark.django_db
def test_unknown_capacity_and_named_occupant_policy_cannot_be_guessed(company_setup):
    offer = company_setup[6]
    offer.occupancy_policy = "named_occupants_required"
    offer.save()
    with pytest.raises(RentalConflict):
        proposed(company_setup)
    offer.occupancy_policy = "reserve_capacity_with_notice"
    offer.save()
    prop = company_setup[5][0]
    prop.occupancy_capacity = None
    prop.save()
    assert offers.offer_payload(offer)["capacity"] is None
    with pytest.raises(RentalConflict):
        proposed(company_setup)


def complex_setup(setup):
    owner, _, approver, _, building, props, _, _ = setup
    complex = ResidentialComplex.objects.create(
        manager=owner,
        name="Synthetic complex",
        code="C",
        address="Synthetic",
        declared_buildings=1,
        declared_standalone_units=1,
        authority_status="verified",
        authority_reviewed_by=approver,
        authority_reference="synthetic-review",
    )
    building.complex = complex
    building.save()
    standalone = Property.objects.create(
        **{k: getattr(props[0], k) for k in portfolio.TEMPLATE_FIELDS},
        owner=owner,
        complex=complex,
        unit_code="S1",
        occupancy_capacity=3,
        status="verified",
        is_verified=True,
        is_ownership_verified=True,
    )
    RentalAvailabilityConfirmation.objects.create(
        property=standalone,
        confirmed_by=owner,
        inventory_revision=0,
        confirmed_at=timezone.now(),
    )
    return complex, standalone


@pytest.mark.django_db
def test_entire_complex_includes_standalone_units_and_protects_child_topology(
    company_setup,
):
    complex, standalone = complex_setup(company_setup)
    setup = list(company_setup)
    setup[6] = offers.create_offer(
        setup[0],
        {
            "scope": "entire_complex",
            "complex_id": complex.id,
            "monthly_rent_minor": 120000,
            "deposit_minor": 10000,
            "publish": True,
            "occupancy_policy": "reserve_capacity_with_notice",
        },
    )
    item = held(setup)
    assert item.snapshot["capacity"] == 11
    assert {str(u.id) for u in [*setup[5], standalone]} == {
        u["id"] for u in item.snapshot["units"]
    }
    with pytest.raises(RentalConflict):
        portfolio.create_container(
            setup[0],
            {
                "kind": "building",
                "complex_id": complex.id,
                "name": "new",
                "code": "new",
                "address": "test",
                "declared_units": 1,
            },
        )
    with pytest.raises(RentalConflict):
        assert_available(
            standalone,
            {"rental_scope": "entire_property"},
            setup[7].starts_on,
            setup[7].ends_on_exclusive,
        )


@pytest.mark.django_db
def test_selected_units_only_claim_selected_conflict_resources(company_setup):
    complex, standalone = complex_setup(company_setup)
    setup = list(company_setup)
    setup[6] = offers.create_offer(
        setup[0],
        {
            "scope": "selected_units",
            "unit_ids": [setup[5][0].id, standalone.id],
            "monthly_rent_minor": 90000,
            "deposit_minor": 10000,
            "publish": True,
            "occupancy_policy": "reserve_capacity_with_notice",
        },
    )
    item = held(setup)
    assert item.hold.day_locks.values("property").distinct().count() == 2
    assert_available(
        setup[5][1],
        {"rental_scope": "entire_property"},
        setup[7].starts_on,
        setup[7].ends_on_exclusive,
    )


@pytest.mark.django_db
def test_authority_review_requires_independent_staff_and_is_audited(company_setup):
    from core_apps.features.services.company.administration import review
    from core_apps.features.models import RentalAuditEvent

    owner, coordinator, _, company, building, *_ = company_setup
    data = {
        "expected_revision": building.revision,
        "status": "verified",
        "evidence_reference": "private-review-123",
        "reason": "Reviewed legal scope",
    }
    with pytest.raises(PermissionDenied):
        review(owner, "building", building.id, data)
    owner.is_superuser = True
    owner.save()
    with pytest.raises(PermissionDenied):
        review(owner, "building", building.id, data)
    reviewer = User.objects.create_user(
        email="reviewer@example.com",
        password="pass",
        is_verified=True,
        is_superuser=True,
    )
    updated = review(reviewer, "building", building.id, data)
    assert updated.authority_reviewed_by == reviewer
    assert RentalAuditEvent.objects.filter(
        subject_id=building.id, action="portfolio_authority_reviewed", actor=reviewer
    ).exists()


@pytest.mark.django_db
def test_limits_cannot_drop_below_reserved_obligations(company_setup):
    from core_apps.features.services.company.administration import set_budget

    item = approved(company_setup)
    company = company_setup[3]
    with pytest.raises(RentalConflict):
        set_budget(
            company_setup[1],
            company.id,
            {
                "expected_revision": company.revision,
                "budget_limit_minor": item.full_term_rent_minor - 1,
                "deposit_limit_minor": None,
                "reason": "Too low",
            },
        )


@pytest.mark.django_db
def test_removed_approver_cannot_authorize_a_new_hold(company_setup):
    item = approved(company_setup)
    CompanyMembership.objects.filter(
        company=company_setup[3], user=company_setup[2]
    ).update(is_approver=False)
    with pytest.raises(PermissionDenied):
        bookings.hold_item(
            company_setup[1], item.id, {"expected_revision": item.revision}
        )


@pytest.mark.django_db(transaction=True)
def test_concurrent_topology_growth_cannot_bypass_whole_building_hold(company_setup):
    if connection.vendor != "postgresql":
        pytest.skip("Real row-lock proof requires PostgreSQL")
    item = approved(company_setup)
    setup = company_setup

    def attempt(index):
        try:
            if index == 0:
                bookings.hold_item(
                    setup[1], item.id, {"expected_revision": item.revision}
                )
            else:
                portfolio.create_batch_item(
                    setup[0],
                    {
                        "batch_key": uuid.uuid4(),
                        "template_id": setup[5][0].id,
                        "parent_kind": "building",
                        "parent_id": setup[4].id,
                    },
                    {
                        "item_key": uuid.uuid4(),
                        "unit_code": "new",
                        "occupancy_capacity": 4,
                    },
                )
            return "saved"
        except RentalConflict:
            return "conflict"

    assert sorted(parallel_calls(attempt)) == ["conflict", "saved"]


@pytest.mark.django_db
def test_attach_preserves_original_unit_and_legacy_historical_scope(company_setup):
    from core_apps.features.services.tenancy_invitations import resolve_offer_snapshot

    owner, coordinator, _, _, building, props, *_ = company_setup
    prop = Property.objects.create(
        **{k: getattr(props[0], k) for k in portfolio.TEMPLATE_FIELDS},
        owner=owner,
        status="verified",
        is_verified=True,
        is_ownership_verified=True,
    )
    lease = Lease.objects.create(
        property=prop,
        owner=owner,
        tenant=coordinator,
        template_id="synthetic",
        template_version="1",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 2, 1),
        rent_amount_minor=1000,
        status="ended",
        offer_snapshot=None,
    )
    before = Property.objects.count()
    attached = portfolio.attach_unit(
        owner,
        "building",
        building.id,
        {
            "expected_revision": building.revision,
            "property_id": prop.id,
            "inventory_revision": 0,
            "unit_code": "A-3",
            "occupancy_capacity": 3,
        },
    )
    assert Property.objects.count() == before
    prop.refresh_from_db()
    lease.refresh_from_db()
    assert (
        prop.building == attached
        and lease.property == prop
        and lease.offer_snapshot is None
    )
    assert resolve_offer_snapshot(prop, "") == ("", None)
    with pytest.raises(RentalConflict):
        portfolio.attach_unit(
            owner,
            "building",
            building.id,
            {
                "expected_revision": attached.revision,
                "property_id": prop.id,
                "inventory_revision": 0,
                "unit_code": "A-4",
                "occupancy_capacity": 3,
            },
        )


@pytest.mark.django_db
def test_attach_cannot_bypass_existing_personal_allocation(company_setup):
    owner, _, _, _, building, props, *_ = company_setup
    prop = Property.objects.create(
        **{k: getattr(props[0], k) for k in portfolio.TEMPLATE_FIELDS}, owner=owner
    )
    with transaction.atomic():
        allocate_days(
            prop=prop,
            snapshot={"rental_scope": "entire_property"},
            offer_id="personal",
            starts_on=date(FUTURE_YEAR, 1, 1),
            ends_on=date(FUTURE_YEAR, 2, 1),
            expires_at=None,
        )
    with pytest.raises(RentalConflict):
        portfolio.attach_unit(
            owner,
            "building",
            building.id,
            {
                "expected_revision": building.revision,
                "property_id": prop.id,
                "inventory_revision": 0,
                "unit_code": "A-3",
                "occupancy_capacity": 3,
            },
        )
    prop.refresh_from_db()
    assert prop.building is None and RentalInventoryDayLock.objects.count() == 31


@pytest.mark.django_db
def test_arabic_errors_use_existing_localized_envelope(company_setup):
    response = authenticated(company_setup[0]).post(
        API + "residential-assets/",
        command(
            kind="building",
            name="A",
            code="A",
            address="Cairo",
            declared_units=1,
            declared_buildings=2,
        ),
        format="json",
        HTTP_ACCEPT_LANGUAGE="ar",
    )
    assert response.status_code == 400
    assert (
        response.json()["message"]
        == "البيانات: يتطلب إنشاء العمارة العدد المعلن للوحدات وحقول العمارة فقط."
    )


@pytest.mark.django_db
def test_parented_inventory_cannot_be_deleted_through_legacy_property_service(
    company_setup,
):
    from core_apps.properties.services.property import PropertyService

    unit = company_setup[5][0]
    with pytest.raises(RentalConflict):
        PropertyService.delete_property(unit, company_setup[0])
    assert Property.objects.filter(pk=unit.pk).exists()


@pytest.mark.django_db
def test_staff_authority_review_recovers_without_company_membership(company_setup):
    from core_apps.features.services.company.access import actions

    building = company_setup[4]
    reviewer = User.objects.create_user(
        email="recovery-reviewer@example.test",
        password=None,
        is_verified=True,
        is_superuser=True,
    )
    body = command(
        expected_revision=building.revision,
        status="verified",
        evidence_reference="synthetic-evidence",
        reason="Synthetic scope review",
    )
    client = authenticated(reviewer)
    response = client.post(
        API + f"company-authority/building/{building.id}/review/", body, format="json"
    )
    assert response.status_code == 200, response.data
    path = API + f"rental-operations/{body['request_key']}/?subject_id={building.id}"
    recovered = client.get(path)
    assert recovered.status_code == 200, recovered.data
    assert recovered.data["operation_receipt"]["subject_id"] == str(building.id)
    assert not actions(reviewer, "residential_portfolios", building.id)
    assert not CompanyMembership.objects.filter(user=reviewer).exists()
    assert authenticated(company_setup[2]).get(path).status_code == 404
    reviewer.is_superuser = False
    reviewer.save()
    assert client.get(path).status_code == 404


@pytest.mark.django_db
def test_partial_batch_read_localizes_failures_without_changing_saved_results(
    company_setup,
):
    owner, _, _, _, building, props, *_ = company_setup
    body = command(
        batch_key=str(uuid.uuid4()),
        template_id=str(props[0].id),
        parent_kind="building",
        parent_id=str(building.id),
        units=[
            {
                "item_key": str(uuid.uuid4()),
                "unit_code": props[0].unit_code,
                "occupancy_capacity": None,
            }
        ],
    )
    client = authenticated(owner)
    response = client.post(
        API + "residential-unit-batches/",
        body,
        format="json",
        HTTP_ACCEPT_LANGUAGE="ar",
    )
    assert response.status_code == 200, response.data
    result = response.json()["data"]["resource"]
    assert not result["complete"]
    assert (
        result["results"][0]["message"] == "راجع قيم الوحدة ورمزها قبل إعادة المحاولة."
    )
    read = client.get(
        API + f"residential-unit-batches/{body['batch_key']}/",
        HTTP_ACCEPT_LANGUAGE="en",
    )
    assert (
        read.json()["data"]["results"][0]["message"]
        == "Review this unit's values and code before retrying."
    )


@pytest.mark.django_db
def test_synthetic_twelve_unit_hold_for_forty_employees_and_eight_reserve_places(
    company_setup,
):
    """Journey A through bounded hold only, with explicitly synthetic reviews."""
    owner, coordinator, approver, company, building, props, offer, request = (
        company_setup
    )
    building.declared_units = 12
    building.save()
    batch = portfolio.submit_batch(
        owner,
        {
            "expected_revision": 0,
            "batch_key": uuid.uuid4(),
            "template_id": props[0].id,
            "parent_kind": "building",
            "parent_id": building.id,
            "units": [
                {
                    "item_key": uuid.uuid4(),
                    "unit_code": f"A-{i}",
                    "occupancy_capacity": 4,
                }
                for i in range(3, 13)
            ],
        },
    )
    assert batch.complete and len({r["property_id"] for r in batch.results}) == 10
    generated = Property.objects.filter(
        id__in=[r["property_id"] for r in batch.results]
    )
    assert all(not p.is_verified and not p.is_ownership_verified for p in generated)
    # Test fixture review, never an owner-operated verification bypass.
    generated.update(status="verified", is_verified=True, is_ownership_verified=True)
    for unit in generated:
        RentalAvailabilityConfirmation.objects.create(
            property=unit,
            confirmed_by=owner,
            confirmed_at=timezone.now(),
            inventory_revision=(unit.rental_inventory or {}).get("revision", 0),
        )
    employees = User.objects.bulk_create(
        [
            User(
                email=f"synthetic-employee-{i}@example.test",
                first_name="Synthetic",
                last_name=str(i),
                is_verified=True,
                password="!",
            )
            for i in range(40)
        ]
    )
    CompanyMembership.objects.bulk_create(
        [
            CompanyMembership(company=company, user=user, is_employee=True)
            for user in employees
        ]
    )
    request.headcount = 40
    request.save()
    item = bookings.select_offer(
        coordinator,
        request.id,
        {
            "expected_revision": request.revision,
            "offer_id": offer.id,
            "offer_revision": offer.revision,
            "occupant_ids": [user.id for user in employees],
        },
    )
    assert item.snapshot["capacity"] == 48
    assert item.snapshot["reserve_places"] == 8
    assert item.occupants.count() == 40
    assert len(item.snapshot["occupants"]) == 40
    assert item.snapshot["company_name"] == company.name
    assert item.snapshot["requester_name"] == coordinator.get_full_name
    assert all(row["building_name"] == building.name for row in item.snapshot["units"])
    item = approval_routing.submit(
        coordinator, item.id, {"expected_revision": item.revision}
    )
    item = bookings.decide(
        approver,
        item.id,
        {
            "expected_revision": item.revision,
            "snapshot_digest": item.snapshot_digest,
            "decision": "approved",
        },
    )
    assert RentalInventoryDayLock.objects.count() == 0
    item = bookings.hold_item(
        coordinator, item.id, {"expected_revision": item.revision}
    )
    assert item.hold.day_locks.count() == 12 * 31
    assert item.hold.day_locks.values("property").distinct().count() == 12
    for unit in building.units.all():
        with pytest.raises(RentalConflict):
            assert_available(
                unit,
                {"rental_scope": "entire_property"},
                request.starts_on,
                request.ends_on_exclusive,
            )
    assert item.lease_id is None and item.invitation_id is None
    assert not item.assignments.exists()
