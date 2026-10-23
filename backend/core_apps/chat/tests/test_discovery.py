import uuid
import pytest
from rest_framework.test import APIClient
from core_apps.chat.models import Message
from core_apps.chat.services.search_index import normalize
from .test_direct_media import direct_chat

pytestmark = pytest.mark.django_db


def client(user):
    value = APIClient()
    value.force_authenticate(user)
    return value


def test_search_old_messages_arabic_cursor_and_tombstones(direct_chat):
    conversation, sender, reader = direct_chat
    rows = [
        Message.objects.create(
            conversation=conversation, sender=sender, content="إِيجار شقة قديمة"
        )
        for _ in range(25)
    ]
    api = client(reader)
    url = "/api/v1/chat/messages/search/"
    result = api.get(url, {"q": "ايجار شقه"})
    assert result.status_code == 200, result.content
    assert not result.json()["data"]["results"]  # no speculative ة/ه conflation
    result = api.get(url, {"q": "ايجار شقة"})
    assert result.status_code == 200, result.content
    data = result.json()["data"]
    assert len(data["results"]) == 20
    Message.objects.create(
        conversation=conversation, sender=sender, content="ايجار شقة جديدة"
    )
    next_page = api.get(url, {"q": "ايجار شقة", "cursor": data["next_cursor"]})
    assert len(next_page.json()["data"]["results"]) == 5
    assert (
        api.get(url, {"q": "مختلف", "cursor": data["next_cursor"]}).status_code == 400
    )
    from django.utils import timezone

    rows[0].deleted_at = timezone.now()
    rows[0].save(update_fields=["deleted_at"])
    assert str(rows[0].id) not in {
        x["message"]["id"]
        for x in api.get(url, {"q": "ايجار شقة", "cursor": data["next_cursor"]}).json()[
            "data"
        ]["results"]
    }


def test_library_and_conversation_query_respect_participation(direct_chat, superuser):
    conversation, sender, reader = direct_chat
    message = Message.objects.create(
        conversation=conversation,
        sender=sender,
        content="See https://example.com/house",
    )
    api = client(reader)
    response = api.get(
        f"/api/v1/chat/conversations/{conversation.id}/library/", {"kind": "link"}
    )
    assert response.status_code == 200, response.content
    assert response.json()["data"]["results"][0]["links"] == [
        "https://example.com/house"
    ]
    denied = client(superuser).get(
        f"/api/v1/chat/conversations/{conversation.id}/library/", {"kind": "link"}
    )
    assert denied.status_code == 404
    response = api.get(
        "/api/v1/chat/conversations/",
        {"q": sender.first_name or "nothing", "workspace": "all"},
    )
    assert response.status_code == 200, response.content


def test_conversation_search_does_not_match_own_name(direct_chat):
    conversation, sender, reader = direct_chat
    reader.first_name = "OnlyViewerName"
    reader.save(update_fields=["first_name"])
    sender.first_name = "OnlyCounterpartyName"
    sender.save(update_fields=["first_name"])
    api = client(reader)
    own = api.get("/api/v1/chat/conversations/", {"q": "OnlyViewerName"})
    assert own.status_code == 200, own.content
    assert not own.json()["data"]
    other = api.get("/api/v1/chat/conversations/", {"q": "OnlyCounterpartyName"})
    assert other.status_code == 200, other.content
    assert str(conversation.id) in {row["id"] for row in other.json()["data"]}


def test_search_cursor_and_index_cannot_reuse_other_users_or_previous_text(direct_chat):
    conversation, sender, reader = direct_chat
    rows = [
        Message.objects.create(
            conversation=conversation, sender=sender, content="original searchable"
        )
        for _ in range(21)
    ]
    url = "/api/v1/chat/messages/search/"
    cursor = client(reader).get(url, {"q": "original"}).json()["data"]["next_cursor"]
    assert (
        client(sender).get(url, {"q": "original", "cursor": cursor}).status_code == 400
    )
    item = rows[-1]
    item.content, item.revision = "replacement searchable", item.revision + 1
    item.save(update_fields=["content", "revision"])
    found = client(reader).get(url, {"q": "replacement"}).json()["data"]["results"]
    assert [row["message"]["id"] for row in found] == [str(item.id)]
    assert client(reader).get(url, {"q": "ًَ"}).status_code == 400
    assert (
        client(reader)
        .get(url, {"q": "original", "conversation_id": "invalid"})
        .status_code
        == 400
    )


def test_backfill_indexes_legacy_rows_without_changing_messages(direct_chat):
    import io
    from django.core.management import call_command
    from core_apps.chat.models import ChatSearchDocument

    conversation, sender, _ = direct_chat
    rows = Message.objects.bulk_create(
        [
            Message(conversation=conversation, sender=sender, content="إِيجار قديم"),
            Message(
                conversation=conversation, sender=sender, content="Older rental message"
            ),
        ]
    )
    ids = [row.pk for row in rows]
    before = list(Message.objects.filter(pk__in=ids).order_by("pk").values())
    assert not ChatSearchDocument.objects.filter(message_id__in=ids).exists()
    for _ in range(2):
        call_command("backfill_chat_search", batch_size=1, stdout=io.StringIO())
    assert ChatSearchDocument.objects.filter(message_id__in=ids).count() == 2
    assert ChatSearchDocument.objects.get(message=rows[0]).body == normalize(
        rows[0].content
    )
    assert list(Message.objects.filter(pk__in=ids).order_by("pk").values()) == before
