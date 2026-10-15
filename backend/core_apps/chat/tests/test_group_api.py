import time
import uuid
from unittest.mock import patch
import pytest
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from core_apps.chat.models import Conversation
from core_apps.chat.services.group_send import send_group_message
from core_apps.chat.services.group_provisioning import provision_group
from core_apps.chat.services.group_access import total_unread_count
from .conftest import message_request
from .test_group_media import image_file

pytestmark = pytest.mark.django_db


def base(conversation):
    return reverse("message-list", kwargs={"id": conversation.id}).removesuffix(
        "messages/"
    )


@pytest.mark.parametrize("access", ["member", "disabled", "unverified", "removed"])
def test_group_chat_discovery_preserves_current_access(
    chat_group, api_client, settings, access
):
    group, conversation, user, member = chat_group
    if access == "disabled":
        settings.PLANNING_ENABLED_SERVICES = []
    elif access == "unverified":
        member.is_verified = False
        member.save(update_fields=["is_verified"])
    elif access == "removed":
        group.memberships.filter(user=member).update(status="removed")
    api_client.force_authenticate(member)
    discovery = api_client.get(
        "/api/v1/features/v1/planning-capabilities/",
        {"capability": "housing_groups"},
    )
    assert discovery.status_code == 200
    assert discovery.json()["data"]["configuration"]["group_chat"] is True
    if access in {"disabled", "unverified"}:
        assert discovery.json()["data"]["allowed_actions"] == []
    summary = api_client.get(base(conversation))
    sent = api_client.post(
        base(conversation) + "messages/create/", message_request(), format="json"
    )
    if access == "member":
        assert summary.status_code == 200
        assert "send_message" in summary.json()["data"]["allowed_actions"]
        assert sent.status_code == 201
    else:
        assert summary.status_code == sent.status_code == 403
        assert summary.json()["data"] is sent.json()["data"] is None


def test_group_lookup_is_read_only_and_owner_role_has_no_grant(
    chat_group, api_client, superuser
):
    group, conversation, user, member = chat_group
    url = f"/api/v1/features/v1/housing-groups/{group.id}/chat/"
    superuser.is_verified = True
    superuser.save()
    api_client.force_authenticate(superuser)
    assert api_client.get(url).status_code == 404
    api_client.force_authenticate(member)
    assert api_client.get(url).json()["data"]["conversation_id"] == str(conversation.id)
    conversation.delete()
    response = api_client.get(url)
    assert response.status_code == 503 and response.json()["data"] is None
    assert not Conversation.objects.filter(housing_group=group).exists()


def test_real_multipart_private_binary_and_boundaries(chat_group, api_client):
    group, conversation, user, member = chat_group
    api_client.force_authenticate(user)
    uploaded = api_client.post(
        base(conversation) + "attachments/",
        {
            "file": image_file(),
            "client_upload_id": str(uuid.uuid4()),
            "kind": "image",
        },
        format="multipart",
    )
    assert uploaded.status_code == 201
    attachment = uploaded.json()["data"]
    assert "storage_key" not in attachment
    response = api_client.post(
        base(conversation) + "messages/create/",
        message_request("Images", kind="image", attachment_ids=[attachment["id"]]),
        format="json",
    )
    assert response.status_code == 201
    message = response.json()["data"]
    assert set(response.json()) == {"message", "data"}
    api_client.force_authenticate(member)
    download = api_client.get("/api/v1/" + attachment["content_path"])
    assert download.status_code == 200 and download["Content-Type"] == "image/jpeg"
    assert download["Cache-Control"] == "private, no-store"
    assert b"".join(download.streaming_content).startswith(b"\xff\xd8")
    assert total_unread_count(member) == 1
    group.memberships.filter(user=member).update(status="left")
    assert api_client.get("/api/v1/" + attachment["content_path"]).status_code == 403
    group.memberships.filter(user=member).update(status="active", joined_revision=5)
    provision_group(group)
    assert api_client.get("/api/v1/" + attachment["content_path"]).status_code == 404
    assert (
        api_client.get(
            base(conversation) + f"messages/{message['id']}/context/"
        ).status_code
        == 404
    )
    assert total_unread_count(member) == 0


def test_expired_and_previous_period_cursor_require_resync(chat_group, api_client):
    group, conversation, user, member = chat_group
    for i in range(3):
        send_group_message(conversation, user, message_request(str(i)))
    api_client.force_authenticate(member)
    page = api_client.get(base(conversation) + "messages/", {"limit": 1})
    cursor = page["X-Chat-Event-Cursor"]
    with patch("django.core.signing.time.time", return_value=time.time() + 8 * 86400):
        assert (
            api_client.get(
                base(conversation) + "events/", {"after_cursor": cursor}
            ).status_code
            == 409
        )
    group.memberships.filter(user=member).update(joined_revision=5)
    provision_group(group)
    assert (
        api_client.get(
            base(conversation) + "events/", {"after_cursor": cursor}
        ).status_code
        == 409
    )


def test_rate_limit_returns_real_error_and_system_fields_cannot_be_forged(
    chat_group, api_client, settings
):
    _, conversation, user, _ = chat_group
    settings.CHAT_RATE_LIMITS = {"send": 1}
    api_client.force_authenticate(user)
    url = base(conversation) + "messages/create/"
    forged = api_client.post(
        url, message_request(sender_id=str(user.id)), format="json"
    )
    assert forged.status_code == 400 and forged.json()["data"] is None
    limited = api_client.post(url, message_request(), format="json")
    assert limited.status_code == 429 and limited.json()["data"] is None
    assert limited["Retry-After"]


@pytest.mark.parametrize("pruned", ["all", "head", "middle"])
def test_pruned_events_require_resync(chat_group, api_client, pruned):
    from core_apps.chat.models import ChatEvent
    from core_apps.chat.services.group_send import send_group_message
    from .conftest import message_request

    _, conversation, user, _ = chat_group
    api_client.force_authenticate(user)
    base = f"/api/v1/chat/conversations/{conversation.id}/"
    cursor = api_client.get(base + "messages/")["X-Chat-Event-Cursor"]
    for _ in range(3):
        send_group_message(conversation, user, message_request())
    events = ChatEvent.objects.filter(conversation=conversation)
    if pruned == "all":
        events.delete()
    else:
        events.get(sequence=1 if pruned == "head" else 2).delete()
    response = api_client.get(base + "events/", {"after_cursor": cursor})
    assert response.status_code == 409
    assert response.json()["data"] is None
