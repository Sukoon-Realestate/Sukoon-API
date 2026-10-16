"""Synthetic academic journeys over canonical groups and PostgreSQL transactions."""

import copy
import hashlib
import io
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
import pytest
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection, connections
from django.utils import timezone
from config.student_housing import SERVICES
from core_apps.features.models import (
    AcademicHousingPlan,
    AcademicRequirementRevision,
    Campus,
    University,
    RentalEvidence,
    RentalVerificationClaim,
    Lease,
    HousingRequest,
    GroupMembership,
    GroupInvitation,
    HousingGroup,
    StudentOfferPolicy,
    RentalOperationalCase,
)
from core_apps.features.services.student_housing.profiles import enrollment
from core_apps.features.services.student_housing.policies import validate_occupants
from core_apps.features.services.rental_phase2 import RentalConflict
from core_apps.features.tests.test_rental_phase2 import (
    rental_participants,
    authenticated,
)
from core_apps.features.tests.test_rental_lifecycle import command

API = "/api/v1/features/v1/"


@pytest.fixture(autouse=True)
def student_capabilities(settings):
    settings.STUDENT_ENABLED_SERVICES = list(SERVICES)


def post(user, path, data, expected=200):
    result = authenticated(user).post(API + path, data, format="json")
    assert result.status_code == expected, result.data
    wire = result.json()
    if expected < 400:
        assert set(wire) == {"message", "data"}
        assert isinstance(wire["message"], str) and wire["message"]
        assert result["Cache-Control"] == "private, no-store"
    return result


def plan_body(tenant, prop, *, group=None, people=None, **overrides):
    start = timezone.localdate() + timedelta(days=10)
    values = dict(
        label="Synthetic semester",
        period_kind="semester",
        starts_on=str(start),
        ends_on_exclusive=str(start + timedelta(days=120)),
        budget_basis="per_person",
        criteria={
            "city_id": str(prop.city.id),
            "rental_scope": "room_group" if group else "room",
            "price_period": "monthly",
            "budget_min": {"amount_minor": 100000, "currency": "EGP"},
            "budget_max": {"amount_minor": 500000, "currency": "EGP"},
        },
        requirements={},
        participant_ids=[str(u.id) for u in (people or [tenant])],
        group_id=str(group.id) if group else None,
    )
    values.update(overrides)
    return command(**values)


def create_plan(tenant, prop, **values):
    return post(tenant, "academic-plans/", plan_body(tenant, prop, **values), 201).data[
        "resource"
    ]


def read(user, identifier):
    response = authenticated(user).get(API + f"academic-plans/{identifier}/")
    assert response.status_code == 200, response.data
    return response.data


def requirements(user, plan, **values):
    return post(
        user,
        f"academic-plans/{plan['id']}/requirements/",
        command(
            plan["revision"],
            requirements=values,
            budget_min={"amount_minor": 100000, "currency": "EGP"},
            budget_max={"amount_minor": 500000, "currency": "EGP"},
            owner_disclosures=["campuses", "affordability"],
        ),
    ).data["resource"]


def review(user, plan):
    return post(
        user,
        f"academic-plans/{plan['id']}/review/",
        command(plan["revision"], consent=True, digest=plan["digest"]),
    ).data["resource"]


def publish(user, plan):
    preview = (
        authenticated(user)
        .get(API + f"academic-plans/{plan['id']}/publication-preview/")
        .data
    )
    return post(
        user,
        f"academic-plans/{plan['id']}/publish/",
        command(
            plan["revision"],
            consent=True,
            digest=preview["publication_preview"]["preview_digest"],
        ),
    ).data["resource"]


@pytest.fixture
def group(rental_participants):
    _, tenant, member, _, _ = rental_participants
    group = HousingGroup.objects.create(name="Synthetic existing group", capacity=4)
    GroupMembership.objects.create(
        group=group, user=tenant, role="admin", joined_revision=1
    )
    GroupMembership.objects.create(group=group, user=member, joined_revision=1)
    return group


@pytest.mark.django_db
def test_solo_plan_demand_and_next_year_preserve_snapshot(rental_participants):
    owner, tenant, stranger, prop, _ = rental_participants
    plan = create_plan(tenant, prop)
    plan = review(tenant, requirements(tenant, plan))
    publish(tenant, plan)
    demand = HousingRequest.objects.get(academic_plan__id=plan["id"])
    original = copy.deepcopy(demand.academic_snapshot)
    assert demand.user == tenant and demand.criteria["people"] == 1
    assert demand.academic_snapshot["budget_basis"] == "per_person"
    assert demand.criteria["budget_max"]["amount_minor"] == 500000
    owner_read = authenticated(owner).get(API + f"housing-requests/{demand.id}/")
    assert owner_read.status_code == 200
    assert "participant_ids" not in owner_read.data["academic_context"]
    assert "student_evidence" not in str(owner_read.data)
    assert (
        authenticated(stranger).get(API + f"academic-plans/{plan['id']}/").status_code
        == 404
    )
    next_plan = create_plan(
        tenant,
        prop,
        previous_plan_id=plan["id"],
        period_kind="academic_year",
        label="Synthetic next year",
    )
    assert next_plan["id"] != plan["id"]
    demand.refresh_from_db()
    assert demand.academic_snapshot == original
    assert AcademicHousingPlan.objects.count() == 2


@pytest.mark.django_db
def test_canonical_group_reuse_and_participation_subset(rental_participants, group):
    _, tenant, member, prop, _ = rental_participants
    before = (GroupMembership.objects.count(), GroupInvitation.objects.count())
    first = create_plan(tenant, prop, group=group, people=[tenant])
    second = create_plan(tenant, prop, group=group, people=[member])
    assert first["group_id"] == second["group_id"] == str(group.id)
    assert (GroupMembership.objects.count(), GroupInvitation.objects.count()) == before
    assert len(first["participants"]) == len(second["participants"]) == 1
    assert group.memberships.count() == 2
    assert (
        authenticated(member).get(API + f"academic-plans/{first['id']}/").status_code
        == 200
    )


@pytest.mark.django_db
def test_individual_consents_different_campuses_and_revisions(
    rental_participants, group
):
    _, tenant, member, prop, _ = rental_participants
    university = University.objects.create(
        name_en="Synthetic institution", name_ar="جامعة اختبار"
    )
    campuses = [
        Campus.objects.create(
            university=university,
            name_en=f"Synthetic {i}",
            name_ar="فرع اختبار",
            city=prop.city,
        )
        for i in range(2)
    ]
    plan = create_plan(tenant, prop, group=group, people=[tenant, member])
    plan = requirements(tenant, plan, campus_ids=[str(campuses[0].id)])
    plan = requirements(member, plan, campus_ids=[str(campuses[1].id)])
    plan = review(tenant, plan)
    assert "waiting_for_consent" in plan["blocking_reasons"]
    post(
        tenant,
        f"academic-plans/{plan['id']}/review/",
        command(
            plan["revision"],
            consent=True,
            digest=plan["digest"],
            user_id=str(member.id),
        ),
        400,
    )
    plan = review(member, plan)
    assert not plan["blocking_reasons"]
    assert len({p["requirements"]["campus_ids"][0] for p in plan["participants"]}) == 2
    plan = publish(tenant, plan)
    request = HousingRequest.objects.get(academic_plan__id=plan["id"])
    assert len(request.academic_snapshot["participant_requirements"]) == 2
    old_revision = request.academic_revision
    plan = requirements(member, plan, internet="Unmetered connection requested")
    assert "waiting_for_consent" in plan["blocking_reasons"]
    request.refresh_from_db()
    assert request.academic_revision == old_revision
    assert AcademicRequirementRevision.objects.filter(plan__id=plan["id"]).count() == 4


@pytest.mark.django_db
def test_membership_revocation_and_receipt_cannot_bypass(rental_participants, group):
    _, tenant, member, prop, _ = rental_participants
    plan = create_plan(tenant, prop, group=group, people=[tenant, member])
    body = command(
        plan["revision"],
        requirements={},
        budget_min={"amount_minor": 1},
        budget_max={"amount_minor": 2},
        owner_disclosures=[],
    )
    post(member, f"academic-plans/{plan['id']}/requirements/", body)
    GroupMembership.objects.filter(group=group, user=member).update(status="left")
    assert (
        authenticated(member).get(API + f"academic-plans/{plan['id']}/").status_code
        == 404
    )
    post(member, f"academic-plans/{plan['id']}/requirements/", body, 404)
    result = authenticated(member).get(
        API + f"rental-operations/{body['request_key']}/", {"subject_id": plan["id"]}
    )
    assert result.status_code == 404
    assert "membership_revoked" in read(tenant, plan["id"])["blocking_reasons"]


@pytest.mark.django_db
def test_profile_is_not_enrollment_and_does_not_edit_published_request(
    rental_participants,
):
    _, tenant, _, prop, _ = rental_participants
    plan = publish(
        tenant, review(tenant, requirements(tenant, create_plan(tenant, prop)))
    )
    demand = HousingRequest.objects.get(academic_plan__id=plan["id"])
    original = copy.deepcopy(demand.academic_snapshot)
    result = post(
        tenant,
        "student-profile/",
        command(enrollment_status="enrolled", institution_name="Synthetic university"),
    )
    assert result.data["resource"]["identity_verified"] is True
    assert result.data["resource"]["student_verification"]["status"] == "unverified"
    demand.refresh_from_db()
    assert demand.academic_snapshot == original


@pytest.mark.django_db
def test_ordinary_group_archive_retired_and_no_academic_requirement(
    rental_participants, group
):
    _, tenant, _, _, _ = rental_participants
    response = authenticated(tenant).get(API + f"housing-groups/{group.id}/")
    assert response.status_code == 200
    assert "archive" not in response.data["allowed_actions"]
    assert "unarchive" not in response.data["allowed_actions"]
    assert not AcademicHousingPlan.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field,value",
    [
        ("budget_basis", "per_semester"),
        ("ends_on_exclusive", "2000-01-01"),
        ("period_kind", "guaranteed_admission"),
    ],
)
def test_invalid_plan_contracts_rejected(rental_participants, field, value):
    _, tenant, _, prop, _ = rental_participants
    post(tenant, "academic-plans/", plan_body(tenant, prop, **{field: value}), 400)
    assert not AcademicHousingPlan.objects.exists()


@pytest.mark.django_db
def test_shared_living_and_exam_acceptance_has_no_lease_effect(
    rental_participants, group
):
    _, tenant, member, prop, _ = rental_participants
    plan = create_plan(tenant, prop, group=group, people=[tenant, member])
    body = command(
        plan_revision=plan["revision"],
        kind="exam",
        starts_on=plan["starts_on"],
        ends_on_exclusive=plan["ends_on_exclusive"],
        rules={"quiet_hours": "22:00–07:00"},
    )
    value = post(tenant, f"academic-plans/{plan['id']}/arrangements/", body, 201).data[
        "resource"
    ]
    value = post(
        tenant,
        f"student-arrangements/{value['id']}/decide/",
        command(value["revision"], consent=True, digest=value["digest"]),
    ).data["resource"]
    assert value["status"] == "proposed"
    value = post(
        member,
        f"student-arrangements/{value['id']}/decide/",
        command(value["revision"], consent=True, digest=value["digest"]),
    ).data["resource"]
    assert value["status"] == "accepted"
    assert (
        value["lease_effect"] == "none"
        and not value["grants_access"]
        and not value["creates_financial_obligation"]
    )
    assert not Lease.objects.exists()


@pytest.mark.django_db
def test_private_enrollment_evidence_and_scoped_review(rental_participants):
    owner, tenant, stranger, _, _ = rental_participants
    value = post(
        tenant, "student-profile/", command(enrollment_status="admission_pending")
    ).data["resource"]
    image = io.BytesIO()
    Image.new("RGB", (2, 2)).save(image, format="PNG")
    content = image.getvalue()
    data = {
        "request_key": str(uuid.uuid4()),
        "sha256": hashlib.sha256(content).hexdigest(),
        "file": SimpleUploadedFile("admission.png", content, content_type="image/png"),
    }
    response = authenticated(tenant).post(
        API + "student-evidence/upload/", data, format="multipart"
    )
    assert response.status_code == 201, response.data
    evidence = RentalEvidence.objects.get(id=response.data["resource"]["id"])
    assert evidence.lease_id is None and evidence.purpose == "student"
    case = RentalOperationalCase.objects.get(
        source_key=f"student-evidence:{evidence.id}"
    )
    assert case.team == "verification" and case.evidence.filter(pk=evidence.pk).exists()
    assert case.next_action and case.due_at and case.status == "open"
    from core_apps.admin_api.models import StaffProfile
    from core_apps.features.services.rental_lifecycle.cases import case_queryset

    StaffProfile.objects.create(user=stranger, role_name="support")
    assert not case_queryset(stranger).filter(pk=case.pk).exists()
    assert case_queryset(tenant).filter(pk=case.pk).exists()
    for viewer in [owner, stranger]:
        assert (
            authenticated(viewer)
            .get(API + f"student-evidence/{evidence.id}/")
            .status_code
            == 404
        )
        assert (
            authenticated(viewer)
            .get(API + f"rental-evidence/{evidence.id}/")
            .status_code
            == 404
        )
    from core_apps.features.tasks import scan_rental_evidence

    scan_rental_evidence()
    assert (
        authenticated(tenant).get(API + f"student-evidence/{evidence.id}/").status_code
        == 200
    )
    body = command(
        value["revision"],
        evidence_id=str(evidence.id),
        claim_code="admission",
        expires_at=(timezone.now() + timedelta(days=90)).isoformat(),
        note="Synthetic reviewer fixture",
    )
    post(owner, f"operations/student-verifications/{value['id']}/review/", body, 403)
    owner.is_superuser = True
    owner.save(update_fields=["is_superuser"])
    value = post(
        owner, f"operations/student-verifications/{value['id']}/review/", body
    ).data["resource"]
    assert value["student_verification"]["status"] == "admission"
    case.refresh_from_db()
    assert case.status == "resolved" and case.assigned_to == owner
    assert str(case.id) in value["review_case_ids"]
    assert enrollment(tenant) is None
    assert enrollment(tenant, allow_admission=True) is not None
    RentalVerificationClaim.objects.update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    assert enrollment(tenant, allow_admission=True) is None


@pytest.mark.django_db
def test_mixed_occupants_explicit_eligibility(rental_participants):
    owner, tenant, member, prop, offer_id = rental_participants
    start = timezone.localdate() + timedelta(days=2)
    end = start + timedelta(days=30)
    StudentOfferPolicy.objects.create(
        property=prop,
        offer_id=offer_id,
        offer_revision=2,
        eligibility="current_enrollment",
        starts_on=start,
        ends_on_exclusive=end,
        expires_at=timezone.now() + timedelta(days=1),
        recorded_by=owner,
    )
    with pytest.raises(RentalConflict):
        validate_occupants(
            prop,
            {"offer_id": offer_id, "offer_revision": 2},
            [tenant, member],
            start,
            end,
        )
    assert GroupMembership.objects.count() == 0


@pytest.mark.django_db
def test_disabled_capabilities_and_no_fake_production_promises(
    rental_participants, settings
):
    _, tenant, _, _, _ = rental_participants
    settings.STUDENT_ENABLED_SERVICES = []
    assert authenticated(tenant).get(API + "academic-plans/").status_code == 403
    settings.STUDENT_ENABLED_SERVICES = list(SERVICES)
    settings.RENTAL_RUNTIME_ENVIRONMENT = "production"
    response = authenticated(tenant).get(
        API + "planning-capabilities/", {"capability": "student_verification"}
    )
    assert "student_verification" not in response.data["verified_services"]
    config = response.data["configuration"]["student_housing"]
    assert not any(
        config[key]
        for key in [
            "ambassadors",
            "partner_services",
            "conditional_group_booking",
            "family_payment_delegation",
            "admission_refund_guarantee",
        ]
    )
    assert authenticated(tenant).get(API + "academic-plans/").status_code == 200


@pytest.mark.django_db(transaction=True)
def test_concurrent_participant_updates_are_serialized(rental_participants, group):
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL row locking")
    _, tenant, member, prop, _ = rental_participants
    plan = create_plan(tenant, prop, group=group, people=[tenant, member])
    barrier = Barrier(2)

    def submit(user):
        try:
            barrier.wait(timeout=10)
            return (
                authenticated(user)
                .post(
                    API + f"academic-plans/{plan['id']}/requirements/",
                    command(
                        plan["revision"],
                        requirements={},
                        budget_min={"amount_minor": 1},
                        budget_max={"amount_minor": 2},
                        owner_disclosures=[],
                    ),
                    format="json",
                )
                .status_code
            )
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(submit, [tenant, member]))
    assert sorted(results) == [200, 409]
    assert AcademicRequirementRevision.objects.filter(plan__id=plan["id"]).count() == 2
