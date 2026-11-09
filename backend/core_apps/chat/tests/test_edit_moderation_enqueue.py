"""A5-01: every committed reviewable revision, including edits, reaches moderation once.

Sprint 00 recorded this as a strict xfail: record_event enqueued {'message.new',
'message.edit'} while edits emit 'message.edited'. Sprint 01 centralizes the moderated
event kinds (group_events.MODERATED_MESSAGE_EVENTS).
"""

from unittest.mock import patch

import pytest

from core_apps.chat.models import ChatModerationInput
from core_apps.chat.moderation.queue import enqueue
from core_apps.chat.services.group_events import MODERATED_MESSAGE_EVENTS
from core_apps.chat.services.group_send import send_group_message
from core_apps.chat.services.message_mutations import mutate_message
from .conftest import message_request
from .test_direct_media import direct_chat  # noqa: F401
from .test_message_mutations import packet
from .test_rental_moderation import rental_chat  # noqa: F401


@pytest.mark.django_db
def test_edited_revision_is_enqueued_for_moderation(direct_chat):  # noqa: F811
    conversation, owner, _ = direct_chat
    with patch("core_apps.chat.moderation.queue.enqueue") as mocked:
        message = send_group_message(conversation, owner, message_request("Harmless text"))
        assert mocked.call_count == 1  # the new message is enqueued
        mutate_message(conversation, owner, packet(conversation, owner, message, content="Edited text"))

    assert mocked.call_count == 2, "the edited revision was never offered to moderation"
    assert mocked.call_args.args[0].pk == message.pk


def test_moderated_kinds_are_event_names_not_command_names():
    assert MODERATED_MESSAGE_EVENTS == {"message.new", "message.edited"}


@pytest.mark.django_db
def test_one_input_per_revision_and_retry_does_not_duplicate(rental_chat):  # noqa: F811
    conversation, owner, _ = rental_chat
    message = send_group_message(conversation, owner, message_request("Harmless text"))
    message.refresh_from_db()
    mutate_message(conversation, owner, packet(conversation, owner, message, content="Edited once"))
    message.refresh_from_db()
    mutate_message(conversation, owner, packet(conversation, owner, message, content="Edited twice"))
    message.refresh_from_db()

    revisions = sorted(ChatModerationInput.objects.filter(message=message).values_list("revision", flat=True))
    assert revisions == [1, 2, 3]
    enqueue(message)  # a retried enqueue of the same revision
    assert ChatModerationInput.objects.filter(message=message).count() == 3


@pytest.mark.django_db
def test_deleted_message_is_never_enqueued(rental_chat):  # noqa: F811
    from django.utils import timezone

    conversation, owner, _ = rental_chat
    message = send_group_message(conversation, owner, message_request("Harmless text"))
    message.deleted_at = timezone.now()
    message.revision += 1
    message.save(update_fields=["deleted_at", "revision"])
    enqueue(message)
    assert not ChatModerationInput.objects.filter(message=message, revision=message.revision).exists()
