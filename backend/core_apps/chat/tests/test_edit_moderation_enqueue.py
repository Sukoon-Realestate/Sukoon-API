"""A5-01 failing-before case: an edited message must reach moderation like a new one.

group_events.record_event enqueues only {'message.new', 'message.edit'} while edits emit
'message.edited', so the edited revision never gets a moderation input. Strict xfail:
the Sprint 01 fix must make this pass and remove the marker.
"""

from unittest.mock import patch

import pytest

from core_apps.chat.services.group_send import send_group_message
from core_apps.chat.services.message_mutations import mutate_message
from .conftest import message_request
from .test_direct_media import direct_chat  # noqa: F401
from .test_message_mutations import packet


@pytest.mark.django_db
@pytest.mark.xfail(strict=True, reason="A5-01: 'message.edited' is not in the moderation enqueue whitelist (Sprint 01)")
def test_edited_revision_is_enqueued_for_moderation(direct_chat):  # noqa: F811
    conversation, owner, _ = direct_chat
    with patch("core_apps.chat.moderation.queue.enqueue") as enqueue:
        message = send_group_message(conversation, owner, message_request("Harmless text"))
        assert enqueue.call_count == 1  # the new message is enqueued
        mutate_message(conversation, owner, packet(conversation, owner, message, content="Edited text"))

    assert enqueue.call_count == 2, "the edited revision was never offered to moderation"
    assert enqueue.call_args.args[0].pk == message.pk
