"""Replay bodies emitted by the Flutter DTOs against fresh authorized Django data.

Only account/resource identifiers and fixture revisions are rebound. Body shapes,
nullable defaults, terms, monetary units and enum vocabulary stay unchanged.
"""

import json
import os
from copy import deepcopy
from pathlib import Path

import pytest

from .test_current_cycle_contract import awaiting_signatures
from .test_funded_settlement import funded_exit
from core_apps.features.models import RentalInterest
from core_apps.features.services.planning import selection_payload
from core_apps.features.services.tenancy_invitations import resolve_offer_snapshot
from .test_funded_settlement import command
from .test_planning_boundaries import current_lease, transition_body
from .test_planning_cycles import (
    API,
    configured_planning_offer,
    create_group,
    group_action,
    join_group,
    post,
)
from .test_rental_phase2 import authenticated, rental_participants


@pytest.fixture
def flutter_bodies():
    filename = os.environ.get("SOKOUN_FLUTTER_REQUEST_BODIES")
    if not filename:
        pytest.skip(
            "Generate fresh Flutter request bodies with the documented Make targets"
        )
    result = json.loads(Path(filename).read_text())
    assert {
        "proposal",
        "invite",
        "housing_request",
        "housing_offer",
        "condition_create",
        "condition_acknowledge",
        "notice",
        "commute",
        "assistant",
        "refund",
        "replacement_consent",
    }.issubset(result)
    return result


@pytest.mark.django_db
def test_flutter_housing_request_and_authoritative_offer_bodies(
    flutter_bodies, rental_participants
):
    owner, tenant, _, prop, offer_id = rental_participants
    body = deepcopy(flutter_bodies["housing_request"])
    body["criteria"]["city_id"] = str(prop.city.id)
    created = post(tenant, "housing-requests/", body, 201).data["resource"]
    offer = deepcopy(flutter_bodies["housing_offer"])
    offer.update(request_id=created["id"], request_revision=created["revision"])
    offer["selection"].update(property_id=str(prop.id), offer_id=offer_id)
    result = post(owner, f"housing-requests/{created['id']}/offers/", offer, 201).data[
        "resource"
    ]
    assert result["selection"]["terms"] == offer["selection"]["terms"]


@pytest.mark.django_db
def test_flutter_invite_body(flutter_bodies, rental_participants):
    _, tenant, _, prop, _ = rental_participants
    group = create_group(tenant, prop)
    body = {
        **flutter_bodies["invite"],
        "group_id": group["id"],
        "group_revision": group["revision"],
    }
    post(tenant, f"housing-groups/{group['id']}/invitations/", body, 201)


@pytest.mark.django_db
def test_flutter_cost_proposal_body(flutter_bodies, rental_participants):
    _, tenant, member, prop, offer_id = rental_participants
    group = create_group(tenant, prop)
    group, _, _ = join_group(tenant, member, group)
    _, selection = resolve_offer_snapshot(prop, offer_id, 2)
    group = group_action(
        tenant, group, "add_shortlist", selection=selection_payload(selection)
    )
    proposal = deepcopy(flutter_bodies["proposal"])
    contributions = list(proposal["contributions"].values())
    proposal.update(
        offer_id=offer_id,
        roster_revision=group["roster_revision"],
        contributions={
            str(tenant.id): contributions[0],
            str(member.id): contributions[1],
        },
    )
    result = group_action(tenant, group, "propose_costs", proposal=proposal)
    assert result["proposals"][0]["total"] == proposal["total"]


@pytest.mark.django_db
def test_flutter_condition_create_and_acknowledgement_roundtrip(
    flutter_bodies, current_lease
):
    owner, tenant, _, lease = current_lease
    body = deepcopy(flutter_bodies["condition_create"])
    body["lease_id"] = str(lease.id)
    body["selection"].update(
        property_id=str(lease.property.id), offer_id=lease.offer_id
    )
    item = post(owner, f"leases/{lease.id}/condition-reports/", body, 201).data[
        "resource"
    ]
    acknowledge = deepcopy(flutter_bodies["condition_acknowledge"])
    acknowledge.update(
        lease_id=str(lease.id),
        expected_revision=item["revision"],
        items=body["items"],
        selection=body["selection"],
    )
    result = post(
        tenant, f"condition-reports/{item['id']}/acknowledge/", acknowledge
    ).data["resource"]
    assert result["status"] == "acknowledged"


@pytest.mark.django_db
def test_flutter_notice_body(flutter_bodies, current_lease):
    _, tenant, _, lease = current_lease
    body = {**flutter_bodies["notice"], "lease_id": str(lease.id)}
    post(tenant, f"leases/{lease.id}/move-out-notices/", body, 201)


@pytest.mark.django_db
def test_flutter_incoming_replacement_consent_body(flutter_bodies, current_lease):
    owner, tenant, candidate, lease = current_lease
    interest = RentalInterest.objects.create(
        property=lease.property,
        tenant=candidate,
        offer_id=lease.offer_id,
        offer_revision=2,
        offer_snapshot=lease.offer_snapshot,
        desired_start=lease.end_date,
        months=1,
        occupants=1,
    )
    item = post(
        tenant,
        f"leases/{lease.id}/replacement-requests/",
        transition_body(lease, "replacement", "submit"),
        201,
    ).data["resource"]
    path = f"replacement-requests/{item['id']}/"
    item = post(
        owner,
        path + "nominate/",
        transition_body(
            lease,
            "replacement",
            "nominate",
            item["revision"],
            candidate_id=str(interest.id),
            candidate_revision=interest.revision,
        ),
    ).data["resource"]
    body = {
        **flutter_bodies["replacement_consent"],
        "expected_revision": item["revision"],
    }
    result = post(candidate, path + "candidate-consent/", body)
    assert result.data["resource"]["status"] == "candidate_consented"
    assert post(candidate, path + "candidate-consent/", body).data == result.data
    post(
        tenant,
        path + "candidate-consent/",
        command(item["revision"], decision="accept"),
        404,
    )


@pytest.mark.django_db
def test_flutter_commute_and_assistant_bodies(flutter_bodies, rental_participants):
    _, tenant, _, prop, _ = rental_participants
    body = deepcopy(flutter_bodies["commute"])
    body["filters"]["city"] = str(prop.city.id)
    post(tenant, "commute-searches/", body, 201)
    post(tenant, "tenant-assistant/turns/", flutter_bodies["assistant"], 201)


@pytest.mark.django_db
def test_flutter_refund_body_and_recovery_subject(flutter_bodies, funded_exit):
    _, tenant, _, lease, attempt = funded_exit
    attempt.refresh_from_db()
    body = {
        **flutter_bodies["refund"],
        "lease_id": str(lease.id),
        "payment_attempt_id": str(attempt.id),
        "payment_revision": attempt.revision,
    }
    result = post(tenant, "refund-requests/", body, 201).data
    assert result["resource"]["allocations"] == body["allocations"]
    recovery = authenticated(tenant).get(
        API + f"rental-operations/{body['request_key']}/?subject_id={attempt.id}"
    )
    assert recovery.status_code == 200 and recovery.data["status"] == "confirmed"
