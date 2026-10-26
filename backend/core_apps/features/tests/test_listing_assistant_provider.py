"""Local transport evidence only; these tests never call Gemini."""

# flake8: noqa: F401,F811 -- pytest fixture imports.
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import patch

import pytest
from django.db import connection, connections
from django.utils import timezone
from rest_framework.test import APIClient

from core_apps.features.models import IdempotencyRecord, ListingSuggestion
from core_apps.features.services.planning_providers import DiscoveryUnavailable
from core_apps.properties.models import Property
from core_apps.properties.services.property import PropertyService
from core_apps.users.models import AuthSession
from core_apps.users.services.sessions import issue_refresh
from .test_tenancy_invitations import participants, owned_property, authenticated

pytestmark = pytest.mark.django_db
API = "/api/v1/features/v1/listing-suggestions/"
PROVIDER = "core_apps.features.services.listing_assistant.post_json"


@pytest.fixture(autouse=True)
def configured(settings):
    settings.PLANNING_GEMINI_API_KEY = "fixture-listing-secret-never-log"
    settings.PLANNING_GEMINI_MODEL = "fixture-existing-model"


def body(prop=None, language="en"):
    return {
        "property_id": str(prop.id) if prop else "",
        "facts": {
            "title": "Owner supplied",
            "description": "Two rooms",
            "bedrooms": 2,
            "amenities": ["wifi"],
        },
        "language": language,
        "request_key": str(uuid.uuid4()),
    }


def completion(**changes):
    value = {
        "title": "Two-room home",
        "description": "Home with two rooms and Wi-Fi.",
        "used_facts": ["bedrooms", "amenities"],
        **changes,
    }
    return {
        "candidates": [
            {
                "finishReason": "STOP",
                "content": {"parts": [{"text": json.dumps(value)}]},
            }
        ]
    }


@pytest.mark.parametrize("language", ["ar", "en"])
def test_provider_copy_is_private_reviewable_and_replayed_once(
    participants, owned_property, language
):
    owner, _, stranger = participants
    payload = body(owned_property, language)
    client = authenticated(owner)
    original_title = owned_property.title
    with patch(PROVIDER, return_value=completion()) as provider:
        result = client.post(API, payload, format="json")
        replay = client.post(API, payload, format="json")
        conflict = client.post(
            API, {**payload, "facts": {"title": "Different"}}, format="json"
        )
    assert result.status_code == replay.status_code == 201
    assert result.data == replay.data and provider.call_count == 1
    sent = provider.call_args.args
    assert "fixture-existing-model:generateContent" in sent[0]
    assert json.loads(sent[1]["contents"][0]["parts"][0]["text"]) == {
        "facts": payload["facts"],
        "language": language,
    }
    assert owner.email not in json.dumps(sent[1])
    assert conflict.status_code == 409
    assert result.data["warnings"] and result["Cache-Control"] == "private, no-store"
    owned_property.refresh_from_db()
    assert owned_property.title == original_title
    assert ListingSuggestion.objects.count() == 1
    assert authenticated(stranger).post(API, payload, format="json").status_code == 404


def test_missing_configuration_keeps_manual_property_edit_available(
    participants, owned_property, settings
):
    settings.PLANNING_GEMINI_API_KEY = ""
    with patch(PROVIDER) as provider:
        response = authenticated(participants[0]).post(
            API, body(owned_property), format="json"
        )
        provider.assert_not_called()
    assert (
        response.status_code == 503
        and response.data["code"] == "assistant_not_configured"
    )
    assert (
        not ListingSuggestion.objects.exists()
        and not IdempotencyRecord.objects.exists()
    )
    prop = PropertyService.update_property(
        owned_property, {"title": "Written manually"}
    )
    assert prop.title == "Written manually"


@pytest.mark.parametrize(
    "raw",
    [
        None,
        {"candidates": [None]},
        completion(title=""),
        completion(used_facts=["invented_pool"]),
        completion(description="x" * 5001),
        {"candidates": [{"finishReason": "MAX_TOKENS"}]},
    ],
)
def test_invalid_provider_result_never_becomes_a_saved_suggestion(participants, raw):
    payload = body()
    with patch(PROVIDER, return_value=raw) as provider:
        first = authenticated(participants[0]).post(API, payload, format="json")
        replay = authenticated(participants[0]).post(API, payload, format="json")
    assert first.status_code == replay.status_code == 503
    assert first.data["code"] == "invalid_provider_response"
    assert provider.call_count == 1 and not ListingSuggestion.objects.exists()


def test_timeout_is_not_reissued_by_replaying_the_key(participants):
    payload = body()
    with patch(PROVIDER, side_effect=DiscoveryUnavailable()) as provider:
        for _ in range(2):
            assert (
                authenticated(participants[0])
                .post(API, payload, format="json")
                .status_code
                == 503
            )
    assert provider.call_count == 1
    assert IdempotencyRecord.objects.get().recovery_status == "unknown"
    with patch(PROVIDER, return_value=completion()) as provider:
        response = authenticated(participants[0]).post(
            API, {**payload, "request_key": str(uuid.uuid4())}, format="json"
        )
    assert response.status_code == 201 and provider.call_count == 1


@pytest.mark.parametrize(
    "facts",
    [
        {"private_identity": "secret"},
        {"amenities": ["invented_pool"]},
        {"price": "NaN"},
        {"price": "-1"},
        {"title": "x" * 151},
        {},
        {"bedrooms": True},
    ],
)
def test_invalid_or_private_facts_never_reach_provider(participants, facts):
    with patch(PROVIDER) as provider:
        response = authenticated(participants[0]).post(
            API, {**body(), "facts": facts}, format="json"
        )
        provider.assert_not_called()
    assert response.status_code == 400
    assert not IdempotencyRecord.objects.exists()


def test_ownership_is_rechecked_after_provider_result(participants, owned_property):
    def transferred(*args):
        Property.objects.filter(pk=owned_property.pk).update(owner=participants[2])
        return completion()

    with patch(PROVIDER, side_effect=transferred):
        result = authenticated(participants[0]).post(
            API, body(owned_property), format="json"
        )
    assert result.status_code == 404 and not ListingSuggestion.objects.exists()


def test_session_revocation_during_generation_blocks_result(participants):
    token = issue_refresh(participants[0])
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def revoked(*args):
        AuthSession.objects.filter(id=token["session_id"]).update(
            revoked_at=timezone.now()
        )
        return completion()

    with patch(PROVIDER, side_effect=revoked) as provider:
        response = client.post(API, body(), format="json")
    assert response.status_code == 401 and provider.call_count == 1
    assert not ListingSuggestion.objects.exists()


def test_unverified_account_cannot_invoke_provider(participants):
    owner = participants[0]
    owner.is_verified = False
    owner.save(update_fields=["is_verified"])
    with patch(PROVIDER) as provider:
        response = authenticated(owner).post(API, body(), format="json")
        provider.assert_not_called()
    assert response.status_code == 403


@pytest.mark.parametrize(
    "changes",
    [
        {"language": []},
        {"language": "fr"},
        {"request_key": " "},
        {"request_key": "x" * 101},
        {"property_id": ["bad"]},
    ],
)
def test_invalid_command_is_rejected_before_provider(participants, changes):
    with patch(PROVIDER) as provider:
        response = authenticated(participants[0]).post(
            API, {**body(), **changes}, format="json"
        )
        provider.assert_not_called()
    assert response.status_code == 400


@pytest.mark.django_db(transaction=True)
def test_concurrent_same_key_claim_calls_provider_without_database_transaction_once(
    participants,
):
    started, release = Event(), Event()
    payload = body()

    def provider(*args):
        assert not connection.in_atomic_block
        started.set()
        assert release.wait(10)
        return completion()

    def first():
        try:
            return authenticated(participants[0]).post(API, payload, format="json")
        finally:
            connections.close_all()

    with patch(PROVIDER, side_effect=provider) as transport, ThreadPoolExecutor(
        max_workers=1
    ) as pool:
        pending = pool.submit(first)
        try:
            assert started.wait(10)
            second = authenticated(participants[0]).post(API, payload, format="json")
            assert second.status_code == 409
        finally:
            release.set()
        assert pending.result(15).status_code == 201
    assert transport.call_count == ListingSuggestion.objects.count() == 1
