import json
import os
import uuid
from datetime import timedelta
from pathlib import Path

import pytest
from django.test import override_settings
from django.utils import timezone

from core_apps.features.models import Lease, RentalInterest
from core_apps.features.planning_models import (
    GroupInvitation,
    HousingGroup,
    LifestyleProfile,
    RoommateConnection,
)
from core_apps.features.services.tenancy_invitations import resolve_offer_snapshot
from core_apps.properties.models import PropertyVisit
from .test_funded_settlement import command
from .test_rental_phase2 import authenticated, rental_participants

API = "/api/v1/features/v1/"


@pytest.fixture(autouse=True)
def configured_planning_offer(rental_participants):
    prop = rental_participants[3]
    for offer in prop.rental_inventory["offers"]:
        offer["terms"].update(
            rental_period=1,
            suitable_for="all",
            description="Configured shared accommodation",
            smoking_allowed=False,
            rules=[],
        )
    prop.save(update_fields=["rental_inventory"])


def post(user, path, body, status=200):
    response = authenticated(user).post(API + path, body, format="json")
    assert response.status_code == status, response.data
    return response


def criteria_for(prop, people=2):
    return {
        "city_id": str(prop.city.id),
        "district_ids": [],
        "rental_scope": "entire_property",
        "property_type": prop.property_type.slug,
        "budget_min": {"amount_minor": 100_000, "currency": "EGP", "exponent": 2},
        "budget_max": {"amount_minor": 2_000_000, "currency": "EGP", "exponent": 2},
        "price_period": "monthly",
        "start_on": str(timezone.localdate() + timedelta(days=10)),
        "end_on": None,
        "people": people,
        "amenities": [],
        "furnished": None,
    }


def planning_grant(user, capability, action, subject=""):
    response = authenticated(user).get(
        API + "planning-capabilities/",
        {"capability": capability, "action": action, "subject_id": subject},
    )
    assert (
        response.status_code == 200 and action in response.data["allowed_actions"]
    ), response.data
    return response.json()["data"]


def group_action(user, group, action, **values):
    return post(
        user,
        f"housing-groups/{group['id']}/{action}/",
        command(
            group["revision"],
            roster_revision=group["roster_revision"],
            action=action,
            consent=False,
            **values,
        ),
    ).data["resource"]


def create_group(tenant, prop):
    return post(
        tenant,
        "housing-groups/",
        command(
            action="create",
            roster_revision=0,
            name="Campus group",
            visibility="invite_only",
            capacity=2,
            criteria=criteria_for(prop),
            consent=False,
        ),
        201,
    ).data["resource"]


def join_group(tenant, member, group):
    invite_response = post(
        tenant,
        f"housing-groups/{group['id']}/invitations/",
        command(group_id=group["id"], group_revision=group["revision"]),
        201,
    )
    invite = invite_response.data["resource"]
    token = invite["link"].split("#")[1]
    preview = post(member, "group-invitations/preview/", {"token": token})
    assert "members" not in preview.data and preview.data["link"] == ""
    body = command(
        group["revision"],
        group_id=group["id"],
        group_revision=group["revision"],
        token=token,
    )
    joined = post(member, "group-invitations/join/", body)
    assert post(member, "group-invitations/join/", body).data == joined.data
    return joined.data["resource"], invite_response, preview


@pytest.mark.django_db
def test_lifestyle_disclosure_connections_and_revocation(rental_participants):
    owner, tenant, member, _, _ = rental_participants
    initial = authenticated(tenant).get(API + "lifestyle-profile/")
    assert initial.data["discoverable"] is False and initial.data["revision"] == 0
    saved = post(
        member,
        "lifestyle-profile/",
        command(
            discoverable=True,
            habits={"sleep": "early", "smoking": "no", "guests": "sometimes"},
            preferences={"quiet": "high"},
            disclosed=["sleep"],
        ),
    )
    candidates = authenticated(tenant).get(API + "roommate-candidates/").data["results"]
    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate["disclosures"] == ["sleep: early"]
    assert "smoking" not in json.dumps(candidate) and "email" not in candidate
    assert candidate["chat_granted"] is False
    body = command(
        decision="request",
        candidate_revision=candidate["revision"],
        note="Roommate invitation",
    )
    created = post(tenant, f"roommate-candidates/{candidate['id']}/request/", body, 201)
    connection = created.data["resource"]
    assert connection["id"] != candidate["id"] and connection["status"] == "pending"
    assert (
        post(tenant, f"roommate-candidates/{candidate['id']}/request/", body, 201).data
        == created.data
    )
    post(
        tenant,
        f"roommate-connections/{connection['id']}/accept/",
        command(1, decision="accept"),
        403,
    )
    post(
        owner,
        f"roommate-connections/{connection['id']}/accept/",
        command(1, decision="accept"),
        404,
    )
    accepted = post(
        member,
        f"roommate-connections/{connection['id']}/accept/",
        command(1, decision="accept"),
    )
    assert accepted.data["resource"]["chat_granted"] is True
    post(
        tenant,
        f"roommate-connections/{connection['id']}/block/",
        command(2, decision="block"),
    )
    assert (
        authenticated(member)
        .get(API + "roommate-connections/")
        .data["results"][0]["chat_granted"]
        is False
    )
    assert authenticated(tenant).get(API + "roommate-candidates/").data["results"] == []
    post(
        member,
        "lifestyle-profile/",
        command(
            1,
            discoverable=False,
            habits={"sleep": "early"},
            preferences={},
            disclosed=[],
        ),
    )
    assert authenticated(owner).get(API + "roommate-candidates/").data["results"] == []
    assert (
        LifestyleProfile.objects.count() == 1
        and RoommateConnection.objects.count() == 1
    )


@pytest.mark.django_db
def test_group_invitation_cost_consent_visit_application_and_roster_change(
    rental_participants,
):
    owner, tenant, member, prop, offer_id = rental_participants
    group = create_group(tenant, prop)
    group, invite, preview = join_group(tenant, member, group)
    assert group["roster_revision"] == 2
    assert (
        authenticated(owner).get(API + f"housing-groups/{group['id']}/").status_code
        == 404
    )
    grant = authenticated(member).get(
        API + "planning-capabilities/",
        {
            "capability": "housing_groups",
            "action": "archive",
            "subject_id": group["id"],
        },
    )
    assert grant.data["allowed_actions"] == []
    _, snapshot = resolve_offer_snapshot(prop, offer_id, 2)
    snapshot["bed_id"] = snapshot["bed_name"] = ""
    group = group_action(tenant, group, "add_shortlist", selection=snapshot)
    proposal = {
        "id": "",
        "revision": 0,
        "roster_revision": group["roster_revision"],
        "offer_id": offer_id,
        "offer_revision": 2,
        "start_on": criteria_for(prop)["start_on"],
        "end_on": "",
        "period": "monthly",
        "total": {"amount_minor": 1_000_000, "currency": "EGP", "exponent": 2},
        "contributions": {str(tenant.id): 600_000, str(member.id): 400_000},
    }
    group = group_action(tenant, group, "propose_costs", proposal=proposal)
    for actor in (tenant, member):
        p = group["proposals"][0]
        group = post(
            actor,
            f"housing-groups/{group['id']}/approve_costs/",
            command(
                group["revision"],
                action="approve_costs",
                roster_revision=group["roster_revision"],
                item_id=p["id"],
                item_revision=p["revision"],
                consent=True,
            ),
        ).data["resource"]
    assert set(group["proposals"][0]["approved_by"]) == {str(tenant.id), str(member.id)}
    appointment = timezone.now() + timedelta(days=1)
    body = command(
        group["revision"],
        action="request_visit",
        roster_revision=group["roster_revision"],
        selection=snapshot,
        participant_ids=[str(tenant.id), str(member.id)],
        consent=True,
        appointment_at=appointment.isoformat(),
    )
    group = post(tenant, f"housing-groups/{group['id']}/request_visit/", body).data[
        "resource"
    ]
    assert PropertyVisit.objects.count() == 0  # Leader cannot consent for a member.
    process = group["visits"][0]
    group = post(
        member,
        f"housing-groups/{group['id']}/consent_visit/",
        command(
            group["revision"],
            action="consent_visit",
            roster_revision=group["roster_revision"],
            item_id=process["id"],
            item_revision=process["revision"],
            consent=True,
        ),
    ).data["resource"]
    assert PropertyVisit.objects.count() == 1
    assert group["visits"][0]["qualifying_visit_id"] == str(
        PropertyVisit.objects.get().id
    )
    application = command(
        group["revision"],
        action="apply",
        roster_revision=group["roster_revision"],
        selection=snapshot,
        participant_ids=[str(tenant.id), str(member.id)],
        consent=True,
    )
    group = post(tenant, f"housing-groups/{group['id']}/apply/", application).data[
        "resource"
    ]
    process = group["applications"][0]
    assert not RentalInterest.objects.exists()
    group = post(
        member,
        f"housing-groups/{group['id']}/consent_application/",
        command(
            group["revision"],
            action="consent_application",
            roster_revision=group["roster_revision"],
            item_id=process["id"],
            item_revision=process["revision"],
            consent=True,
        ),
    ).data["resource"]
    assert RentalInterest.objects.count() == 1
    interest = RentalInterest.objects.get()
    assert (
        interest.tenant == tenant
        and interest.occupants == 2
        and interest.offer_id == offer_id
    )
    assert Lease.objects.count() == 0
    # A real owner-facing interest exists; acceptance/signing is still separate.
    owner_interest = authenticated(owner).get(API + f"rental-interests/{interest.id}/")
    assert owner_interest.status_code == 200
    accepted_group = group
    departure = group_action(member, group, "leave")
    assert departure["members"] == [] and departure["allowed_actions"] == []
    group = authenticated(tenant).get(API + f"housing-groups/{group['id']}/").data
    assert group["roster_revision"] == 3
    assert group["proposals"][0]["approved_by"] == []
    assert group["applications"][0]["status"] == "withdrawn"
    assert PropertyVisit.objects.get().status == "canceled"
    interest.refresh_from_db()
    assert interest.status == "withdrawn"
    assert (
        authenticated(member).get(API + f"housing-groups/{group['id']}/").status_code
        == 404
    )
    directory = os.environ.get("SOKOUN_PLANNING_ARTIFACT_DIR")
    if directory:
        target = Path(directory)
        target.mkdir(parents=True, exist_ok=True)
        (target / "django-group-contract.json").write_text(
            json.dumps(
                {
                    "owner_id": str(owner.id),
                    "tenant_id": str(tenant.id),
                    "member_id": str(member.id),
                    "group": accepted_group,
                    "invitation": invite.json(),
                    "preview": preview.json(),
                    "selection": snapshot,
                    "proposal_body": proposal,
                    "invite_grant": planning_grant(
                        tenant, "housing_groups", "create_invite"
                    ),
                    "invite_body": {
                        "request_key": invite.data["operation_receipt"]["request_key"],
                        "group_id": invite.data["resource"]["group_id"],
                        "group_revision": invite.data["resource"]["group_revision"],
                    },
                },
                indent=2,
            )
        )


@pytest.mark.django_db
def test_group_capacity_expiry_wrong_token_stale_roster_and_independent_gates(
    rental_participants,
):
    owner, tenant, member, prop, _ = rental_participants
    group = create_group(tenant, prop)
    group, invite, _ = join_group(tenant, member, group)
    token = invite.data["resource"]["link"].split("#")[1]
    post(owner, "group-invitations/preview/", {"token": "x" * 64}, 404)
    post(
        owner,
        "group-invitations/join/",
        command(
            group["revision"],
            token=token,
            group_id=group["id"],
            group_revision=group["revision"],
        ),
        409,
    )
    post(
        tenant,
        f"housing-groups/{group['id']}/archive/",
        command(group["revision"], action="archive", roster_revision=1),
        409,
    )
    assert HousingGroup.objects.get(id=group["id"]).status == "active"
    with override_settings(PLANNING_ENABLED_SERVICES=["housing_groups"]):
        response = authenticated(tenant).get(
            API + "planning-capabilities/",
            {
                "capability": "group_visits",
                "action": "request_visit",
                "subject_id": group["id"],
            },
        )
        assert response.data["allowed_actions"] == []
    GroupInvitation.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
    post(owner, "group-invitations/preview/", {"token": token}, 409)


@pytest.mark.django_db
def test_housing_request_offer_identity_permissions_expiry_and_recovery(
    rental_participants,
):
    owner, tenant, stranger, prop, offer_id = rental_participants
    body = command(
        action="publish",
        title="Campus home",
        note="Two residents",
        criteria=criteria_for(prop),
        visibility="eligible_owners",
    )
    created = post(tenant, "housing-requests/", body, 201)
    item = created.data["resource"]
    assert item["criteria"]["city"]["id"] == str(prop.city.id)
    assert item["criteria"]["filters"]["price_min"] == "1000"
    assert post(tenant, "housing-requests/", body, 201).data == created.data
    recovered = authenticated(tenant).get(
        API + f"rental-operations/{body['request_key']}/",
        {"subject_id": str(tenant.id)},
    )
    assert recovered.status_code == 200 and recovered.data["status"] == "confirmed"
    assert authenticated(stranger).get(API + "housing-demand/").status_code == 403
    assert (
        authenticated(stranger).get(API + f"housing-requests/{item['id']}/").status_code
        == 404
    )
    assert (
        authenticated(owner).get(API + "housing-demand/").data["results"][0]["id"]
        == item["id"]
    )
    _, snapshot = resolve_offer_snapshot(prop, offer_id, 2)
    snapshot["bed_id"] = snapshot["bed_name"] = ""
    offer_body = command(
        request_id=item["id"],
        request_revision=item["revision"],
        selection=snapshot,
        note="Owned available home",
    )
    post(stranger, f"housing-requests/{item['id']}/offers/", offer_body, 404)
    forged = {
        **offer_body,
        "selection": {**snapshot, "terms": {"price": "1", "price_period": "monthly"}},
    }
    post(owner, f"housing-requests/{item['id']}/offers/", forged, 409)
    offer_response = post(
        owner, f"housing-requests/{item['id']}/offers/", offer_body, 201
    )
    offer = offer_response.data["resource"]
    assert offer["rent"]["amount_minor"] == 1_000_000
    assert offer["allowed_actions"] == ["withdraw"]
    tenant_offer = (
        authenticated(tenant)
        .get(API + f"housing-requests/{item['id']}/offers/")
        .data["results"][0]
    )
    assert tenant_offer["allowed_actions"] == ["shortlist", "decline"]
    shortlisted = post(
        tenant,
        f"housing-offers/{offer['id']}/shortlist/",
        command(1, decision="shortlist"),
    )
    assert shortlisted.data["resource"]["status"] == "shortlisted"
    assert Lease.objects.count() == 0
    # Continue into the actual interest workflow with independent validation.
    interest = post(
        tenant,
        "rental-interests/",
        command(
            property_id=str(prop.id),
            offer_id=offer_id,
            offer_revision=2,
            desired_start=criteria_for(prop)["start_on"],
            months=2,
            occupants=2,
            message="Selected owner response",
        ),
        201,
    )
    assert interest.data["resource"]["offer_id"] == offer_id
    edited_body = {
        **body,
        **command(item["revision"]),
        "action": "edit",
        "title": "Updated request",
    }
    post(tenant, f"housing-requests/{item['id']}/edit/", edited_body)
    stale = (
        authenticated(tenant)
        .get(API + f"housing-requests/{item['id']}/offers/")
        .data["results"][0]
    )
    assert stale["status"] == "expired" and stale["allowed_actions"] == []
    directory = os.environ.get("SOKOUN_PLANNING_ARTIFACT_DIR")
    if directory:
        target = Path(directory)
        target.mkdir(parents=True, exist_ok=True)
        (target / "django-housing-contract.json").write_text(
            json.dumps(
                {
                    "owner_id": str(owner.id),
                    "tenant_id": str(tenant.id),
                    "request_body": body,
                    "request": created.json(),
                    "offer_body": offer_body,
                    "offer": offer_response.json(),
                    "tenant_offer": tenant_offer,
                    "shortlisted": shortlisted.json(),
                    "request_grant": planning_grant(
                        tenant, "housing_requests", "publish"
                    ),
                    "offer_grant": planning_grant(owner, "housing_offers", "offer"),
                },
                indent=2,
            )
        )
