"""A5-03: chat projections never disclose a counterpart's account email (Sprint 01)."""

import json

import pytest
from rest_framework.test import APIClient

from core_apps.chat.services.message_service import get_or_create_direct_conversation

pytestmark = pytest.mark.django_db


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def test_starting_a_chat_does_not_return_the_counterpart_email(user, another_user):
    response = _client(user).post("/api/v1/chat/conversations/create/", {"user_id": str(another_user.id)}, format="json")
    assert response.status_code == 200, response.content
    body = json.dumps(response.json())
    assert another_user.email not in body
    other = response.json()["data"]["other_participant"]
    assert other["email"] == ""
    assert other["id"] == str(another_user.id)


def test_list_detail_and_history_omit_counterpart_email(user, another_user):
    conv = get_or_create_direct_conversation(user=user, other_user=another_user)
    client = _client(user)
    client.post(f"/api/v1/chat/conversations/{conv.id}/messages/create/", {"content": "hi"}, format="json")
    peer = _client(another_user)
    peer.post(f"/api/v1/chat/conversations/{conv.id}/messages/create/", {"content": "hello"}, format="json")

    for url in (
        "/api/v1/chat/conversations/",
        f"/api/v1/chat/conversations/{conv.id}/",
        f"/api/v1/chat/conversations/{conv.id}/messages/",
    ):
        response = client.get(url)
        assert response.status_code == 200, (url, response.status_code)
        assert another_user.email not in json.dumps(response.json()), url


def test_own_sender_projection_keeps_the_viewers_email(user, another_user):
    conv = get_or_create_direct_conversation(user=user, other_user=another_user)
    response = _client(user).post(
        f"/api/v1/chat/conversations/{conv.id}/messages/create/", {"content": "mine"}, format="json"
    )
    assert response.status_code == 201
    assert response.json()["data"]["sender"]["email"] == user.email
