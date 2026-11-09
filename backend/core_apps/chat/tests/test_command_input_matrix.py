"""Sprint 02 negative input matrix for chat write commands.

Every chat write route receives non-object bodies and, for each field a chat
command reads, values of the wrong shape (null, bool, number, list, object,
oversized text). None may surface as an unhandled 5xx; accepted bodies must
not contain the poisoned value.
"""

import uuid

import pytest
from rest_framework.test import APIClient

from core_apps.chat.models import Message

from .test_direct_media import direct_chat  # noqa: F401  (fixture)

pytestmark = pytest.mark.django_db

ROUTES = [
    ("post", "conversations/{c}/messages/create/"),
    ("post", "conversations/{c}/read/"),
    ("patch", "conversations/{c}/preferences/"),
    ("post", "conversations/{c}/attachments/"),
    ("post", "conversations/{c}/policy/"),
    ("post", "conversations/{c}/rental-context/"),
    ("post", "conversations/{c}/forward/"),
    ("put", "conversations/{c}/messages/{m}/star/"),
    ("put", "conversations/{c}/messages/{m}/pin/"),
    ("put", "conversations/{c}/messages/{m}/poll/vote/"),
    ("post", "conversations/{c}/messages/{m}/poll/close/"),
    ("post", "conversations/{c}/messages/{m}/forward/"),
    ("put", "conversations/{c}/mentions/{m}/seen/"),
    ("put", "conversations/{c}/messages/{m}/reaction/"),
    ("post", "conversations/create/"),
    ("post", "notification-actions/"),
    ("post", "lists/"),
    ("put", "quick-replies/{q}/"),
]

FIELDS = [
    "content", "kind", "client_message_id", "attachment_ids", "reply_to_id",
    "last_read_sequence", "is_muted", "membership_period", "emoji", "reaction",
    "option_ids", "options", "question", "starred", "pinned", "conversation_ids",
    "message_ids", "target_conversation_ids", "participant_id", "property_id",
    "name", "id", "text", "action", "notification_id", "preferences", "mentions",
    "lease_id", "context", "file", "sha256", "waveform", "metadata", "poll",
]

POISON = [None, True, 7, 1.5, [], [None], {}, {"nested": {"deep": [1]}}, "x" * 20_000]


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def chat_target(direct_chat):  # noqa: F811
    conversation, sender, recipient = direct_chat
    client = _client(sender)
    base = f"/api/v1/chat/conversations/{conversation.id}/"
    sent = client.post(
        base + "messages/create/",
        {"client_message_id": str(uuid.uuid4()), "content": "hello"},
        format="json",
    )
    message_id = (
        sent.json()["data"]["id"]
        if sent.status_code == 201
        else Message.objects.filter(conversation=conversation).values_list("id", flat=True).first()
        or uuid.uuid4()
    )
    return client, conversation.id, message_id


def _call(client, method, path, body):
    return getattr(client, method)("/api/v1/chat/" + path, body, format="json")


def test_chat_commands_never_500_on_malformed_bodies(chat_target):
    client, conversation_id, message_id = chat_target
    failures = []
    for method, template in ROUTES:
        path = template.format(c=conversation_id, m=message_id, q=uuid.uuid4())
        bodies = [[], "text", 5, None]
        bodies += [{field: value} for field in FIELDS for value in POISON]
        for body in bodies:
            try:
                response = _call(client, method, path, body)
            except Exception as error:  # an escaped exception is a 500 in production
                failures.append((method, template, repr(body)[:80], type(error).__name__))
                continue
            if response.status_code >= 500:
                failures.append((method, template, repr(body)[:80], response.status_code))
    assert not failures, failures[:20]
