"""Interest requests work independently of payment and signing providers."""

import copy
import uuid
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from core_apps.features.models import IdempotencyRecord, RentalInterest, TermsProposal
from core_apps.features.services.rental_foundation import capabilities_for
from .test_rental_phase2 import agreement_terms, authenticated, rental_participants


API = "/api/v1/features/v1/"
pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def production_without_provider(settings):
    settings.RENTAL_PROVIDER_BACKEND = "disabled"
    settings.RENTAL_FAKE_PROVIDER_ALLOWED = False
    settings.RENTAL_RUNTIME_ENVIRONMENT = "production"


def interest_body(property_obj, offer_id):
    return {
        "property_id": str(property_obj.id),
        "offer_id": offer_id,
        "offer_revision": 2,
        "desired_start": str(timezone.localdate() + timedelta(days=10)),
        "months": 1,
        "occupants": 1,
        "message": "Interested in this accommodation",
        "request_key": str(uuid.uuid4()),
        "expected_revision": 0,
    }


def readiness(client, subject_id, action):
    return client.get(
        API + f"rental-capabilities/?subject_id={subject_id}&action={action}"
    )


@pytest.mark.parametrize("provider", ["disabled", "fake"])
def test_create_interest_without_provider_preserves_receipt_and_owner_delivery(
    rental_participants,
    settings,
    provider,
    django_capture_on_commit_callbacks,  # noqa: F811 - shared fixture
):
    # Even a configured fake provider must stay disabled in production.
    settings.RENTAL_PROVIDER_BACKEND = provider
    settings.RENTAL_FAKE_PROVIDER_ALLOWED = True
    owner, tenant, stranger, property_obj, offer_id = rental_participants
    client = authenticated(tenant)
    body = interest_body(property_obj, offer_id)

    grant = readiness(client, property_obj.id, "create_rental_interest")
    assert grant.status_code == 200
    assert grant["Cache-Control"] == "private, no-store"
    assert grant.data["enabled_capabilities"] == ["rental_interests"]
    assert grant.data["allowed_actions"] == ["create_rental_interest"]
    assert grant.data["blocking_reasons"] == []

    from core_apps.features.planning_models import PlanningEvent
    from core_apps.features.services.planning_notifications import (
        deliver_planning_events,
    )

    created = client.post(API + "rental-interests/", body, format="json")
    assert created.status_code == 201, created.data
    event = PlanningEvent.objects.get(recipient=owner)
    assert event.destination["workspace"] == "owner"
    assert event.delivered_at is None
    with patch(
        "core_apps.notifications.services.fcm_service.FCMService.send_push_to_user",
        return_value=1,
    ):
        assert deliver_planning_events() == 1
        assert deliver_planning_events() == 0
    event.refresh_from_db()
    assert event.notification_id is not None
    assert event.delivered_at is not None

    resource = created.data["resource"]
    receipt = created.data["operation_receipt"]
    assert resource["property_id"] == str(property_obj.id)
    assert resource["offer_id"] == offer_id
    assert resource["offer_snapshot"]["offer_revision"] == 2
    assert resource["status"] == "submitted"
    assert resource["allowed_actions"] == ["withdraw"]
    assert receipt["request_key"] == body["request_key"]
    assert receipt["subject_id"] == resource["id"]
    assert receipt["revision"] == 1
    assert event.destination["rental_interest_id"] == resource["id"]

    owner_client = authenticated(owner)
    owner_list = owner_client.get(API + "rental-interests/?workspace=owner")
    assert [item["id"] for item in owner_list.data["results"]] == [resource["id"]]
    assert owner_list.data["results"][0]["allowed_actions"] == [
        "reject",
        "request_information",
        "mark_under_review",
    ]
    detail_url = API + f"rental-interests/{resource['id']}/"
    assert owner_client.get(detail_url).status_code == 200
    assert authenticated(stranger).get(detail_url).status_code == 404

    replay = client.post(API + "rental-interests/", body, format="json")
    assert replay.status_code == 201
    assert replay.data == created.data
    recovered = client.get(
        API + f"rental-operations/{body['request_key']}/?subject_id={property_obj.id}"
    )
    assert recovered.data["status"] == "confirmed"
    assert recovered.data["operation_receipt"] == receipt
    changed = client.post(
        API + "rental-interests/", {**body, "months": 2}, format="json"
    )
    assert changed.status_code == 409
    assert changed["X-App-Error-Code"] == "idempotency_conflict"
    assert RentalInterest.objects.count() == 1
    assert (
        IdempotencyRecord.objects.filter(request_key=body["request_key"]).count() == 1
    )


@pytest.mark.parametrize("actor", ["owner", "unverified", "inactive"])
def test_interest_still_requires_verified_other_account(
    rental_participants, actor
):  # noqa: F811
    owner, tenant, _, property_obj, offer_id = rental_participants
    user = owner if actor == "owner" else tenant
    if actor == "unverified":
        user.is_verified = False
    elif actor == "inactive":
        user.is_active = False
    user.save()
    client = authenticated(user)
    grant = capabilities_for(user, property_obj, "create_rental_interest")
    assert "create_rental_interest" not in grant["allowed_actions"]
    assert grant["blocking_reasons"]
    result = client.post(
        API + "rental-interests/", interest_body(property_obj, offer_id), format="json"
    )
    assert result.status_code in {400, 403}
    assert RentalInterest.objects.count() == 0


@pytest.mark.parametrize(
    "property_change", [{"is_verified": False}, {"status": "pending"}]
)
def test_unavailable_property_cannot_receive_interest(
    rental_participants, property_change
):  # noqa: F811
    _, tenant, _, property_obj, offer_id = rental_participants
    for field, value in property_change.items():
        setattr(property_obj, field, value)
    property_obj.save()
    grant = capabilities_for(tenant, property_obj, "create_rental_interest")
    assert "create_rental_interest" not in grant["allowed_actions"]
    assert grant["blocking_reasons"]
    result = authenticated(tenant).post(
        API + "rental-interests/", interest_body(property_obj, offer_id), format="json"
    )
    assert result.status_code == 403
    assert RentalInterest.objects.count() == 0


@pytest.mark.parametrize(
    "offer_change,expected_status",
    [
        ({"revision": 3}, 409),
        ({"archived": True}, 409),
        ({"availability": "unavailable"}, 409),
        ({"terms": {"price": "10000", "price_period": "daily"}}, 400),
        ({"id": str(uuid.uuid4())}, 400),
    ],
)
def test_selected_offer_is_still_validated(
    rental_participants, offer_change, expected_status  # noqa: F811 - shared fixture
):
    _, tenant, _, property_obj, offer_id = rental_participants
    inventory = copy.deepcopy(property_obj.rental_inventory)
    inventory["offers"][0].update(offer_change)
    property_obj.rental_inventory = inventory
    property_obj.save(update_fields=["rental_inventory"])
    result = authenticated(tenant).post(
        API + "rental-interests/", interest_body(property_obj, offer_id), format="json"
    )
    assert result.status_code == expected_status
    assert RentalInterest.objects.count() == 0


@pytest.mark.parametrize("decision", ["withdraw", "reject"])
def test_interest_can_be_closed_without_provider_and_replayed(
    rental_participants, decision
):  # noqa: F811
    owner, tenant, stranger, property_obj, offer_id = rental_participants
    tenant_client = authenticated(tenant)
    created = tenant_client.post(
        API + "rental-interests/", interest_body(property_obj, offer_id), format="json"
    )
    assert created.status_code == 201, created.data
    interest_id = created.data["resource"]["id"]
    client = tenant_client if decision == "withdraw" else authenticated(owner)
    grant = readiness(client, interest_id, decision)
    assert grant.data["allowed_actions"] == (
        ["reject", "request_information", "mark_under_review"]
        if decision == "reject"
        else [decision]
    )
    assert grant.data["blocking_reasons"] == []
    body = {
        "decision": decision,
        "expected_revision": 1,
        "request_key": str(uuid.uuid4()),
    }
    url = API + f"rental-interests/{interest_id}/respond/"
    assert authenticated(stranger).post(url, body, format="json").status_code == 404
    result = client.post(url, body, format="json")
    assert result.status_code == 200
    assert result.data["resource"]["status"] == (
        "withdrawn" if decision == "withdraw" else "rejected"
    )
    assert result.data["resource"]["revision"] == 2
    assert result.data["resource"]["allowed_actions"] == []
    assert client.post(url, body, format="json").data == result.data
    closed_grant = readiness(client, interest_id, decision)
    assert decision not in closed_grant.data["allowed_actions"]
    repeated = client.post(
        url,
        {**body, "expected_revision": 2, "request_key": str(uuid.uuid4())},
        format="json",
    )
    assert repeated.status_code == 403
    assert RentalInterest.objects.get(id=interest_id).revision == 2


def test_agreement_and_onboarding_remain_provider_gated(
    rental_participants,
):  # noqa: F811
    owner, tenant, _, property_obj, offer_id = rental_participants
    created = authenticated(tenant).post(
        API + "rental-interests/", interest_body(property_obj, offer_id), format="json"
    )
    assert created.status_code == 201, created.data
    interest = created.data["resource"]
    client = authenticated(owner)
    grant = readiness(client, interest["id"], "create_terms_proposal")
    assert grant.data["enabled_capabilities"] == ["rental_interests"]
    assert grant.data["allowed_actions"] == [
        "reject",
        "request_information",
        "mark_under_review",
    ]
    assert grant.data["blocking_reasons"]
    starts_on = timezone.localdate() + timedelta(days=10)
    terms = client.post(
        API + "terms-proposals/",
        {
            "interest_id": interest["id"],
            "offer_id": offer_id,
            "interest_revision": 1,
            "offer_revision": 2,
            "expected_revision": 0,
            "request_key": str(uuid.uuid4()),
            "terms": agreement_terms(starts_on, starts_on + timedelta(days=31)),
        },
        format="json",
    )
    assert terms.status_code == 403
    assert terms["X-App-Error-Code"] == "capability_unavailable"
    assert TermsProposal.objects.count() == 0
    profile = client.get(API + "owner-payment-profile/").data
    profile_grant = readiness(client, profile["id"], "onboard_beneficiary")
    assert "onboard_beneficiary" not in profile_grant.data["allowed_actions"]
    onboarding = client.post(
        API + "owner-payment-profile/onboarding-session/",
        {
            "expected_revision": profile["revision"],
            "request_key": str(uuid.uuid4()),
            "accepted_policy_versions": ["rental-policy-v1"],
        },
        format="json",
    )
    assert onboarding.status_code == 403
    assert onboarding["X-App-Error-Code"] == "capability_unavailable"
