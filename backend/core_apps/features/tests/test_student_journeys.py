"""Synthetic HTTP journeys using PostgreSQL and the explicit test provider.

No university partnership, production signature, receipt, or occupancy is asserted.
"""

import copy
import json
import os
import uuid
from datetime import date, timedelta
from pathlib import Path

import pytest
from django.utils import timezone
from core_apps.features.models import (
    AcademicPlanParticipant,
    GroupBookingParticipant,
    GroupInvitation,
    GroupMembership,
    HousingGroup,
    HousingRequest,
    Lease,
    PaymentAttempt,
    RentalInterest,
    RentalOperationalCase,
    RentInvoice,
    SigningSession,
    PaymentReceipt,
)
from core_apps.features.services.tenancy_invitations import resolve_offer_snapshot
from core_apps.users.models import User
from .test_student_housing import (
    API,
    student_capabilities,
    post,
    create_plan,
    requirements,
    review,
    publish,
    read,
)
from .test_rental_phase2 import (
    rental_participants,
    authenticated,
    run_interest_to_activation,
    agreement_terms,
    complete_owner_onboarding,
)
from .test_rental_lifecycle import policy, command
from .test_planning_cycles import join_group, criteria_for
from .test_current_cycle_contract import sign, capture, create_checkout


def artifact(name, payload):
    if directory := os.environ.get("SOKOUN_STUDENT_ARTIFACT_DIR"):
        root = Path(directory)
        root.mkdir(parents=True, exist_ok=True)
        (root / f"{name}.json").write_text(
            json.dumps({"synthetic": True, "data": payload}, indent=2, default=str)
        )


def inventory(prop, people=1):
    rooms = [str(uuid.uuid4()) for _ in range(people)]
    ids = [str(uuid.uuid4()) for _ in range(people)]
    base = copy.deepcopy(prop.rental_inventory["offers"][0])
    base.update(
        capacity=people,
        rental_scope="room_group" if people > 1 else "room",
        room_ids=rooms,
    )
    base["terms"].update(rental_period=1, price=str(10000 * people), suitable_for="all")
    individual = [
        dict(
            base,
            id=offer,
            name=f"Synthetic room {i+1}",
            capacity=1,
            rental_scope="room",
            room_ids=[room],
            terms={**base["terms"], "price": "10000"},
        )
        for i, (room, offer) in enumerate(zip(rooms, ids))
    ]
    prop.rental_inventory = {
        "schema_version": 1,
        "revision": 1,
        "mode": "partial",
        "rooms": [
            {"id": room, "name": f"Synthetic room {i+1}", "beds": []}
            for i, room in enumerate(rooms)
        ],
        "offers": [base, *individual] if people > 1 else [base],
    }
    prop.save(update_fields=["rental_inventory"])
    return base["id"], ids if people > 1 else [base["id"]]


def reviewed_plan(tenant, prop, members, group=None, **values):
    start = (
        date.fromisoformat(values["starts_on"])
        if values.get("starts_on")
        else timezone.localdate() + timedelta(days=10)
    )
    values.setdefault("ends_on_exclusive", str(start + timedelta(days=31)))
    plan = create_plan(
        tenant,
        prop,
        group=group,
        people=members,
        **values,
    )
    for member in members:
        plan = requirements(member, plan, study_space="Individual desk requested")
    for member in members:
        plan = review(member, plan)
    return plan


def response_for(owner, tenant, prop, plan, offer_id):
    original_resources = (Lease.objects.count(), PaymentAttempt.objects.count())
    plan = publish(tenant, plan)
    demand = HousingRequest.objects.get(academic_plan__id=plan["id"])
    _, selection = resolve_offer_snapshot(prop, offer_id, 2)
    selection["bed_id"] = selection["bed_name"] = ""
    response = post(
        owner,
        f"housing-requests/{demand.id}/offers/",
        command(
            request_id=str(demand.id),
            request_revision=demand.revision,
            selection=selection,
            note="Synthetic available accommodation; study facilities unverified",
        ),
        201,
    ).data["resource"]
    response = post(
        tenant,
        f"housing-offers/{response['id']}/select_to_proceed/",
        command(response["revision"], decision="select_to_proceed"),
    ).data["resource"]
    assert (Lease.objects.count(), PaymentAttempt.objects.count()) == original_resources
    return plan, response, selection


@pytest.mark.django_db
def test_journey_a_solo_room_through_signing_payment_arrival_and_support(
    rental_participants,
):
    owner, tenant, _, prop, offer_id = rental_participants
    inventory(prop)
    criteria = {**criteria_for(prop, 1), "rental_scope": "room"}
    plan = reviewed_plan(tenant, prop, [tenant], criteria=criteria)
    plan, response, _ = response_for(owner, tenant, prop, plan, offer_id)
    body = command(
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
    )
    interest = post(tenant, "rental-interests/", body, 201).data["resource"]
    assert interest["desired_end"] == plan["ends_on_exclusive"]
    assert (
        post(tenant, "rental-interests/", body, 201).data["resource"]["id"]
        == interest["id"]
    )
    run_interest_to_activation(
        rental_participants,
        existing_interest=interest,
        artifact_name="synthetic-student-solo",
    )
    lease = Lease.objects.get(tenant=tenant)
    assert lease.status == "active"
    assert AcademicPlanParticipant.objects.get(plan__id=plan["id"]).lease_id == lease.pk
    plan = read(tenant, plan["id"])
    assert plan["participants"][0]["lease_id"] == str(lease.id)
    report = command(
        plan["revision"],
        lease_id=str(lease.id),
        kind="missing_facility",
        note="The agreed desk is missing",
    )
    result = post(tenant, f"academic-plans/{plan['id']}/check_in/", report)
    post(tenant, f"academic-plans/{plan['id']}/check_in/", report)
    assert (
        RentalOperationalCase.objects.filter(
            kind="move_in_mismatch", lease=lease
        ).count()
        == 1
    )
    artifact("solo-plan", result.data["resource"])
    artifact("solo-interest", interest)
    artifact("solo-response", response)
    # Selected summaries reuse real invoices and receipts without delegated payment.
    recipient = rental_participants[2]
    options = (
        authenticated(tenant)
        .get(API + f"leases/{lease.id}/summary-sharing-options/")
        .data
    )
    assert options["receipts"]
    grant_body = command(
        recipient_email=recipient.email,
        scopes=["booking", "invoice", "receipt"],
        invoice_id=options["invoices"][0]["id"],
        receipt_id=options["receipts"][0]["id"],
        expires_at=(timezone.now() + timedelta(days=2)).isoformat(),
        consent=True,
    )
    grant = post(tenant, f"leases/{lease.id}/summary-grants/", grant_body, 201).data[
        "resource"
    ]
    shared = (
        authenticated(recipient).get(API + "shared-rental-summaries/").data["results"]
    )
    assert shared[0]["id"] == grant["id"] and not shared[0]["payment_authorized"]
    assert set(shared[0]) == {
        "id",
        "revision",
        "scopes",
        "status",
        "expires_at",
        "student_name",
        "recipient_name",
        "allowed_actions",
        "blocking_reasons",
        "payment_authorized",
        "tenancy_authority",
        "booking",
        "invoice",
        "receipt",
    }
    assert authenticated(recipient).get(API + f"leases/{lease.id}/").status_code == 404
    assert (
        authenticated(recipient)
        .get(API + f"rent-invoices/{options['invoices'][0]['id']}/")
        .status_code
        == 404
    )
    post(
        recipient,
        f"rent-invoices/{options['invoices'][0]['id']}/quote/",
        command(1, decision="quote"),
        404,
    )
    artifact("family-summary", shared[0])
    post(
        tenant,
        f"rental-summary-grants/{grant['id']}/revoke/",
        command(grant["revision"]),
    )
    assert (
        authenticated(recipient).get(API + "shared-rental-summaries/").data["results"]
        == []
    )


def group_application(owner, tenant, prop, members):
    group = post(
        tenant,
        "housing-groups/",
        command(
            action="create",
            roster_revision=0,
            name="Synthetic academic group",
            visibility="invite_only",
            capacity=len(members),
            criteria=criteria_for(prop, len(members)),
            consent=False,
        ),
        201,
    ).data["resource"]
    for member in members[1:]:
        group, _, _ = join_group(tenant, member, group)
    identity = (
        group["id"],
        copy.deepcopy(group["chat"]),
        GroupMembership.objects.count(),
        GroupInvitation.objects.count(),
    )
    canonical = HousingGroup.objects.get(id=group["id"])
    base_id, individual_ids = inventory(prop, len(members))
    plan = reviewed_plan(tenant, prop, members, group=canonical)
    plan, response, selection = response_for(owner, tenant, prop, plan, base_id)
    group = authenticated(tenant).get(API + f"housing-groups/{group['id']}/").data
    assert len(group["shortlist"]) == 1
    assert group["shortlist"][0]["academic_plan_ids"] == [plan["id"]]
    context = dict(
        academic_plan_id=plan["id"], academic_revision=plan["requirements_revision"]
    )
    cost = dict(
        id="",
        revision=0,
        roster_revision=group["roster_revision"],
        offer_id=base_id,
        offer_revision=2,
        start_on=plan["starts_on"],
        end_on=plan["ends_on_exclusive"],
        period="monthly",
        total={"amount_minor": len(members) * 1000000, "currency": "EGP"},
        contributions={str(member.id): 1000000 for member in members},
    )
    group = post(
        tenant,
        f"housing-groups/{group['id']}/propose_costs/",
        command(
            group["revision"],
            roster_revision=group["roster_revision"],
            action="propose_costs",
            proposal=cost,
            consent=False,
            **context,
        ),
    ).data["resource"]
    for member in members:
        proposal = group["proposals"][0]
        group = post(
            member,
            f"housing-groups/{group['id']}/approve_costs/",
            command(
                group["revision"],
                roster_revision=group["roster_revision"],
                action="approve_costs",
                item_id=proposal["id"],
                item_revision=proposal["revision"],
                consent=True,
                **context,
            ),
        ).data["resource"]
    group = post(
        tenant,
        f"housing-groups/{group['id']}/apply/",
        command(
            group["revision"],
            roster_revision=group["roster_revision"],
            action="apply",
            selection=selection,
            participant_ids=[str(member.id) for member in members],
            consent=True,
            **context,
        ),
    ).data["resource"]
    for member in members[1:]:
        application = group["applications"][0]
        group = post(
            member,
            f"housing-groups/{group['id']}/consent_application/",
            command(
                group["revision"],
                roster_revision=group["roster_revision"],
                action="consent_application",
                item_id=application["id"],
                item_revision=application["revision"],
                consent=True,
                **context,
            ),
        ).data["resource"]
    application = group["applications"][0]
    application = post(
        owner,
        f"group-applications/{application['id']}/approve/",
        command(application["revision"], note="Synthetic review"),
    ).data["resource"]
    assert (
        group["id"],
        group["chat"]["conversation_id"],
        GroupMembership.objects.count(),
        GroupInvitation.objects.count(),
    ) == (identity[0], identity[1]["conversation_id"], identity[2], identity[3])
    assert not RentalInterest.objects.exists() and not Lease.objects.exists()
    return group, plan, application, individual_ids


def complete_independent_agreement(owner, tenant, invitation, terms, prop, offer_id):
    response = authenticated(tenant).post(
        API + f"tenancy-invitations/{invitation.id}/respond/",
        dict(
            decision="accepted",
            revision=invitation.revision,
            request_key=str(uuid.uuid4()),
        ),
        format="json",
    )
    assert response.status_code == 200, response.data
    invitation.refresh_from_db()
    lease = post(
        owner,
        "leases/",
        command(
            invitation_id=str(invitation.id),
            invitation_revision=invitation.revision,
            property_id=str(prop.id),
            offer_id=offer_id,
            offer_revision=2,
            tenant_id=str(tenant.id),
            terms=terms,
        ),
        201,
    ).data["resource"]
    for actor in [owner, tenant]:
        lease = post(
            actor,
            f"leases/{lease['id']}/review/",
            command(lease["revision"], decision="accept_review"),
        ).data["resource"]
    lease = post(
        owner,
        f"leases/{lease['id']}/submit-for-signature/",
        command(lease["revision"], decision="submit_for_signature"),
    ).data["resource"]
    for actor in [owner, tenant]:
        result = post(
            actor,
            f"leases/{lease['id']}/signing-session/",
            command(
                lease["revision"],
                document_id=lease["document_id"],
                document_hash=lease["document_hash"],
            ),
            201,
        )
        assert (
            sign(SigningSession.objects.get(id=result.data["session_id"])).status_code
            == 200
        )
    signed = Lease.objects.get(id=lease["id"])
    for invoice in RentInvoice.objects.filter(
        lease=signed, status__in=["due", "pending", "unpaid"]
    ):
        attempt = create_checkout(tenant, invoice)
        assert capture(attempt).status_code == 200
    signed.refresh_from_db()
    assert signed.status == "active"
    return signed


@pytest.mark.django_db
def test_journeys_b_d_f_canonical_group_three_completed_one_declined_next_year(
    rental_participants, policy
):
    owner, tenant, other, prop, _ = rental_participants
    members = [
        tenant,
        other,
        *[
            User.objects.create_user(
                email=f"synthetic-student-{i}@example.test",
                password="pass",
                is_verified=True,
            )
            for i in range(2)
        ],
    ]
    group, plan, application, offers = group_application(owner, tenant, prop, members)
    complete_owner_onboarding(owner)
    terms = agreement_terms(
        date.fromisoformat(plan["starts_on"]),
        date.fromisoformat(plan["ends_on_exclusive"]),
    )
    body = command(
        application_id=application["id"],
        application_revision=application["revision"],
        roster_revision=group["roster_revision"],
        booking_model="independent",
        deadline=(timezone.now() + timedelta(days=1)).isoformat(),
        participants=[
            dict(
                tenant_id=str(member.id), offer_id=offer, offer_revision=2, terms=terms
            )
            for member, offer in zip(members, offers)
        ],
    )
    post(
        owner,
        "group-booking-proposals/",
        {**body, "booking_model": "conditional_bundle"},
        409,
    )
    proposal = post(owner, "group-booking-proposals/", body, 201).data["resource"]
    proposal = post(
        owner,
        f"group-booking-proposals/{proposal['id']}/submit/",
        command(proposal["revision"]),
    ).data["resource"]
    leases = []
    for member, offer in zip(members[:3], offers[:3]):
        proposal = post(
            member,
            f"group-booking-proposals/{proposal['id']}/consents/",
            command(
                proposal["revision"],
                decision="accept",
                terms_digest=proposal["terms_digest"],
            ),
        ).data["resource"]
        participant = GroupBookingParticipant.objects.get(
            proposal__id=proposal["id"], tenant=member
        )
        leases.append(
            complete_independent_agreement(
                owner, member, participant.invitation, terms, prop, offer
            )
        )
    prior_amounts = list(
        PaymentAttempt.objects.values_list("id", "amount_minor", "payment_status")
    )
    proposal = post(
        members[-1],
        f"group-booking-proposals/{proposal['id']}/consents/",
        command(
            proposal["revision"],
            decision="decline",
            terms_digest=proposal["terms_digest"],
        ),
    ).data["resource"]
    assert (
        proposal["status"] == "submitted" and proposal["booking_model"] == "independent"
    )
    assert proposal["total_rent_minor"] == 4000000
    assert all(Lease.objects.get(pk=lease.pk).status == "active" for lease in leases)
    assert not Lease.objects.filter(tenant=members[-1]).exists()
    assert (
        list(PaymentAttempt.objects.values_list("id", "amount_minor", "payment_status"))
        == prior_amounts
    )
    old_request = copy.deepcopy(
        HousingRequest.objects.get(academic_plan__id=plan["id"]).academic_snapshot
    )
    next_plan = create_plan(
        tenant,
        prop,
        group=HousingGroup.objects.get(id=group["id"]),
        people=members[:3],
        previous_plan_id=plan["id"],
        current_lease_id=str(leases[0].id),
        label="Synthetic next academic year",
    )
    assert next_plan["id"] != plan["id"] and next_plan["group_id"] == group["id"]
    assert (
        "waiting_for_consent" in next_plan["blocking_reasons"]
        or "missing_requirements" in next_plan["blocking_reasons"]
    )
    assert (
        HousingRequest.objects.get(academic_plan__id=plan["id"]).academic_snapshot
        == old_request
    )
    artifact("group", group)
    artifact("group-plan", read(tenant, plan["id"]))
    artifact("group-booking", proposal)
    artifact("next-year", next_plan)


@pytest.mark.django_db
def test_journey_c_existing_roommate_connections_then_canonical_group(
    rental_participants,
):
    owner, tenant, other, prop, _ = rental_participants
    for member in [tenant, other]:
        post(
            member,
            "lifestyle-profile/",
            command(
                discoverable=True,
                habits={"sleep": "early"},
                preferences={},
                disclosed=["sleep"],
            ),
        )
    post(
        other,
        "student-profile/",
        command(
            enrollment_status="admission_pending",
            preferences={
                "exam_quiet": "Please discuss guests",
                "accessibility": "Private requirement",
            },
            roommate_disclosures=["exam_quiet"],
        ),
    )
    candidate = next(
        row
        for row in authenticated(tenant)
        .get(API + "roommate-candidates/")
        .data["results"]
        if row["user_id"] == str(other.id)
    )
    assert "Private requirement" not in json.dumps(candidate)
    connection = post(
        tenant,
        f"roommate-candidates/{candidate['id']}/request/",
        command(
            decision="request",
            candidate_revision=candidate["revision"],
            note="Discuss shared housing",
        ),
        201,
    ).data["resource"]
    post(
        other,
        f"roommate-connections/{connection['id']}/accept/",
        command(connection["revision"], decision="accept"),
    )
    group, plan, _, _ = group_application(owner, tenant, prop, [tenant, other])
    assert plan["group_id"] == group["id"]
    assert GroupMembership.objects.count() == 2 and GroupInvitation.objects.count() == 1


@pytest.mark.django_db
def test_revoked_membership_hides_academic_requests_from_collection(
    rental_participants,
):
    owner, tenant, other, prop, _ = rental_participants
    group, plan, _, _ = group_application(owner, tenant, prop, [tenant, other])
    before = authenticated(other).get(API + "housing-requests/").data["results"]
    assert len(before) == 1
    post(
        other,
        f"housing-groups/{group['id']}/leave/",
        command(
            group["revision"],
            action="leave",
            roster_revision=group["roster_revision"],
            consent=False,
        ),
    )
    assert authenticated(other).get(API + "housing-requests/").data["results"] == []
    assert (
        authenticated(other).get(API + f"academic-plans/{plan['id']}/").status_code
        == 404
    )
