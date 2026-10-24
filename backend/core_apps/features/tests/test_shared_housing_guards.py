import copy
from unittest.mock import patch
import pytest
from django.utils import timezone
from datetime import timedelta
from .test_shared_housing import (
    pair,
    create,
    candidate,
    submitted,
    accepted,
    act,
    proposal_act,
    post,
    API,
)
from .test_rental_phase2 import rental_participants, authenticated
from .test_funded_settlement import command
from core_apps.features.models import RentalInterest, TenancyInvitation
from core_apps.features.shared_housing_models import (
    SharedHousingPlan,
    SharedHousingAllocation,
)
from core_apps.features.services.shared_housing.counts import pending_count

pytestmark = pytest.mark.django_db


def test_exact_revision_and_changed_inventory_revoke_selection(pair):
    _, first, second, prop, _ = pair
    plan = candidate(pair)
    old = copy.deepcopy(plan)
    plan = proposal_act(first, plan, "consent_selection", consent=True)
    path = f"shared-housing-plans/{plan['id']}/proposals/{plan['proposals'][0]['id']}/consent_selection/"
    post(second, path, command(old["revision"], consent=True), 409)
    prop.rental_inventory["offers"][1]["revision"] += 1
    prop.save()
    post(second, path, command(plan["revision"], consent=True), 409)
    assert not RentalInterest.objects.exists()


@pytest.mark.parametrize(
    "invalid",
    [
        None,
        {},
        [1, 2],
        [{"tenant_id": [], "selection": {}}] * 2,
        [{"tenant_id": "a", "selection": []}] * 2,
    ],
)
def test_invalid_allocations_return_validation_not_server_error(pair, invalid):
    _, first, second, _, _ = pair
    plan, _ = create(pair)
    plan = act(second, plan, "accept_invite")
    post(
        first,
        f"shared-housing-plans/{plan['id']}/proposals/",
        command(plan["revision"], allocations=invalid),
        400,
    )


def test_expiry_hides_public_demand_and_allows_new_plan(pair):
    owner, first, second, _, _ = pair
    plan, _ = create(pair)
    plan = act(second, plan, "accept_invite")
    for user in [first, second]:
        plan = act(user, plan, "approve_publication", consent=True)
    plan = act(first, plan, "publish")
    SharedHousingPlan.objects.filter(id=plan["id"]).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    assert authenticated(owner).get(API + "shared-housing-demand/").data["count"] == 0
    assert (
        authenticated(first)
        .get(API + f"shared-housing-plans/{plan['id']}/")
        .data["status"]
        == "expired"
    )
    another, _ = create(pair)
    assert another["id"] != plan["id"]


def test_owner_offer_both_review_it_and_submit(pair):
    owner, first, second, prop, _ = pair
    plan, _ = create(pair)
    plan = act(second, plan, "accept_invite")
    for user in [first, second]:
        plan = act(user, plan, "approve_publication", consent=True)
    plan = act(first, plan, "publish")
    lines = [
        {
            "tenant_id": str(user.id),
            "selection": {
                "property_id": str(prop.id),
                "offer_id": offer["id"],
                "offer_revision": 1,
            },
        }
        for user, offer in zip([first, second], prop.rental_inventory["offers"])
    ]
    plan = post(
        owner,
        f"shared-housing-plans/{plan['id']}/proposals/",
        command(plan["revision"], allocations=lines),
    )
    for user in [first, second]:
        plan = proposal_act(user, plan, "consent_selection", consent=True)
    plan = proposal_act(first, plan, "submit")
    assert plan["status"] == "reviewing"
    assert (
        authenticated(owner)
        .get(API + "owner-shared-housing-applications/")
        .data["count"]
        == 1
    )


def test_owner_changes_require_reason_and_reset_both(pair):
    owner, first, second, _, _ = pair
    plan = accepted(pair)
    plan = proposal_act(first, plan, "consent_terms", independent_consent=True)
    path = f"shared-housing-plans/{plan['id']}/proposals/{plan['proposals'][0]['id']}/request_changes/"
    post(owner, path, command(plan["revision"]), 400)
    plan = proposal_act(owner, plan, "request_changes", note="Choose a later date")
    assert plan["status"] == "searching"
    assert RentalInterest.objects.filter(status="withdrawn").count() == 2
    assert not TenancyInvitation.objects.exists()
    assert plan["proposals"][0]["note"] == "Choose a later date"


def test_counts_track_the_person_who_needs_to_act(pair):
    owner, first, second, _, _ = pair
    plan, _ = create(pair)
    assert pending_count(first) == 0 and pending_count(second) == 1
    plan = accepted(pair)
    assert pending_count(owner, owner=True) == 0
    assert pending_count(first) == pending_count(second) == 1
    plan = proposal_act(first, plan, "consent_terms", independent_consent=True)
    assert pending_count(first) == 0 and pending_count(second) == 1
    plan = proposal_act(second, plan, "consent_terms", independent_consent=True)
    assert pending_count(owner, owner=True) == 1
    proposal_act(owner, plan, "send_invitations")
    assert pending_count(owner, owner=True) == pending_count(second) == 0


def test_second_invitation_failure_rolls_back_pair(pair):
    owner, first, second, _, _ = pair
    plan = accepted(pair)
    for user in [first, second]:
        plan = proposal_act(user, plan, "consent_terms", independent_consent=True)
    from core_apps.features.services.rental_application_records import create_invitation

    calls = []

    def fail_second(**kwargs):
        calls.append(1)
        if len(calls) == 2:
            from rest_framework.exceptions import ValidationError

            raise ValidationError("Injected invitation failure")
        return create_invitation(**kwargs)

    with patch(
        "core_apps.features.services.shared_housing.commands.create_invitation",
        side_effect=fail_second,
    ):
        post(
            owner,
            f"shared-housing-plans/{plan['id']}/proposals/{plan['proposals'][0]['id']}/send_invitations/",
            command(plan["revision"]),
            400,
        )
    assert not TenancyInvitation.objects.exists()
    assert SharedHousingPlan.objects.get(id=plan["id"]).status == "reviewing"
    assert not SharedHousingAllocation.objects.filter(invitation__isnull=False).exists()


def test_connection_withdrawal_closes_both_pending_requests(pair):
    _, first, _, _, connection = pair
    plan = submitted(pair)
    post(
        first,
        f"roommate-connections/{connection.id}/withdraw/",
        command(connection.revision, decision="withdraw"),
    )
    assert SharedHousingPlan.objects.get(id=plan["id"]).status == "closed"
    assert RentalInterest.objects.filter(status="withdrawn").count() == 2


def test_owner_count_includes_submitted_pair(pair):
    submitted(pair)
    assert pending_count(pair[0], owner=True) == 1


def test_disabled_service_keeps_exact_withdrawal_authority(pair, settings):
    _, first, second, _, _ = pair
    plan, _ = create(pair)
    settings.SHARED_HOUSING_ENABLED = False
    result = authenticated(second).get(
        API
        + f"planning-capabilities/?capability=shared_housing_plans&subject_id={plan['id']}&action=decline_invite"
    )
    assert (
        result.data["allowed_actions"]
        == result.data["privacy_actions"]
        == ["decline_invite"]
    )
    plan = act(second, plan, "decline_invite")
    assert plan["status"] == "closed"


def test_joint_requests_only_appear_in_joint_inbox_until_handoff(pair):
    from core_apps.features.services.request_counts import pending_request_counts

    owner, first, _, _, _ = pair
    submitted(pair)
    assert pending_request_counts(owner, owner=True)["rental_interests"] == 0
    assert pending_request_counts(owner, owner=True)["shared_housing_plans"] == 1
    assert (
        authenticated(first)
        .get(API + "rental-interests/?workspace=tenant")
        .data["count"]
        == 0
    )
    assert (
        authenticated(owner)
        .get(API + "rental-interests/?workspace=owner")
        .data["count"]
        == 0
    )


def test_arabic_shared_validation_uses_localized_http_message(pair):
    # The catalog is used by the shared HTTP exception renderer.
    from core_apps.common.translation_catalog import EN_TO_AR_MESSAGES

    assert (
        EN_TO_AR_MESSAGES["Both participants must approve publication."]
        == "يجب أن يوافق الطرفان على نشر الطلب."
    )
    _, first, second, _, _ = pair
    plan, _ = create(pair)
    plan = act(second, plan, "accept_invite")
    client = authenticated(first)
    response = client.post(
        API + f"shared-housing-plans/{plan['id']}/publish/",
        command(plan["revision"]),
        format="json",
        HTTP_ACCEPT_LANGUAGE="ar",
    )
    assert response.status_code == 409
    assert "يجب أن يوافق الطرفان" in str(response.json())


def test_accepted_roommate_card_links_existing_plan(pair):
    _, first, _, _, _ = pair
    plan, _ = create(pair)
    result = authenticated(first).get(API + "roommate-connections/").data
    assert result["results"][0]["shared_housing_plan_id"] == plan["id"]


def test_recovery_uses_receipt_without_repeating_creation(pair):
    _, first, _, _, _ = pair
    plan, body = create(pair)
    result = authenticated(first).get(
        API + f"rental-operations/{body['request_key']}/?subject_id={first.id}"
    )
    assert result.status_code == 200
    assert result.data["operation_receipt"]["subject_id"] == plan["id"]
    assert SharedHousingPlan.objects.count() == 1
