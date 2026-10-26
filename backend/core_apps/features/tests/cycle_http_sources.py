"""Owner-facing planning sources exercised through authenticated HTTP actors."""

from core_apps.features.models import Lease, RentalInterest
from core_apps.features.services.planning import selection_payload
from core_apps.features.services.tenancy_invitations import resolve_offer_snapshot
from .test_funded_settlement import command
from .test_planning_cycles import criteria_for

API = "/api/v1/features/v1/"
PROPERTIES = "/api/v1/properties/"


def mutate(actor, path, body, status=200):
    response = actor.post(API + path, body)
    assert response.status_code == status, response.data
    return response.data["resource"]


def marketplace_entry(actors, participants):
    owner, tenant, _, prop, offer_id = participants
    owner_api, tenant_api = actors[owner.pk], actors[tenant.pk]
    found = tenant_api.get(PROPERTIES, {"search": prop.title})
    assert found.status_code == 200, found.data
    detail = tenant_api.get(PROPERTIES + f"{prop.id}/")
    assert detail.status_code == 200, detail.data
    saved = tenant_api.post(PROPERTIES + f"{prop.id}/save/", {})
    assert saved.status_code in (200, 201), saved.data
    listed = tenant_api.get(PROPERTIES + "saved/")
    assert listed.status_code == 200, listed.data
    visit = tenant_api.post(
        PROPERTIES + f"{prop.id}/visits/",
        {
            "note": "HTTP cycle",
            "offer_id": offer_id,
            "expected_offer_revision": 2,
        },
    )
    assert visit.status_code == 201, visit.data
    accepted = owner_api.post(
        PROPERTIES + f"owner/visits/requests/{visit.data['id']}/accept/",
        command(visit.data["revision"]),
    )
    assert accepted.status_code == 200, accepted.data
    tenant_read = tenant_api.get(PROPERTIES + f"visits/{visit.data['id']}/")
    assert tenant_read.status_code == 200 and tenant_read.data["status"] == "confirmed"
    assert not Lease.objects.exists() and not RentalInterest.objects.exists()


def housing_request_entry(actors, participants):
    owner, tenant, _, prop, offer_id = participants
    owner_api, tenant_api = actors[owner.pk], actors[tenant.pk]
    criteria = criteria_for(prop)
    request = mutate(
        tenant_api,
        "housing-requests/",
        command(
            action="publish",
            title="HTTP cycle home",
            note="Two residents",
            criteria=criteria,
            visibility="eligible_owners",
        ),
        201,
    )
    _, snapshot = resolve_offer_snapshot(prop, offer_id, 2)
    offer = mutate(
        owner_api,
        f"housing-requests/{request['id']}/offers/",
        command(
            request_id=request["id"],
            request_revision=request["revision"],
            selection=selection_payload(snapshot),
            note="Owned available home",
        ),
        201,
    )
    current = tenant_api.get(API + f"housing-offers/{offer['id']}/")
    assert current.status_code == 200, current.data
    assert current.data["selection"]["offer_id"] == offer_id
    assert not Lease.objects.exists() and not RentalInterest.objects.exists()
    interest = mutate(
        tenant_api,
        "rental-interests/",
        command(
            property_id=str(prop.id),
            offer_id=offer_id,
            offer_revision=2,
            desired_start=criteria["start_on"],
            months=1,
            occupants=2,
            message="Continue the reviewed housing offer",
        ),
        201,
    )
    assert interest["offer_id"] == offer_id
    return interest


def group_entry(actors, participants):
    owner, tenant, member, prop, offer_id = participants
    tenant_api, member_api, owner_api = (
        actors[tenant.pk],
        actors[member.pk],
        actors[owner.pk],
    )
    group = mutate(
        tenant_api,
        "housing-groups/",
        command(
            action="create",
            roster_revision=0,
            name="Connected HTTP group",
            visibility="invite_only",
            capacity=2,
            criteria=criteria_for(prop),
            consent=False,
        ),
        201,
    )
    invitation = mutate(
        tenant_api,
        f"housing-groups/{group['id']}/invitations/",
        command(
            group_id=group["id"],
            group_revision=group["revision"],
        ),
        201,
    )
    group = mutate(
        member_api,
        "group-invitations/join/",
        command(
            group["revision"],
            group_id=group["id"],
            group_revision=group["revision"],
            token=invitation["link"].split("#")[1],
        ),
    )
    _, snapshot = resolve_offer_snapshot(prop, offer_id, 2)
    selection = selection_payload(snapshot)
    for action, extra in (
        ("add_shortlist", {"selection": selection}),
        (
            "propose_costs",
            {
                "proposal": {
                    "id": "",
                    "revision": 0,
                    "roster_revision": group["roster_revision"],
                    "offer_id": offer_id,
                    "offer_revision": 2,
                    "start_on": criteria_for(prop)["start_on"],
                    "end_on": "",
                    "period": "monthly",
                    "total": {
                        "amount_minor": 1_000_000,
                        "currency": "EGP",
                        "exponent": 2,
                    },
                    "contributions": {str(tenant.id): 600_000, str(member.id): 400_000},
                }
            },
        ),
    ):
        group = mutate(
            tenant_api,
            f"housing-groups/{group['id']}/{action}/",
            command(
                group["revision"],
                action=action,
                roster_revision=group["roster_revision"],
                consent=False,
                **extra,
            ),
        )
    for actor in (tenant_api, member_api):
        proposal = group["proposals"][0]
        group = mutate(
            actor,
            f"housing-groups/{group['id']}/approve_costs/",
            command(
                group["revision"],
                action="approve_costs",
                roster_revision=group["roster_revision"],
                item_id=proposal["id"],
                item_revision=proposal["revision"],
                consent=True,
            ),
        )
    group = mutate(
        tenant_api,
        f"housing-groups/{group['id']}/apply/",
        command(
            group["revision"],
            action="apply",
            roster_revision=group["roster_revision"],
            selection=selection,
            participant_ids=[str(tenant.id), str(member.id)],
            consent=True,
        ),
    )
    assert not RentalInterest.objects.exists()  # Leader cannot consent for a member.
    application = group["applications"][0]
    group = mutate(
        member_api,
        f"housing-groups/{group['id']}/consent_application/",
        command(
            group["revision"],
            action="consent_application",
            roster_revision=group["roster_revision"],
            item_id=application["id"],
            item_revision=application["revision"],
            consent=True,
        ),
    )
    # Group consensus is an owner-reviewed application, not permission for the
    # leader to create an individual tenancy on everybody's behalf.
    reviewed = owner_api.get(API + f"group-applications/{application['id']}/")
    assert reviewed.status_code == 200 and reviewed.data["status"] == "under_review"
    approved = mutate(
        owner_api,
        f"group-applications/{application['id']}/approve/",
        command(reviewed.data["revision"], note="Suitable group application"),
    )
    assert approved["status"] == "approved_to_proceed"
    assert not RentalInterest.objects.exists()
    created = mutate(
        tenant_api,
        "rental-interests/",
        command(
            property_id=str(prop.id),
            offer_id=offer_id,
            offer_revision=2,
            desired_start=criteria_for(prop)["start_on"],
            months=1,
            occupants=2,
            message="Explicit individual application after owner group review",
        ),
        201,
    )
    interest = RentalInterest.objects.get(id=created["id"])
    assert (
        interest.tenant_id == tenant.pk
        and interest.offer_id == offer_id
        and interest.occupants == 2
    )
    assert not Lease.objects.exists()
    response = owner_api.get(API + f"rental-interests/{interest.id}/")
    assert response.status_code == 200, response.data
    return response.data
