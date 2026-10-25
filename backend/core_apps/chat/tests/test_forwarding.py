import uuid
from concurrent.futures import ThreadPoolExecutor
import pytest
from django.db import close_old_connections
from rest_framework.exceptions import APIException
from rest_framework.test import APIClient
from core_apps.chat.models import ChatAttachment, Message
from core_apps.chat.services.forwarding import forward_message
from core_apps.chat.services.group_access import authorize
from core_apps.chat.services.group_send import send_group_message
from core_apps.chat.services.group_projection import message_payload
from core_apps.chat.services.group_operations import delete_group_message
from core_apps.chat.services.group_media_storage import private_path, remove_files
from core_apps.chat.services.group_provisioning import provision_group
from core_apps.features.planning_models import HousingGroup, GroupMembership
from .conftest import message_request


def target_group(owner, peer):
    group = HousingGroup.objects.create(name="Forward destination", capacity=4)
    GroupMembership.objects.create(group=group, user=owner, role="admin")
    GroupMembership.objects.create(group=group, user=peer)
    return provision_group(group)


def forward_body(source, target, user, message):
    _, origin, _ = authorize(source, user)
    _, destination, _ = authorize(target, user)
    return {
        "client_message_id": str(uuid.uuid4()),
        "destination_id": str(target.id),
        "source_membership_period": str(origin.membership_period),
        "destination_membership_period": str(destination.membership_period),
        "expected_revision": message.revision,
    }


@pytest.mark.django_db
def test_forward_uses_server_snapshot_and_replays_once(chat_group):
    _, source, owner, peer = chat_group
    target = target_group(owner, peer)
    message = send_group_message(source, owner, message_request("original 😀"))
    body = forward_body(source, target, peer, message)
    forwarded = forward_message(source, peer, message.id, {**body, "content": "forged", "sender_id": str(owner.id)})
    assert forwarded.content == "original 😀" and forwarded.sender == peer and forwarded.is_forwarded
    assert forwarded.conversation == target and forwarded.id != message.id
    _, participant, member = authorize(target, owner)
    projection = message_payload(forwarded, participant, member)
    assert projection["is_forwarded"] and "forward" in projection["allowed_actions"]
    assert "source_message_id" not in projection and "source_conversation_id" not in projection
    delete_group_message(source, owner, message.id)
    assert forward_message(source, peer, message.id, body).pk == forwarded.pk
    assert target.messages.exclude(kind="system").count() == 1
    with pytest.raises(APIException):
        forward_message(source, peer, message.id, {**body, "expected_revision": 2})


@pytest.mark.django_db
def test_forward_drops_original_mentions_replies_and_reactions(chat_group):
    _, source, owner, peer = chat_group
    target = target_group(owner, peer)
    previous = send_group_message(source, owner, message_request("reply context"))
    message = send_group_message(
        source,
        owner,
        message_request("@all", mentions=[{"kind": "all", "start": 0, "end": 4}], reply_to_message_id=str(previous.id)),
    )
    copy = forward_message(source, peer, message.id, forward_body(source, target, peer, message))
    assert copy.content == "@all" and copy.is_forwarded
    assert copy.mentions == [] and copy.reply_to_id is None
    assert not copy.mention_receipts.exists() and not copy.reactions.exists()
    again = forward_message(target, owner, copy.id, forward_body(target, source, owner, copy))
    assert again.is_forwarded and again.content == "@all"


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["image", "voice", "file", "video"])
def test_forwarded_media_has_its_own_access_and_survives_original_deletion(chat_group, kind):
    _, source, owner, peer = chat_group
    target = target_group(owner, peer)
    _, participant, _ = authorize(source, owner)
    key = uuid.uuid4().hex + ".bin"
    private_path(key).write_bytes(b"private attachment bytes")
    original = ChatAttachment.objects.create(
        conversation=source,
        uploader=owner,
        membership_period=participant.membership_period,
        client_upload_id=uuid.uuid4(),
        kind=kind,
        state="ready",
        fingerprint="a" * 64,
        storage_key=key,
        mime_type="application/pdf",
        byte_size=24,
        original_name="file.pdf",
        duration_ms=1200 if kind in {"voice", "video"} else None,
    )
    message = send_group_message(
        source,
        owner,
        message_request("" if kind == "voice" else "caption", kind=kind, attachment_ids=[str(original.id)]),
    )
    copy = forward_message(source, peer, message.id, forward_body(source, target, peer, message))
    attachment = copy.attachments.get()
    assert attachment.id != original.id and attachment.conversation == target and attachment.uploader == peer
    assert attachment.duration_ms == original.duration_ms and attachment.original_name == original.original_name
    delete_group_message(source, owner, message.id)
    original.refresh_from_db()
    remove_files(original)
    assert private_path(key).read_bytes() == b"private attachment bytes"
    client = APIClient()
    client.force_authenticate(peer)
    assert client.get(f"/api/v1/chat/conversations/{source.id}/attachments/{attachment.id}/content/").status_code == 404
    response = client.get(f"/api/v1/chat/conversations/{target.id}/attachments/{attachment.id}/content/")
    assert response.status_code == 200 and b"".join(response.streaming_content) == b"private attachment bytes"
    delete_group_message(target, peer, copy.id)
    attachment.refresh_from_db()
    remove_files(attachment)
    assert not private_path(key).exists()


@pytest.mark.django_db
def test_destination_search_pagination_and_removed_access(chat_group, superuser):
    group, source, owner, peer = chat_group
    target = target_group(owner, peer)
    message = send_group_message(source, owner, message_request())
    endpoint = f"/api/v1/chat/conversations/{source.id}/messages/{message.id}"
    client = APIClient()
    client.force_authenticate(peer)
    response = client.get(endpoint + "/forward-destinations/", {"q": "destination"})
    assert response.status_code == 200
    rows = response.data["results"]
    assert [r["id"] for r in rows] == [str(target.id)] and "membership_period" in rows[0]
    assert client.get(endpoint + "/forward-destinations/", {"q": "no match"}).data["results"] == []
    client.force_authenticate(superuser)
    assert client.get(endpoint + "/forward-destinations/").status_code == 403
    client.force_authenticate(peer)
    body = forward_body(source, target, peer, message)
    target.housing_group.memberships.filter(user=peer).update(status="removed")
    assert client.post(endpoint + "/forward/", body, format="json").status_code == 403
    assert client.get(endpoint + "/forward-destinations/").data["results"] == []
    group.memberships.filter(user=peer).update(status="removed")
    assert client.get(endpoint + "/forward-destinations/").status_code == 403
    assert not Message.objects.filter(client_message_id=body["client_message_id"]).exists()


@pytest.mark.django_db
def test_stale_revision_membership_and_system_messages_are_rejected(chat_group):
    _, source, owner, peer = chat_group
    target = target_group(owner, peer)
    message = send_group_message(source, owner, message_request())
    body = forward_body(source, target, peer, message)
    for changes in [
        {"expected_revision": 99},
        {"source_membership_period": str(uuid.uuid4())},
        {"destination_membership_period": str(uuid.uuid4())},
    ]:
        with pytest.raises(APIException):
            forward_message(source, peer, message.id, {**body, **changes})
    message.kind = "system"
    message.save(update_fields=["kind"])
    with pytest.raises(APIException):
        forward_message(source, peer, message.id, body)
    assert not target.messages.exclude(kind="system").exists()


@pytest.mark.django_db
def test_location_forward_and_direct_destination(chat_group):
    from core_apps.chat.services.message_service import get_or_create_direct_conversation

    _, source, owner, peer = chat_group
    target = get_or_create_direct_conversation(user=owner, other_user=peer)
    message = send_group_message(
        source, owner, message_request("meet here", kind="location", location={"latitude": 30.1, "longitude": 31.2})
    )
    copy = forward_message(source, peer, message.id, forward_body(source, target, peer, message))
    assert copy.location == message.location and copy.is_forwarded
    assert forward_message(target, owner, copy.id, forward_body(target, source, owner, copy)).is_forwarded


@pytest.mark.django_db(transaction=True)
def test_opposite_forwards_and_duplicate_retries_do_not_deadlock(chat_group):
    _, source, owner, peer = chat_group
    target = target_group(owner, peer)
    first = send_group_message(source, owner, message_request("A"))
    second = send_group_message(target, peer, message_request("B"))
    a = forward_body(source, target, peer, first)
    b = forward_body(target, source, owner, second)

    def run(args):
        close_old_connections()
        try:
            return str(forward_message(*args).id)
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=3) as pool:
        calls = [
            pool.submit(run, values)
            for values in [(source, peer, first.id, a), (target, owner, second.id, b), (source, peer, first.id, a)]
        ]
        ids = [call.result(timeout=20) for call in calls]
    assert ids[0] == ids[2] and ids[0] != ids[1]


@pytest.mark.django_db
def test_blocked_direct_chat_is_not_a_forward_destination(chat_group):
    from core_apps.chat.models import ChatBlock
    from core_apps.chat.services.message_service import get_or_create_direct_conversation

    _, source, owner, peer = chat_group
    target = get_or_create_direct_conversation(user=owner, other_user=peer)
    message = send_group_message(source, owner, message_request())
    body = forward_body(source, target, peer, message)
    ChatBlock.objects.create(user=owner, blocked_user=peer)
    from core_apps.chat.services.forwarding import destinations

    assert destinations(source, peer, message.id, {}) == []
    with pytest.raises(APIException):
        forward_message(source, peer, message.id, body)
    assert not target.messages.exists()


@pytest.mark.django_db
def test_destination_pagination_counts_authorized_rows_before_slicing(chat_group):
    _, source, owner, peer = chat_group
    targets = [target_group(owner, peer) for _ in range(21)]
    hidden = target_group(owner, peer)
    hidden.housing_group.memberships.filter(user=peer).update(status="removed")
    message = send_group_message(source, owner, message_request())
    client = APIClient()
    client.force_authenticate(peer)
    endpoint = f"/api/v1/chat/conversations/{source.id}/messages/{message.id}/forward-destinations/"
    first = client.get(endpoint).data
    second = client.get(endpoint, {"page": 2}).data
    assert first["count"] == second["count"] == 21
    assert len(first["results"]) == 20 and len(second["results"]) == 1
    assert {r["id"] for r in first["results"] + second["results"]} == {str(c.id) for c in targets}


@pytest.mark.django_db
def test_migration_keeps_old_instance_message_inserts_working(chat_group):
    from django.db import connection

    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL rolling deployment contract")
    _, source, owner, _ = chat_group
    message = send_group_message(source, owner, message_request("legacy insert"))
    identity = uuid.uuid4()
    columns = [f.column for f in Message._meta.local_concrete_fields if f.column not in {"pkid", "is_forwarded"}]
    quoted = [connection.ops.quote_name(c) for c in columns]
    values = [
        "CAST(%s AS uuid)" if c == "id" else "NULL" if c in {"sequence", "client_message_id"} else q
        for c, q in zip(columns, quoted)
    ]
    with connection.cursor() as cursor:
        cursor.execute(
            f'INSERT INTO "chat_message" ({", ".join(quoted)}) SELECT {", ".join(values)} FROM "chat_message" WHERE pkid = %s',
            [str(identity), message.pk],
        )
    assert Message.objects.get(id=identity).is_forwarded is False
