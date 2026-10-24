"""One-time data classification keeps history usable in the normal inbox."""
from importlib import import_module
from types import SimpleNamespace
from datetime import time
import uuid

import pytest
from django.apps import apps
from django.db import connection
from django.utils import timezone

from core_apps.chat.models import (
    Conversation, ConversationParticipant, ConversationWorkspace,
    RentalChatContext, ChatList, Message,
)
from core_apps.chat.services.conversation_preferences import preferences_payload
from core_apps.chat.services.message_service import get_or_create_direct_conversation
from core_apps.chat.services.group_access import authorize, visible_messages
from core_apps.chat.services.group_send import send_group_message
from core_apps.chat.services.workspace_inbox import scoped
from core_apps.properties.models import PropertyVisit
from core_apps.properties.tests.conftest import apartment_type, cairo_city, cairo_governorate  # noqa: F401
from core_apps.properties.tests.test_owner_visit_screens import create_property
from .conftest import message_request

pytestmark = pytest.mark.django_db


def migrate_chats():
    migration = import_module("core_apps.chat.migrations.0019_classify_existing_direct_chats")
    migration.classify_existing_chats(apps, SimpleNamespace(connection=connection))


def existing_chat(*people):
    chat = Conversation.objects.create(workspace_archived=True)
    for person in people:
        person.is_verified = True
        person.save(update_fields=["is_verified"])
        ConversationParticipant.objects.create(
            conversation=chat, user=person, membership_period=uuid.uuid4(),
        )
    return chat


@pytest.mark.parametrize("evidence", ["rental_context", "visit"])
def test_existing_rental_chat_uses_its_owner_and_keeps_private_history(
    user, another_user, apartment_type, cairo_city, cairo_governorate, evidence,
):
    owner, tenant = user, another_user
    prop = create_property(owner, apartment_type, cairo_city, cairo_governorate)
    # Owning another property must not turn the renter into this chat's owner.
    create_property(tenant, apartment_type, cairo_city, cairo_governorate)
    chat = existing_chat(owner, tenant)
    if evidence == "rental_context":
        RentalChatContext.objects.create(conversation=chat, owner=owner).properties.add(prop)
    else:
        PropertyVisit.objects.create(property=prop, tenant=tenant,
            visit_date=timezone.localdate(), visit_time=time(12), renter_workspace="student")
    original = Message.objects.create(conversation=chat, sender=owner, content="Original", sequence=1)
    latest = Message.objects.create(conversation=chat, sender=tenant, content="Reply", sequence=2, reply_to=original)
    chat.last_sequence = 2
    chat.save(update_fields=["last_sequence"])
    chat.participant_set.filter(user=tenant).update(
        hidden_through_sequence=1, visible_from_sequence=2,
        last_read_sequence=1, is_muted=True, is_favorite=True,
    )
    migrate_chats()
    chat.refresh_from_db()
    assert chat.workspace_archived is False
    assert list(scoped(owner, "owner")) == [chat]
    assert list(scoped(tenant, "individual")) == [chat]
    assert not scoped(owner, "individual").exists()
    assert not scoped(tenant, "owner").exists()
    _, participant, _ = authorize(chat, tenant)
    assert list(visible_messages(chat, participant)) == [latest]
    assert participant.is_muted and participant.is_favorite
    assert participant.last_read_sequence == 1
    latest.refresh_from_db()
    original.refresh_from_db()
    assert latest.reply_to_id == original.pk and original.content == "Original"
    assert get_or_create_direct_conversation(user=tenant, other_user=owner,
        workspace="individual", rental_context={"property_id": str(prop.id)}) == chat


def test_duplicates_remain_usable_and_current_workspaces_stay_separate(user, another_user):
    old = [existing_chat(user, another_user) for _ in range(2)]
    current = get_or_create_direct_conversation(user=user, other_user=another_user, workspace="individual")
    student = get_or_create_direct_conversation(user=user, other_user=another_user, workspace="student")
    for chat in old:
        Message.objects.create(conversation=chat, sender=user, content="Keep this history", sequence=1)
        ConversationWorkspace.objects.create(conversation=chat, user=user, workspace="student")
    saved = ChatList.objects.create(user=user, workspace="student", name="Visits")
    saved.conversations.add(old[0], student)
    migrate_chats()
    migrate_chats()  # Restart/replay must not duplicate or discard history.
    assert set(scoped(user, "individual")) == {*old, current}
    assert list(scoped(user, "student")) == [student]
    assert get_or_create_direct_conversation(user=user, other_user=another_user, workspace="individual") == current
    assert Message.objects.filter(conversation__in=old, content="Keep this history").count() == 2
    assert list(saved.conversations.all()) == [student]
    assert list(ChatList.objects.get(user=user, workspace="individual", name="Visits").conversations.all()) == [old[0]]
    for chat in old:
        assert "is_legacy" not in preferences_payload(chat, user)
        assert "is_archived" not in preferences_payload(chat, user)
        assert send_group_message(chat, user, message_request()).id


def test_unassigned_history_without_rental_evidence_defaults_to_individuals(user, another_user):
    chat = existing_chat(user, another_user)
    migrate_chats()
    assert list(scoped(user, "individual")) == [chat]
    assert list(scoped(another_user, "individual")) == [chat]
    assert get_or_create_direct_conversation(user=user, other_user=another_user) == chat
