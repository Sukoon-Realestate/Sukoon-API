"""Forwarding shares an explicit copy, never access to its source conversation."""
import uuid

import pytest

from core_apps.chat.models import Message
from core_apps.chat.services.forward_batch import forward_batch
from core_apps.chat.services.message_service import get_or_create_direct_conversation
from .test_direct_media import direct_chat  # noqa: F401
from .test_group_media_remote import durable  # noqa: F401
from .test_mvp_direct_tools import batch
from .test_rich_attachments import client_for, upload

pytestmark = pytest.mark.django_db


def test_forwarded_file_keeps_original_and_copy_conversation_access_separate(direct_chat, durable, superuser):
    source, owner, peer = direct_chat
    superuser.is_verified = True
    superuser.save(update_fields=['is_verified'])
    target = get_or_create_direct_conversation(user=peer, other_user=superuser)
    base = f'/api/v1/chat/conversations/{source.id}/'
    content = b'Synthetic private viewing notes; no identity or rental documents.'
    response = upload(client_for(owner), base, 'viewing-notes.txt', content)
    assert response.status_code == 201, response.data
    original = response.json()['data']
    sent = client_for(owner).post(base + 'messages/create/', {
        'client_message_id': str(uuid.uuid4()), 'kind': 'file',
        'content': 'Explicitly shared viewing notes', 'attachment_ids': [original['id']],
    }, format='json')
    assert sent.status_code == 201, sent.data
    message = Message.objects.get(id=sent.json()['data']['id'])
    command = batch(source, [target], peer, [message])
    result = forward_batch(source, peer, command)
    assert forward_batch(source, peer, command) == result
    forwarded = target.messages.get()
    clone = forwarded.attachments.get()
    assert str(clone.id) != original['id'] and clone.conversation_id == target.pk
    original_path = '/api/v1/' + original['content_path']
    copied_path = f'/api/v1/chat/conversations/{target.id}/attachments/{clone.id}/content/'
    # Recipient of the explicit copy acquires no access to source media/history.
    assert client_for(superuser).get(original_path).status_code == 403
    assert client_for(owner).get(copied_path).status_code == 403
    downloaded = client_for(superuser).get(copied_path)
    assert downloaded.status_code == 200
    assert downloaded['Cache-Control'] == 'private, no-store'
    assert b''.join(downloaded.streaming_content) == content
    assert target.messages.count() == 1 and forwarded.attachments.count() == 1
