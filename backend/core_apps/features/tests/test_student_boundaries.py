"""Academic policy, evidence and historical privacy regression tests."""

from copy import deepcopy
import uuid
from datetime import timedelta
import pytest
from django.utils import timezone
from django.db import IntegrityError, transaction
from core_apps.features.models import (
    HousingRequest,
    HousingOffer,
    Lease,
    RentalSummaryGrant,
    Campus,
    University,
    RentalEvidence,
    RentalVerificationClaim,
)
from .test_student_housing import (
    API,
    student_capabilities,
    group,
    create_plan,
    plan_body,
    post,
    requirements,
    review,
    publish,
    read,
)
from .test_student_journeys import inventory, reviewed_plan, response_for, artifact
from .test_rental_phase2 import rental_participants, authenticated
from .test_rental_lifecycle import command
from .test_planning_cycles import criteria_for
from .test_planning_boundaries import current_lease, transition_body
from .test_funded_settlement import funded_exit
from .test_current_cycle_contract import awaiting_signatures
from core_apps.features.services.student_housing.profiles import enrollment


@pytest.mark.django_db
def test_changed_affiliation_requires_review_without_mutating_valid_tenancy(
    current_lease,
):
    owner, tenant, _, lease = current_lease
    original = (
        lease.status,
        lease.revision,
        lease.occupancy_status,
        deepcopy(lease.terms),
    )
    profile = post(
        tenant,
        "student-profile/",
        command(enrollment_status="enrolled", institution_name="Synthetic institution"),
    ).data["resource"]
    evidence = RentalEvidence.objects.create(
        uploader=tenant,
        purpose="student",
        original_name="synthetic.png",
        content_type="image/png",
        request_key=uuid.uuid4(),
        size_bytes=1,
        sha256="a" * 64,
        storage_key="synthetic-private-evidence",
        malware_status="safe",
    )
    claim = RentalVerificationClaim.objects.create(
        subject_kind="student_enrollment",
        subject_user=tenant,
        student_evidence=evidence,
        claim_code="enrollment",
        reviewer=owner,
        public_wording="Synthetic student review",
        evidence_reference=str(evidence.id),
        checked_at=timezone.now(),
        expires_at=timezone.now() + timedelta(days=30),
    )
    assert enrollment(tenant) == claim
    profile = post(
        tenant,
        "student-profile/",
        command(
            profile["revision"],
            enrollment_status="enrolled",
            institution_name="Synthetic institution",
            preferences={"study_times": "Evening"},
        ),
    ).data["resource"]
    assert enrollment(tenant) == claim
    RentalVerificationClaim.objects.filter(pk=claim.pk).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    assert enrollment(tenant) is None
    lease.refresh_from_db()
    assert (
        lease.status,
        lease.revision,
        lease.occupancy_status,
        lease.terms,
    ) == original
    RentalVerificationClaim.objects.filter(pk=claim.pk).update(
        expires_at=timezone.now() + timedelta(days=30)
    )
    changed = post(
        tenant,
        "student-profile/",
        command(
            profile["revision"],
            enrollment_status="enrolled",
            institution_name="A different synthetic institution",
        ),
    ).data["resource"]
    assert changed["student_verification"]["status"] == "unverified"
    claim.refresh_from_db()
    assert (
        claim.revoked_at
        and RentalVerificationClaim.objects.filter(pk=claim.pk).exists()
    )
    lease.refresh_from_db()
    assert (
        lease.status,
        lease.revision,
        lease.occupancy_status,
        lease.terms,
    ) == original


@pytest.mark.django_db
def test_campus_requires_a_complete_valid_coordinate_pair(rental_participants):
    _, _, _, prop, _ = rental_participants
    university = University.objects.create(name_en="Synthetic", name_ar="اختبار")
    for coordinates in [
        dict(latitude=30),
        dict(longitude=31),
        dict(latitude=91, longitude=31),
    ]:
        with pytest.raises(IntegrityError), transaction.atomic():
            Campus.objects.create(
                university=university,
                city=prop.city,
                name_en="Synthetic",
                name_ar="اختبار",
                **coordinates,
            )
    assert (
        Campus.objects.create(
            university=university, city=prop.city, name_en="Unknown", name_ar="اختبار"
        ).latitude
        is None
    )


@pytest.mark.django_db
def test_completed_period_keeps_history_but_rejects_new_consent(rental_participants):
    _, tenant, _, prop, _ = rental_participants
    plan = reviewed_plan(tenant, prop, [tenant])
    completed = post(
        tenant, f"academic-plans/{plan['id']}/complete/", command(plan["revision"])
    ).data["resource"]
    response = post(
        tenant,
        f"academic-plans/{plan['id']}/review/",
        command(completed["revision"], consent=True, digest=completed["digest"]),
        409,
    )
    assert response["X-App-Error-Code"] == "plan_completed"
    assert read(tenant, plan["id"])["status"] == "completed"


@pytest.mark.django_db
def test_offer_policy_is_immutable_and_new_revision_requires_response_review(
    rental_participants,
):
    owner, tenant, _, prop, offer_id = rental_participants
    inventory(prop)
    start = timezone.localdate() + timedelta(days=10)
    body = command(
        offer_id=offer_id,
        offer_revision=2,
        eligibility="open",
        period_kinds=["semester"],
        starts_on=str(start),
        ends_on_exclusive=str(start + timedelta(days=150)),
        expires_at=(timezone.now() + timedelta(days=7)).isoformat(),
        exam_extension_requests=True,
    )
    policy = post(owner, f"properties/{prop.id}/student-policies/", body).data[
        "resource"
    ]
    plan = reviewed_plan(
        tenant,
        prop,
        [tenant],
        criteria={**criteria_for(prop, 1), "rental_scope": "room"},
    )
    plan, response, _ = response_for(owner, tenant, prop, plan, offer_id)
    old = deepcopy(HousingOffer.objects.get(id=response["id"]).student_policy_snapshot)
    assert (
        old["id"] == policy["id"] and old["conditional_cancellation_guarantee"] is False
    )
    post(
        owner,
        f"properties/{prop.id}/student-policies/",
        {**body, **command(policy["revision"]), "eligibility": "current_enrollment"},
    )
    offered = HousingOffer.objects.get(id=response["id"])
    assert offered.student_policy_snapshot == old
    data = (
        authenticated(tenant)
        .get(API + f"housing-requests/{offered.request.id}/offers/")
        .data["results"][0]
    )
    assert data["status"] == "review_required" and data["allowed_actions"] == []
    post(
        tenant,
        "rental-interests/",
        command(
            property_id=str(prop.id),
            offer_id=offer_id,
            offer_revision=2,
            desired_start=plan["starts_on"],
            months=1,
            occupants=1,
            academic_plan_id=plan["id"],
            academic_revision=plan["requirements_revision"],
            source_housing_offer_id=response["id"],
            source_housing_offer_revision=response["revision"],
        ),
        409,
    )


@pytest.mark.django_db
def test_started_plan_can_revise_requirements_without_rewriting_published_dates(
    rental_participants, monkeypatch
):
    _, tenant, _, prop, _ = rental_participants
    plan = publish(
        tenant, review(tenant, requirements(tenant, create_plan(tenant, prop)))
    )
    demand = HousingRequest.objects.get(academic_plan__id=plan["id"])
    snapshot = deepcopy(demand.academic_snapshot)
    from datetime import date

    monkeypatch.setattr(
        timezone,
        "localdate",
        lambda *args, **kwargs: date.fromisoformat(plan["starts_on"])
        + timedelta(days=10),
    )
    body = plan_body(
        tenant,
        prop,
        starts_on=plan["starts_on"],
        ends_on_exclusive=plan["ends_on_exclusive"],
        label="Revised study needs",
    )
    body["expected_revision"] = plan["revision"]
    changed = post(tenant, f"academic-plans/{plan['id']}/edit/", body).data["resource"]
    assert (
        changed["starts_on"] == plan["starts_on"]
        and "waiting_for_consent" in changed["blocking_reasons"]
    )
    demand.refresh_from_db()
    assert demand.academic_snapshot == snapshot


@pytest.mark.django_db
def test_history_exposes_only_own_private_requirements(rental_participants, group):
    _, tenant, member, prop, _ = rental_participants
    plan = create_plan(tenant, prop, group=group, people=[tenant, member])
    plan = post(
        member,
        f"academic-plans/{plan['id']}/requirements/",
        command(
            plan["revision"],
            requirements={"internship_destination": "PRIVATE_PLACEMENT"},
            budget_min={"amount_minor": 10},
            budget_max={"amount_minor": 20},
            owner_disclosures=[],
        ),
    ).data["resource"]
    assert "PRIVATE_PLACEMENT" not in str(read(tenant, plan["id"]))
    own = authenticated(member).get(API + f"academic-plans/{plan['id']}/history/").data
    other = (
        authenticated(tenant).get(API + f"academic-plans/{plan['id']}/history/").data
    )
    assert "PRIVATE_PLACEMENT" in str(own) and "PRIVATE_PLACEMENT" not in str(other)


@pytest.mark.django_db
def test_study_fact_cannot_be_self_certified_and_expiry_is_visible(
    rental_participants, settings
):
    owner, tenant, _, prop, offer_id = rental_participants
    body = command(
        offer_id=offer_id,
        code="study_desk",
        value="A desk is included",
        classification="verified",
    )
    post(owner, f"properties/{prop.id}/decision-facts/", body, 404)
    fact = post(
        owner,
        f"properties/{prop.id}/decision-facts/",
        {**body, "classification": "owner_reported"},
    ).data["resource"]
    data = (
        authenticated(tenant)
        .get(
            API + f"properties/{prop.id}/decision-summary/",
            {"offer_id": offer_id, "offer_revision": 2},
        )
        .data
    )
    desk = next(row for row in data["facts"] if row["code"] == "study_desk")
    assert desk["classification"] == "owner_reported" and desk["checked_at"]
    assert "study_ready_badge" not in data
    settings.STUDENT_ENABLED_SERVICES = []
    data = (
        authenticated(tenant)
        .get(
            API + f"properties/{prop.id}/decision-summary/",
            {"offer_id": offer_id, "offer_revision": 2},
        )
        .data
    )
    assert not any(row["code"] == "study_desk" for row in data["facts"])


@pytest.mark.django_db
def test_journey_e_internship_plan_and_departure_request_do_not_release_current_tenancy(
    current_lease,
):
    owner, tenant, _, lease = current_lease
    original = (lease.status, lease.occupancy_status, deepcopy(lease.terms))
    old = create_plan(tenant, lease.property, current_lease_id=str(lease.id))
    new = reviewed_plan(
        tenant,
        lease.property,
        [tenant],
        current_lease_id=str(lease.id),
        previous_plan_id=old["id"],
        period_kind="internship",
        label="Synthetic placement housing",
    )
    notice = post(
        tenant,
        f"leases/{lease.id}/move-out-notices/",
        transition_body(lease, "moveOutNotice", "submit"),
        201,
    ).data["resource"]
    acknowledged = post(
        owner,
        f"move-out-notices/{notice['id']}/acknowledge/",
        transition_body(lease, "moveOutNotice", "acknowledge", notice["revision"]),
    ).data["resource"]
    lease.refresh_from_db()
    assert (lease.status, lease.occupancy_status, lease.terms) == original
    assert acknowledged["status"] != "effective"
    assert new["current_lease_id"] == str(lease.id)
    assert not Lease.objects.exclude(pk=lease.pk).exists()
    artifact("transition-plan", new)
    artifact("transition-notice", acknowledged)


@pytest.mark.django_db
def test_family_grant_expiry_and_unselected_invoice_remain_private(current_lease):
    owner, tenant, recipient, lease = current_lease
    body = command(
        recipient_email=recipient.email,
        scopes=["booking"],
        expires_at=(timezone.now() + timedelta(days=2)).isoformat(),
        consent=True,
    )
    result = post(tenant, f"leases/{lease.id}/summary-grants/", body, 201).data[
        "resource"
    ]
    assert "invoice" not in result and "receipt" not in result
    post(owner, f"leases/{lease.id}/summary-grants/", body, 404)
    RentalSummaryGrant.objects.filter(id=result["id"]).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    assert (
        authenticated(recipient).get(API + "shared-rental-summaries/").data["results"]
        == []
    )
    assert (
        authenticated(recipient)
        .get(API + f"leases/{lease.id}/summary-sharing-options/")
        .status_code
        == 404
    )
    from core_apps.features.models import RentInvoice

    other_invoice = RentInvoice.objects.create(
        lease=lease,
        payer=owner,
        reference="SYNTHETIC-OTHER-PAYER",
        due_date=timezone.localdate(),
        amount_minor=100,
    )
    options = (
        authenticated(tenant)
        .get(API + f"leases/{lease.id}/summary-sharing-options/")
        .data
    )
    assert str(other_invoice.id) not in {row["id"] for row in options["invoices"]}
    post(
        tenant,
        f"leases/{lease.id}/summary-grants/",
        {
            **body,
            **command(),
            "scopes": ["invoice"],
            "invoice_id": str(other_invoice.id),
        },
        404,
    )
