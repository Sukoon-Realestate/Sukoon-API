import pytest
from rest_framework.exceptions import ValidationError
from core_apps.chat.models import ConversationWorkspace
from core_apps.chat.services.workspace_inbox import scoped
from core_apps.chat.services.group_send import send_group_message
from core_apps.features.tests.test_rental_phase2 import authenticated
from .conftest import message_request

pytestmark = pytest.mark.django_db


def test_group_inbox_belongs_to_students_and_aggregate_badges_remain_available(chat_group):
    _, conversation, user, member = chat_group
    send_group_message(conversation, member, message_request("Workspace test"))
    # A stale client hint must not reclassify a group as personal/direct work.
    ConversationWorkspace.objects.create(
        conversation=conversation, user=user, workspace="individual"
    )
    assert not scoped(user, "individual").filter(pk=conversation.pk).exists()
    assert scoped(user, "student").filter(pk=conversation.pk).exists()
    with pytest.raises(ValidationError):
        scoped(user, "all")
    client = authenticated(user)
    counts = client.get("/api/v1/features/v1/workspace-summary/").data[
        "workspace_chat_counts"
    ]
    assert counts["student"] == counts["all"] == 1
    assert counts["individual"] == 0
    individual = client.get(
        "/api/v1/chat/conversations/", {"workspace": "individual", "page_size": 1}
    )
    assert individual.status_code == 200, individual.data
    assert individual.data["count"] == 0


def test_workspace_selection_never_restores_revoked_group_membership(chat_group):
    group, conversation, user, _ = chat_group
    group.memberships.filter(user=user).update(status="left")
    for space in ["student", "individual", "owner"]:
        assert not scoped(user, space).filter(pk=conversation.pk).exists()
    with pytest.raises(ValidationError):
        scoped(user, "all")
