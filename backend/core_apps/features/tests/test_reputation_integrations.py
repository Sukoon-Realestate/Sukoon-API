"""Connected corporate, portfolio, ownership and outage contracts."""

import uuid
from datetime import timedelta
import pytest
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied
from core_apps.features.models import (
    Company,
    CompanyMembership,
    CompanyHousingRequest,
    PortfolioOffer,
    CompanyBookingItem,
    CompanyApproval,
    CompanyLeaseBinding,
    EmployeeAssignment,
    RentalEvidence,
    LeaseResponsibilityTransition,
    ReviewCase,
    ReviewSection,
    ReviewSubmission,
    SigningSession,
)
from core_apps.properties.models import ResidentialBuilding, ResidentialComplex
from core_apps.features.services.reputation import (
    company_bindings,
    employee_occupancy,
    company_generation,
    responsibility,
    recovery,
    rollups,
    generation,
    submission,
    visibility,
    ancestry,
)
from core_apps.features.services.reputation.policy import ReviewError
from .test_reputation import actors, stay, body, client, approve


def key(**kw):
    return {"request_key": str(uuid.uuid4()), **kw}


def setup_company(actors, *, signed=True):
    owner, tenant, employee, delegate, *_ = actors
    lease = stay(actors)
    company = Company.objects.create(
        name="Company",
        registration_number="TEST",
        contact_email="company@example.test",
        review_status="verified",
    )
    admin = CompanyMembership.objects.create(
        company=company,
        user=tenant,
        is_admin=True,
        signing_verified_until=timezone.now() + timedelta(days=30),
    )
    other = CompanyMembership.objects.create(
        company=company, user=delegate, is_coordinator=True
    )
    CompanyMembership.objects.create(company=company, user=employee, is_employee=True)
    request = CompanyHousingRequest.objects.create(
        company=company,
        requester=tenant,
        coordinator=delegate,
        title="Housing",
        purpose="Staff",
        location="Cairo",
        starts_on=lease.start_date,
        ends_on_exclusive=lease.end_date,
        headcount=3,
        commitment_ceiling_minor=100000,
        deposit_limit_minor=10000,
    )
    offer = PortfolioOffer.objects.create(
        owner=owner, scope="selected_units", monthly_rent_minor=1000
    )
    item = CompanyBookingItem.objects.create(
        request=request,
        offer=offer,
        snapshot={
            "units": [
                {"id": str(lease.property.id), **ancestry.from_property(lease.property)}
            ]
        },
        snapshot_digest="a" * 64,
        quote_expires_at=timezone.now() + timedelta(days=1),
        full_term_rent_minor=1000,
        deposit_minor=0,
    )
    CompanyApproval.objects.create(
        item=item,
        approver=tenant,
        commercial_revision=1,
        snapshot=item.snapshot,
        snapshot_digest=item.snapshot_digest,
        decision="approved",
        expires_at=timezone.now() + timedelta(days=1),
    )
    if signed:
        lease.document_id, lease.document_hash = uuid.uuid4(), "b" * 64
        lease.save()
        for person in (owner, tenant):
            SigningSession.objects.create(
                lease=lease,
                signer=person,
                status="completed",
                completed_at=timezone.now(),
                document_id=lease.document_id,
                document_hash=lease.document_hash,
                expires_at=timezone.now() + timedelta(days=1),
            )
    return lease, company, admin, other, item


def bind(actors):
    lease, company, admin, other, item = setup_company(actors)
    data = company_bindings.propose(
        actors[1],
        key(
            lease_id=str(lease.id),
            renter_company_id=str(company.id),
            booking_id=str(item.id),
        ),
    )
    for actor, role in [
        (actors[0], "lease_owner"),
        (actors[1], "lease_tenant"),
        (actors[1], "renter_company"),
    ]:
        data = company_bindings.confirm(
            actor, data["id"], key(role=role, expected_revision=data["revision"])
        )
    binding = CompanyLeaseBinding.objects.get(id=data["id"])
    return binding, admin, other


def grant(actor, binding, member, **kw):
    return company_bindings.authority(
        actor,
        binding.id,
        key(
            membership_id=str(member.id),
            expected_revision=0,
            is_active=True,
            can_submit=True,
            can_view_reputation=True,
            **kw,
        ),
    )


def employee_stay(actors, binding):
    assignment = employee_occupancy.assign(
        actors[1],
        binding.id,
        key(
            employee_id=str(actors[2].id),
            starts_on=binding.lease.start_date.isoformat(),
            ends_on=binding.lease.end_date.isoformat(),
        ),
    )
    record = EmployeeAssignment.objects.get(id=assignment["id"])
    for kind, day in [
        ("arrival", binding.lease.start_date),
        ("departure", binding.lease.end_date),
    ]:
        record.refresh_from_db()
        data = employee_occupancy.propose(
            actors[1],
            record.id,
            key(
                expected_revision=record.revision,
                kind=kind,
                possession_on=day.isoformat(),
            ),
        )
        confirmation = next(x for x in data["confirmations"] if x["kind"] == kind)
        for actor, role in [(actors[2], "employee"), (actors[0], "landlord")]:
            data = employee_occupancy.confirm(
                actor,
                confirmation["id"],
                key(expected_revision=confirmation["revision"], role=role),
            )
            confirmation = next(x for x in data["confirmations"] if x["kind"] == kind)
    return record


@pytest.mark.django_db
def test_link_requires_signed_lease_and_three_explicit_confirmations(actors):
    lease, company, _, _, item = setup_company(actors, signed=False)
    with pytest.raises(ReviewError, match="."):
        company_bindings.propose(
            actors[1],
            key(
                lease_id=str(lease.id),
                renter_company_id=str(company.id),
                booking_id=str(item.id),
            ),
        )
    assert not CompanyLeaseBinding.objects.exists()
    item.lease = lease
    item.save()
    with pytest.raises(ReviewError):
        generation.generate_tenancy(lease)
    assert not ReviewCase.objects.exists()


@pytest.mark.django_db
def test_company_has_one_ballot_no_property_vote_and_explicit_authority(actors):
    binding, admin, other = bind(actors)
    case = generation.generate_tenancy(binding.lease)
    opp = case.opportunities.get(reviewer_company=binding.renter_company)
    assert [t["kind"] for t in opp.allowed_targets] == ["person_landlord"]
    with pytest.raises(NotFound):
        submission.opportunity_for(actors[1], opp.id)
    grant(actors[1], binding, admin)
    grant(actors[1], binding, other)
    receipt = submission.submit(actors[1], opp.id, body(opp))
    replay = submission.submit(actors[3], opp.id, body(opp))
    assert replay["id"] == receipt["id"] and replay["already_submitted"]
    assert ReviewSubmission.objects.filter(opportunity=opp).count() == 1
    admin.is_active = False
    admin.save()
    with pytest.raises(NotFound):
        submission.lookup(actors[1], receipt["request_key"])
    assert submission.opportunity_for(actors[3], opp.id).pk == opp.pk


@pytest.mark.django_db
def test_company_shared_draft_revision_and_revocation(actors):
    binding, admin, other = bind(actors)
    case = generation.generate_tenancy(binding.lease)
    opp = case.opportunities.get(reviewer_company=binding.renter_company)
    grant(actors[1], binding, admin)
    grant(actors[1], binding, other)
    url = f"/api/v1/features/v1/reviews/opportunities/{opp.id}/draft/"
    response = client(actors[1]).put(
        url, key(expected_revision=0, payload={"sections": []}), format="json"
    )
    assert response.status_code == 200, response.data
    assert client(actors[3]).get(url).data["revision"] == 1
    assert (
        client(actors[3])
        .put(url, key(expected_revision=0, payload={}), format="json")
        .status_code
        == 409
    )
    admin.is_active = False
    admin.save()
    assert client(actors[1]).get(url).status_code == 404


@pytest.mark.django_db
def test_employee_needs_confirmed_actual_possession_and_independent_gate(actors):
    binding, admin, _ = bind(actors)
    grant(actors[1], binding, admin)
    assignment = employee_stay(actors, binding)
    case = ReviewCase.objects.get(employee_assignment=assignment)
    assert case.release_mode == "deadline" and case.opportunities.count() == 1
    opp = case.opportunities.get()
    assert opp.reviewer_id == actors[2].pk
    with pytest.raises(NotFound):
        submission.opportunity_for(actors[1], opp.id)
    submission.submit(actors[2], opp.id, body(opp))
    case.refresh_from_db()
    assert not case.gate_released_at
    corporate = generation.generate_tenancy(binding.lease)
    for co in corporate.opportunities.all():
        submission.submit(
            actors[1] if co.reviewer_company_id else actors[0], co.id, body(co)
        )
    assert not visibility.released(case)
    assignment.starts_on += timedelta(days=1)
    assignment.save()
    from core_apps.features.services.reputation.eligibility import valid_source

    assert not valid_source(case)


@pytest.mark.django_db
def test_assignment_alone_is_not_occupancy_and_coordinator_cannot_confirm_for_employee(
    actors,
):
    binding, _, _ = bind(actors)
    data = employee_occupancy.assign(
        actors[1],
        binding.id,
        key(
            employee_id=str(actors[2].id),
            starts_on=binding.lease.start_date.isoformat(),
            ends_on=binding.lease.end_date.isoformat(),
        ),
    )
    assignment = EmployeeAssignment.objects.get(id=data["id"])
    with pytest.raises(ReviewError):
        company_generation.generate_employee(assignment)
    data = employee_occupancy.propose(
        actors[1],
        assignment.id,
        key(
            expected_revision=1,
            kind="arrival",
            possession_on=binding.lease.start_date.isoformat(),
        ),
    )
    with pytest.raises(NotFound):
        employee_occupancy.confirm(
            actors[1],
            data["confirmations"][0]["id"],
            key(expected_revision=1, role="employee"),
        )


def container(actors, name):
    complex_ = ResidentialComplex.objects.create(
        manager=actors[0], name=name, code=name, address="Cairo"
    )
    building = ResidentialBuilding.objects.create(
        manager=actors[0],
        complex=complex_,
        name=name,
        code=name,
        address="Cairo",
        declared_units=2,
    )
    return building, complex_


@pytest.mark.django_db
def test_rollups_retain_old_parent_and_withdrawal_updates_every_level(actors):
    original, complex_ = container(actors, "Original")
    other, _ = container(actors, "Other")
    prop = actors[-1]
    prop.building = original
    prop.save()
    lease = stay(actors)
    start = lease.handovers.get(kind="move_in")
    start.context_snapshot = ancestry.from_property(prop)
    start.save()
    prop.building = other
    prop.save()
    case = generation.generate_tenancy(lease)
    for opp in case.opportunities.all():
        submission.submit(
            opp.reviewer,
            opp.id,
            body(
                opp, target="property" if opp.reviewer_id == actors[1].pk else "tenant"
            ),
        )
    ReviewSection.objects.all().update(content_state="approved")
    assert rollups.summary("building", original.id)["review_count"] == 1
    assert rollups.summary("complex", complex_.id)["distinct_unit_count"] == 1
    assert rollups.summary("building", other.id)["review_count"] == 0
    assert any(x["historical"] for x in rollups.property_links(prop.id))
    ReviewSection.objects.filter(subject_kind="property_stay").update(
        content_state="withdrawn"
    )
    assert rollups.summary("complex", complex_.id)["average"] is None


@pytest.mark.django_db
def test_unknown_historical_parent_never_backfilled_from_current_listing(actors):
    building, _ = container(actors, "Current")
    actors[-1].building = building
    actors[-1].save()
    case = generation.generate_tenancy(stay(actors))
    assert not case.source_snapshot.get("building_id")


def proof(actors, lease):
    return RentalEvidence.objects.create(
        lease=lease,
        uploader=actors[1],
        request_key=uuid.uuid4(),
        original_name="ownership.pdf",
        content_type="application/pdf",
        size_bytes=10,
        sha256="a" * 64,
        storage_key=str(uuid.uuid4()),
        malware_status="safe",
    )


def transfer(actors, lease):
    prop = lease.property
    prop.owner, prop.is_ownership_verified = actors[3], True
    prop.save()
    data = responsibility.propose(
        actors[1],
        lease.id,
        key(
            effective_on=(lease.start_date + timedelta(days=5)).isoformat(),
            evidence_id=str(proof(actors, lease).id),
        ),
    )
    for actor in (actors[0], actors[1], actors[3]):
        data = responsibility.confirm(
            actor, data["id"], key(expected_revision=data["revision"])
        )
    return data


@pytest.mark.django_db
def test_ownership_change_splits_period_and_keeps_original_owner_reputation(actors):
    lease = stay(actors)
    result = transfer(actors, lease)
    assert result["state"] == "accepted"
    cases = list(
        ReviewCase.objects.filter(revocation_reason="").order_by(
            "source_snapshot__starts_on"
        )
    )
    assert len(cases) == 2
    assert {c.party_b_id for c in cases} == {actors[0].pk, actors[3].pk}
    lease.refresh_from_db()
    assert lease.owner_id == actors[0].pk
    from core_apps.features.services.reputation.eligibility import valid_source

    assert all(valid_source(c) for c in cases)
    generation.generate_tenancy(lease)
    assert ReviewCase.objects.count() == 2


@pytest.mark.django_db
def test_ownership_can_close_period_before_tenant_moves_out(actors):
    lease = stay(actors, end=False)
    transfer(actors, lease)
    assert ReviewCase.objects.count() == 1
    assert ReviewCase.objects.get().party_b_id == actors[0].pk


@pytest.mark.django_db
def test_ownership_cannot_rewrite_submitted_review(actors):
    lease = stay(actors)
    case = generation.generate_tenancy(lease)
    opp = case.opportunities.get(reviewer=actors[1])
    submission.submit(actors[1], opp.id, body(opp))
    with pytest.raises(ReviewError):
        transfer(actors, lease)
    assert not LeaseResponsibilityTransition.objects.exists()


def outage(lease):
    end = lease.handovers.get(kind="move_out")
    return key(
        source_kind="tenancy",
        source_id=str(lease.id),
        reason="Restored after worker outage",
        incident_reference="OPS-TEST",
        outage_started_at=(end.accepted_at - timedelta(hours=1)).isoformat(),
        outage_ended_at=min(
            timezone.now(), end.accepted_at + timedelta(hours=1)
        ).isoformat(),
    )


@pytest.mark.django_db
def test_old_outage_recovery_uses_real_source_full_window_and_receipt(actors):
    lease = stay(actors, nights=80)
    lease.handovers.filter(kind="move_out").update(
        accepted_at=timezone.now() - timedelta(days=40)
    )
    with pytest.raises(ReviewError):
        generation.generate_tenancy(lease)
    data = outage(lease)
    result = recovery.recover(actors[4], data)
    case = ReviewCase.objects.get(id=result["id"])
    assert (case.closes_at - case.opens_at).days == 30
    assert case.source_snapshot["generation_reason"] == "audited_outage_recovery"
    assert recovery.recover(actors[4], data) == result
    with pytest.raises(PermissionDenied):
        recovery.recover(actors[0], data)


@pytest.mark.django_db
def test_pair_extension_never_reopens_deadline_or_published_review(actors):
    lease = stay(actors)
    case = generation.generate_tenancy(lease)
    data = outage(lease) | {"expected_revision": case.revision, "extension_days": 2}
    recovery.extend(actors[4], case.id, data)
    case.refresh_from_db()
    assert (case.closes_at - case.opens_at).days == 32
    case.opens_at = timezone.now() - timedelta(days=31)
    case.closes_at = timezone.now() - timedelta(seconds=1)
    case.save()
    with pytest.raises(ReviewError):
        recovery.extend(
            actors[4],
            case.id,
            {**outage(lease), "expected_revision": case.revision, "extension_days": 2},
        )


@pytest.mark.django_db
def test_company_history_is_scoped_and_employees_never_become_private_tenants(actors):
    binding, admin, other = bind(actors)
    grant(actors[1], binding, admin)
    case = generation.generate_tenancy(binding.lease)
    for opp in case.opportunities.all():
        submission.submit(
            actors[1] if opp.reviewer_company_id else actors[0], opp.id, body(opp)
        )
    ReviewSection.objects.all().update(content_state="approved")
    assert (
        visibility.summary("organization_renter", binding.renter_company.id, actors[1])[
            "review_count"
        ]
        == 1
    )
    with pytest.raises(NotFound):
        visibility.summary("organization_renter", binding.renter_company.id, actors[3])
    assert not ReviewSection.objects.filter(subject_kind="person_tenant").exists()
    with pytest.raises(NotFound):
        visibility.summary("person_tenant", actors[2].id, actors[1])


@pytest.mark.django_db
def test_revoked_company_admin_cannot_read_experience_operation_receipt(actors):
    binding, admin, other = bind(actors)
    payload = key(
        membership_id=str(other.id),
        expected_revision=0,
        is_active=True,
        can_submit=True,
        can_view_reputation=False,
    )
    company_bindings.authority(actors[1], binding.id, payload)
    admin.is_active = False
    admin.save()
    with pytest.raises(NotFound):
        submission.lookup(actors[1], payload["request_key"])


@pytest.mark.django_db
def test_real_employee_property_votes_keep_one_distinct_company_experience(actors):
    from core_apps.users.models import User

    binding, _, _ = bind(actors)
    for index in range(4):
        employee = User.objects.create_user(
            email=f"occupant-{index}@example.test", is_verified=True
        )
        CompanyMembership.objects.create(
            company=binding.renter_company, user=employee, is_employee=True
        )
        current = list(actors)
        current[2] = employee
        assignment = employee_stay(current, binding)
        case = ReviewCase.objects.get(employee_assignment=assignment)
        opp = case.opportunities.get()
        submission.submit(employee, opp.id, body(opp, target="property"))
        case.opens_at = timezone.now() - timedelta(days=31)
        case.closes_at = timezone.now() - timedelta(seconds=1)
        case.save()
    ReviewSection.objects.all().update(content_state="approved")
    result = visibility.summary("property_stay", binding.lease.property.id)
    assert result["review_count"] == 4
    assert result["distinct_experience_count"] == 1


@pytest.mark.django_db
def test_company_landlord_replies_remain_with_authorized_company(actors):
    lease, company, admin, other, _ = setup_company(actors)
    data = company_bindings.propose(
        actors[0], key(lease_id=str(lease.id), landlord_company_id=str(company.id))
    )
    for actor, role in [
        (actors[0], "lease_owner"),
        (actors[1], "lease_tenant"),
        (actors[1], "landlord_company"),
    ]:
        data = company_bindings.confirm(
            actor, data["id"], key(role=role, expected_revision=data["revision"])
        )
    binding = CompanyLeaseBinding.objects.get(id=data["id"])
    # The tenant cannot act for the opposing landlord company even if delegated.
    grant(actors[1], binding, other)
    case = generation.generate_tenancy(lease)
    assert (
        case.opportunities.get(reviewer=actors[1]).allowed_targets[0]["kind"]
        == "organization_landlord"
    )
    for opp in case.opportunities.all():
        submission.submit(
            actors[3] if opp.reviewer_company_id else actors[1], opp.id, body(opp)
        )
    ReviewSection.objects.all().update(content_state="approved")
    section = ReviewSection.objects.get(subject_kind="organization_landlord")
    from core_apps.features.services.reputation import moderation

    result = moderation.section_action(
        actors[3],
        section.id,
        "reply",
        key(expected_revision=section.revision, comment="We appreciate the feedback."),
    )
    assert section.reply.author_company_id == company.pk
    other.is_active = False
    other.save()
    with pytest.raises(NotFound):
        moderation.withdraw_reply(actors[3], result["id"], key(expected_revision=1))


@pytest.mark.django_db(transaction=True)
def test_two_delegates_concurrently_submit_only_one_company_ballot(actors):
    from concurrent.futures import ThreadPoolExecutor
    from django.db import connections

    binding, admin, other = bind(actors)
    grant(actors[1], binding, admin)
    grant(actors[1], binding, other)
    case = generation.generate_tenancy(binding.lease)
    opp = case.opportunities.get(reviewer_company=binding.renter_company)

    def send(user):
        try:
            return submission.submit(user, opp.id, body(opp))
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(send, [actors[1], actors[3]]))
    assert responses[0]["id"] == responses[1]["id"]
    assert ReviewSubmission.objects.filter(opportunity=opp).count() == 1


@pytest.mark.django_db
def test_experience_api_owner_employee_authority_and_public_rollup_contract(actors):
    binding, admin, _ = bind(actors)
    grant(actors[1], binding, admin)
    assignment = employee_stay(actors, binding)
    base = "/api/v1/features/v1/reviews/"
    for user, suffix in [
        (actors[0], f"company-bindings/{binding.id}/assignments/"),
        (actors[2], "employee-assignments/"),
        (actors[1], f"company-bindings/{binding.id}/"),
    ]:
        response = client(user).get(base + suffix)
        assert response.status_code == 200, response.data
        assert response["Cache-Control"] == "private, no-store"
        assert set(response.json()) == {"message", "data"}
    assert (
        client(actors[3])
        .get(base + f"employee-assignments/{assignment.id}/")
        .status_code
        == 200
    )  # assigned coordinator
    assert (
        client(actors[5])
        .get(base + f"employee-assignments/{assignment.id}/")
        .status_code
        == 404
    )
    building, _ = container(actors, "Public")
    response = client(None).get(base + f"portfolios/building/{building.id}/summary/")
    assert response.status_code == 200
    assert response.json()["data"]["average"] is None
    response = client(actors[1]).post(
        base + "company-bindings/", key(lease_id="not-a-uuid"), format="json"
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_safe_ancestry_backfill_never_guesses_and_is_repeatable(actors):
    from django.core.management import call_command

    building, _ = container(actors, "Historical")
    lease = stay(actors)
    lease.offer_snapshot = {
        **lease.offer_snapshot,
        "building_id": str(building.id),
        "building_name": building.name,
    }
    lease.save()
    case = generation.generate_tenancy(lease)
    case.source_snapshot.pop("building_id")
    case.source_snapshot.pop("building_name")
    case.save()
    call_command("backfill_review_ancestry")
    call_command("backfill_review_ancestry")
    case.refresh_from_db()
    assert case.source_snapshot["building_id"] == str(building.id)
    assert lease.handovers.get(kind="move_in").context_snapshot["building_id"] == str(
        building.id
    )


@pytest.mark.django_db
def test_lease_action_does_not_offer_a_personal_ballot_to_company_representative(
    actors,
):
    from core_apps.features.services.reputation.eligibility import can_review_lease

    binding, _, _ = bind(actors)
    assert not can_review_lease(binding.lease, actors[1])
    assert can_review_lease(binding.lease, actors[0])


@pytest.mark.django_db
def test_outage_recovery_for_old_confirmed_housemates(actors):
    first = stay(actors, nights=80)
    second = stay(actors, tenant=actors[2], nights=80)
    past = timezone.now() - timedelta(days=40)
    for lease in (first, second):
        lease.handovers.filter(kind="move_out").update(accepted_at=past)
    result = recovery.recover(
        actors[4],
        {**outage(first), "source_kind": "co_living", "peer_lease_id": str(second.id)},
    )
    case = ReviewCase.objects.get(id=result["id"])
    assert case.context_type == "co_living" and case.opportunities.count() == 2
    assert (case.closes_at - case.opens_at).days == 30


@pytest.mark.django_db(transaction=True)
def test_concurrent_bindings_cannot_split_one_renewed_tenancy_between_companies(actors):
    from concurrent.futures import ThreadPoolExecutor
    from django.db import connections

    first, company_a, _, _, booking_a = setup_company(actors)
    second, company_b, _, _, booking_b = setup_company(actors)
    second.tenancy_root_id = first.tenancy_root_id
    second.save()

    def propose(args):
        user, lease, company, booking = args
        try:
            return company_bindings.propose(
                user,
                key(
                    lease_id=str(lease.id),
                    renter_company_id=str(company.id),
                    booking_id=str(booking.id),
                ),
            )["id"]
        except ReviewError as error:
            return error.get_codes()
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(
                propose,
                [
                    (actors[0], first, company_a, booking_a),
                    (actors[1], second, company_b, booking_b),
                ],
            )
        )
    assert results.count("revision_conflict") == 1
    assert CompanyLeaseBinding.objects.count() == 1
