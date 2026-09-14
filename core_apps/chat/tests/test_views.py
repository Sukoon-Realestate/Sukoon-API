import uuid
import pytest
from django.urls import reverse
from rest_framework import status

from core_apps.chat.models import ConversationParticipant
from core_apps.chat.services.message_service import (
    get_or_create_direct_conversation,
    send_message,
)


@pytest.mark.django_db
class TestConversationListAPIView:
    def test_unauthenticated_returns_401(self, api_client):
        url = reverse("conversation-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_conversations_happy_path(self, api_client, user, another_user):
        conv = get_or_create_direct_conversation(user=user, other_user=another_user)
        send_message(conversation=conv, sender=another_user, content="Hey!")

        api_client.force_authenticate(user=user)
        url = reverse("conversation-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # GenericJsonRenderer wraps GET responses as {"data": ...}
        results = response.data.get("data", response.data)
        if "results" in results:
            results = results["results"]
        assert len(results) == 1
        assert results[0]["id"] == str(conv.id)
        assert results[0]["unread_count"] == 1
        assert results[0]["other_participant"]["id"] == str(another_user.id)


@pytest.mark.django_db
class TestConversationCreateAPIView:
    def test_unauthenticated_returns_401(self, api_client):
        url = reverse("conversation-create")
        response = api_client.post(url, {"user_id": str(uuid.uuid4())})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_conversation_invalid_payload_returns_400(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse("conversation-create")
        response = api_client.post(url, {"user_id": "invalid-uuid"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_conversation_user_not_found_returns_404(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse("conversation-create")
        response = api_client.post(url, {"user_id": str(uuid.uuid4())})
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_conversation_self_returns_400(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse("conversation-create")
        response = api_client.post(url, {"user_id": str(user.id)})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_conversation_happy_path(self, api_client, user, another_user):
        api_client.force_authenticate(user=user)
        url = reverse("conversation-create")
        response = api_client.post(url, {"user_id": str(another_user.id)})

        assert response.status_code == status.HTTP_200_OK
        payload = response.data.get("data", response.data)
        assert "id" in payload
        assert payload["other_participant"]["id"] == str(another_user.id)


@pytest.mark.django_db
class TestMessageListAPIView:
    def test_unauthenticated_returns_401(self, api_client):
        url = reverse("message-list", kwargs={"id": uuid.uuid4()})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_conversation_not_found_returns_404(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse("message-list", kwargs={"id": uuid.uuid4()})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_non_participant_forbidden_returns_403(
        self, api_client, user, another_user, superuser
    ):
        conv = get_or_create_direct_conversation(user=user, other_user=another_user)

        api_client.force_authenticate(user=superuser)
        url = reverse("message-list", kwargs={"id": conv.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_messages_happy_path(self, api_client, user, another_user):
        conv = get_or_create_direct_conversation(user=user, other_user=another_user)
        send_message(conversation=conv, sender=user, content="Msg 1")
        send_message(conversation=conv, sender=another_user, content="Msg 2")

        api_client.force_authenticate(user=user)
        url = reverse("message-list", kwargs={"id": conv.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get("data", response.data)
        if "results" in results:
            results = results["results"]
        assert len(results) == 2
        assert results[0]["content"] == "Msg 1"
        assert results[1]["content"] == "Msg 2"


@pytest.mark.django_db
class TestMessageCreateAPIView:
    def test_unauthenticated_returns_401(self, api_client):
        url = reverse("message-create", kwargs={"id": uuid.uuid4()})
        response = api_client.post(url, {"content": "Hello"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_payload_returns_400(self, api_client, user, another_user):
        conv = get_or_create_direct_conversation(user=user, other_user=another_user)
        api_client.force_authenticate(user=user)
        url = reverse("message-create", kwargs={"id": conv.id})
        response = api_client.post(url, {"content": ""})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_non_participant_returns_403(
        self, api_client, user, another_user, superuser
    ):
        conv = get_or_create_direct_conversation(user=user, other_user=another_user)
        api_client.force_authenticate(user=superuser)
        url = reverse("message-create", kwargs={"id": conv.id})
        response = api_client.post(url, {"content": "Intruder"})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_send_message_happy_path(self, api_client, user, another_user):
        conv = get_or_create_direct_conversation(user=user, other_user=another_user)
        api_client.force_authenticate(user=user)
        url = reverse("message-create", kwargs={"id": conv.id})
        response = api_client.post(url, {"content": "I want to visit the villa."})

        assert response.status_code == status.HTTP_201_CREATED
        payload = response.data.get("data", response.data)
        assert payload["content"] == "I want to visit the villa."
        assert payload["sender"]["id"] == str(user.id)


@pytest.mark.django_db
class TestConversationReadAPIView:
    def test_unauthenticated_returns_401(self, api_client):
        url = reverse("conversation-read", kwargs={"id": uuid.uuid4()})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_non_participant_returns_403(
        self, api_client, user, another_user, superuser
    ):
        conv = get_or_create_direct_conversation(user=user, other_user=another_user)
        api_client.force_authenticate(user=superuser)
        url = reverse("conversation-read", kwargs={"id": conv.id})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_mark_read_happy_path(self, api_client, user, another_user):
        conv = get_or_create_direct_conversation(user=user, other_user=another_user)
        send_message(conversation=conv, sender=user, content="Msg")

        api_client.force_authenticate(user=another_user)
        url = reverse("conversation-read", kwargs={"id": conv.id})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        part = ConversationParticipant.objects.get(conversation=conv, user=another_user)
        assert part.unread_count == 0
