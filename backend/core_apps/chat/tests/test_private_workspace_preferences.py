"""Workspace identity, bilateral consent, private history and mutation boundaries."""
from datetime import timedelta
import pytest
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from core_apps.chat.models import ChatList, ConversationWorkspace, Message
from core_apps.chat.services.message_service import get_or_create_direct_conversation
from core_apps.chat.services.conversation_preferences import update_preferences, preferences_payload
from core_apps.chat.services.workspace_inbox import scoped
from core_apps.chat.services.group_access import authorize, visible_messages
from core_apps.chat.services.group_send import send_group_message
from core_apps.chat.services.message_mutations import mutate_message
from core_apps.chat.services.group_projection import message_payload
from core_apps.properties.tests.conftest import apartment_type, cairo_city, cairo_governorate  # noqa: F401
from .test_direct_media import direct_chat  # noqa: F401
from .test_message_mutations import packet
from .conftest import message_request

pytestmark = pytest.mark.django_db


def contextual(user, peer, workspace):
    return get_or_create_direct_conversation(user=user, other_user=peer, workspace=workspace)


def test_same_people_separate_workspaces_and_idempotent_retry(direct_chat):
    _, user, peer = direct_chat
    individual = contextual(user, peer, "individual")
    student = contextual(user, peer, "student")
    assert individual != student
    assert contextual(user, peer, "individual") == individual
    assert contextual(peer, user, "individual") == individual
    assert list(scoped(user, "individual")) == [individual]
    assert list(scoped(user, "student")) == [student]
    with pytest.raises(ValidationError):
        scoped(user, "all")


def test_block_is_bilateral_across_workspaces_and_unblock_is_owned(direct_chat):
    _, user, peer = direct_chat
    first, second = contextual(user, peer, "individual"), contextual(user, peer, "student")
    update_preferences(first, user, {"blocked": True})
    assert contextual(user, peer, "individual") == first
    with pytest.raises(PermissionDenied):
        contextual(user, peer, "owner")
    for chat in (first, second):
        for actor in (user, peer):
            with pytest.raises(PermissionDenied):
                send_group_message(chat, actor, message_request())
    update_preferences(first, peer, {"blocked": False})
    assert preferences_payload(first, peer)["is_blocked"]
    update_preferences(second, user, {"blocked": False})
    assert not preferences_payload(first, peer)["is_blocked"]
    assert send_group_message(first, peer, message_request()).id


def test_delete_for_me_cutoff_retry_preserves_new_messages(direct_chat):
    _, user, peer = direct_chat
    chat = contextual(user, peer, "individual")
    old = send_group_message(chat, peer, message_request("Old"))
    changes = {"delete_for_me": True, "delete_through_sequence": old.sequence}
    update_preferences(chat, user, changes)
    assert not scoped(user, "individual").exists()
    assert scoped(peer, "individual").exists()
    new = send_group_message(chat, peer, message_request("New"))
    update_preferences(chat, user, changes)
    _, participant, _ = authorize(chat, user)
    assert list(visible_messages(chat, participant)) == [new]
    _, other, _ = authorize(chat, peer)
    assert list(visible_messages(chat, other)) == [old, new]
    assert scoped(user, "individual").exists()
    assert participant.unread_count == 1


def test_preferences_and_lists_are_private_and_workspace_scoped(direct_chat):
    _, user, peer = direct_chat
    chat = contextual(user, peer, "individual")
    own = ChatList.objects.create(user=user, workspace="individual", name="Visits")
    other_scope = ChatList.objects.create(user=user, workspace="student", name="Visits")
    result = update_preferences(chat, user, {"is_favorite": True, "is_muted": True, "list_ids": [str(own.id)]})
    assert result["is_favorite"] and result["is_muted"]
    assert not preferences_payload(chat, peer)["is_favorite"]
    for actor, target in ((peer, own), (user, other_scope)):
        with pytest.raises(PermissionDenied):
            update_preferences(chat, actor, {"list_ids": [str(target.id)]})
    with pytest.raises(ValidationError):
        update_preferences(chat, user, {"list_ids": ["invalid"]})


def test_delete_after_one_hour_rejected_and_edits_visible_to_both(direct_chat):
    chat, user, peer = direct_chat
    message = send_group_message(chat, user, message_request("Before"))
    mutate_message(chat, user, packet(chat, user, message, content="After"))
    message.refresh_from_db()
    for actor in (user, peer):
        _, participant, grant = authorize(chat, actor)
        history = message_payload(message, participant, grant)["edit_history"]
        assert [(x["before"], x["after"]) for x in history] == [("Before", "After")]
    Message.objects.filter(pk=message.pk).update(created_at=timezone.now() - timedelta(hours=1, seconds=1))
    message.refresh_from_db()
    change = packet(chat, user, message, type="message.delete")
    change.pop("content")
    with pytest.raises(PermissionDenied):
        mutate_message(chat, user, change)
    _, participant, grant = authorize(chat, user)
    assert "delete_message" not in message_payload(message, participant, grant)["allowed_actions"]


def test_workspace_is_assigned_automatically_and_not_a_user_preference(direct_chat):
    chat, user, peer = direct_chat
    assert contextual(user, peer, "individual") == chat
    assert preferences_payload(chat, user)["workspace"] == "individual"
    assert preferences_payload(chat, peer)["workspace"] == "individual"
    with pytest.raises(ValidationError):
        update_preferences(chat, user, {"workspace": "owner"})
    assert send_group_message(chat, user, message_request()).id


def test_private_preferences_endpoints_reject_foreign_viewers_and_bad_ids(direct_chat, superuser):
    from rest_framework.test import APIClient
    _, user, peer = direct_chat
    chat = contextual(user, peer, "individual")
    client = APIClient()
    client.force_authenticate(user)
    path = f"/api/v1/chat/conversations/{chat.id}/preferences/"
    response = client.get(path)
    assert response.status_code == 200, response.data
    result = client.post("/api/v1/chat/lists/", {"workspace": "individual", "name": "Visits"}, format="json")
    assert result.status_code == 200, result.data
    listed = client.get("/api/v1/chat/lists/", {"workspace": "individual"})
    assert listed.status_code == 200
    assert listed.json()["data"] == [{"id": result.json()["data"]["id"], "name": "Visits"}]
    assert client.patch(path, {"is_favorite": True, "is_muted": True}, format="json").status_code == 200
    assert client.get("/api/v1/chat/conversations/", {"workspace": "individual", "list_id": "bad"}).status_code == 400
    client.force_authenticate(superuser)
    assert client.get(path).status_code == 403
    client.force_authenticate(peer)
    assert client.get(path).json()["data"]["is_favorite"] is False


def test_owner_reopens_exact_visit_workspace(direct_chat, apartment_type, cairo_city, cairo_governorate):
    from datetime import time
    from core_apps.properties.models import PropertyVisit
    from core_apps.properties.tests.test_owner_visit_screens import create_property
    _, owner, tenant = direct_chat
    prop = create_property(owner, apartment_type, cairo_city, cairo_governorate)
    chats, visits = {}, {}
    for scope in ("individual", "student"):
        visits[scope] = PropertyVisit.objects.create(property=prop, tenant=tenant,
            visit_date=timezone.localdate(), visit_time=time(12 if scope == "individual" else 13), renter_workspace=scope)
        chats[scope] = get_or_create_direct_conversation(user=tenant, other_user=owner, workspace=scope, rental_context={"property_id": str(prop.id)})
    assert chats["student"] != chats["individual"]
    for scope in visits:
        reopened = get_or_create_direct_conversation(user=owner, other_user=tenant, workspace="owner",
            rental_context={"property_id": str(prop.id), "visit_id": str(visits[scope].id)})
        assert reopened == chats[scope]
        from rest_framework.test import APIClient
        client = APIClient()
        client.force_authenticate(owner)
        response = client.post("/api/v1/chat/conversations/create/", {
            "user_id": str(tenant.id), "workspace": "owner",
            "rental_context": {"property_id": str(prop.id), "visit_id": str(visits[scope].id)},
        }, format="json")
        assert response.status_code == 200, response.data
        assert response.json()["data"]["id"] == str(reopened.id)
