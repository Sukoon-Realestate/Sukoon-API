import uuid
from datetime import timedelta
import pytest
from django.utils import timezone
from rest_framework.exceptions import APIException
from rest_framework.test import APIClient
from core_apps.chat.models import MessageStar, MessagePin, ChatEvent, MessageReadReceipt
from core_apps.chat.services.group_access import authorize
from core_apps.chat.services.group_projection import message_payload, summary
from core_apps.chat.services.group_send import send_group_message
from core_apps.chat.services.group_events import event_payload
from core_apps.chat.services.group_operations import mark_group_read, delete_group_message
from core_apps.chat.services.message_tools import set_message_tool, message_readers, reader_payload
from core_apps.chat.services.polls import change_poll
from core_apps.chat.services.forward_batch import forward_batch
from core_apps.chat.services.forwarding import forward_message
from core_apps.chat.services.quick_replies import save, listing
from core_apps.chat.services.message_service import get_or_create_direct_conversation
from .conftest import message_request
from .test_forwarding import target_group, forward_body


def command(conversation, user, **extra):
    _, p, _ = authorize(conversation, user)
    return {"membership_period": str(p.membership_period), "operation_id": str(uuid.uuid4()), **extra}


def project(conversation, user, message):
    _, p, m = authorize(conversation, user)
    return message_payload(message, p, m)


@pytest.mark.django_db
def test_stars_are_private_and_retries_do_not_toggle_newer_choice(chat_group):
    _, conversation, owner, peer = chat_group
    message = send_group_message(conversation, owner, message_request())
    first = command(conversation, peer, enabled=True)
    assert set_message_tool(conversation, peer, message.id, first)["is_starred"]
    event = ChatEvent.objects.filter(kind="message.star").get()
    assert event_payload(event, owner) is None
    assert event_payload(event, peer)["payload"]["is_starred"]
    assert not project(conversation, owner, message)["is_starred"]
    set_message_tool(conversation, peer, message.id, command(conversation, peer, enabled=False))
    assert not set_message_tool(conversation, peer, message.id, first)["is_starred"]
    assert MessageStar.objects.get().revision == 2
    with pytest.raises(APIException):
        set_message_tool(conversation, peer, message.id, {**first, "enabled": False})


@pytest.mark.django_db
def test_starred_endpoint_hides_deleted_and_previous_membership(chat_group):
    group, conversation, owner, peer = chat_group
    messages = [send_group_message(conversation, owner, message_request(str(i))) for i in range(2)]
    for m in messages:
        set_message_tool(conversation, peer, m.id, command(conversation, peer, enabled=True))
    client = APIClient()
    client.force_authenticate(peer)
    path = f"/api/v1/chat/conversations/{conversation.id}/starred/"
    assert client.get(path).data["count"] == 2
    delete_group_message(conversation, owner, messages[0].id)
    assert client.get(path).data["count"] == 1
    conversation.participant_set.filter(user=peer).update(membership_period=uuid.uuid4())
    assert client.get(path).data["count"] == 0
    group.memberships.filter(user=peer).update(status="removed")
    assert client.get(path).status_code == 403


@pytest.mark.django_db
def test_pins_permissions_expiration_limit_and_visibility(chat_group):
    _, conversation, owner, peer = chat_group
    messages = [send_group_message(conversation, owner, message_request(str(i))) for i in range(4)]
    with pytest.raises(APIException):
        set_message_tool(conversation, peer, messages[0].id, command(conversation, peer, enabled=True), pin=True)
    for m in messages[:3]:
        set_message_tool(conversation, owner, m.id, command(conversation, owner, enabled=True), pin=True)
    assert len(summary(conversation, peer)["pinned_messages"]) == 3
    with pytest.raises(APIException):
        set_message_tool(conversation, owner, messages[3].id, command(conversation, owner, enabled=True), pin=True)
    MessagePin.objects.filter(message=messages[0]).update(expires_at=timezone.now() - timedelta(seconds=1))
    assert len(summary(conversation, peer)["pinned_messages"]) == 2
    set_message_tool(conversation, owner, messages[3].id, command(conversation, owner, enabled=True), pin=True)
    conversation.participant_set.filter(user=peer).update(visible_from_sequence=messages[3].sequence)
    assert [p["message"]["id"] for p in summary(conversation, peer)["pinned_messages"]] == [str(messages[3].id)]
    delete_group_message(conversation, owner, messages[3].id)
    assert summary(conversation, peer)["pinned_messages"] == []


@pytest.mark.django_db
def test_both_direct_participants_can_pin_but_blocked_send_cannot(chat_group):
    _, _, owner, peer = chat_group
    conversation = get_or_create_direct_conversation(user=owner, other_user=peer)
    message = send_group_message(conversation, owner, message_request())
    assert set_message_tool(conversation, peer, message.id, command(conversation, peer, enabled=True), pin=True)[
        "pinned_messages"
    ]
    from core_apps.chat.models import ChatBlock

    ChatBlock.objects.create(user=owner, blocked_user=peer)
    with pytest.raises(APIException):
        set_message_tool(conversation, peer, message.id, command(conversation, peer, enabled=False), pin=True)


@pytest.mark.django_db
def test_exact_first_read_time_and_legacy_unknown_time(chat_group):
    _, conversation, owner, peer = chat_group
    first = send_group_message(conversation, owner, message_request("first"))
    second = send_group_message(conversation, owner, message_request("second"))
    mark_group_read(conversation, peer, first.sequence)
    at = MessageReadReceipt.objects.get(message=first).read_at
    mark_group_read(conversation, peer, second.sequence)
    assert MessageReadReceipt.objects.get(message=first).read_at == at
    message, readers = message_readers(conversation, owner, first.id)
    assert reader_payload(message, readers.get())["read_at"] == at.isoformat()
    MessageReadReceipt.objects.filter(message=first).delete()
    row = reader_payload(message, readers.get())
    assert row["is_read"] and row["read_at"] is None
    with pytest.raises(APIException):
        message_readers(conversation, peer, first.id)
    assert "message_info" in project(conversation, owner, first)["allowed_actions"]
    assert "message_info" not in project(conversation, peer, first)["allowed_actions"]


def poll_message(conversation, owner, multiple=False):
    return send_group_message(
        conversation,
        owner,
        message_request(
            "",
            kind="poll",
            poll={"question": "اختيار المجموعة", "options": ["الأول", "الثاني"], "allow_multiple": multiple},
        ),
    )


@pytest.mark.django_db
def test_poll_send_vote_retry_close_and_private_membership(chat_group):
    group, conversation, owner, peer = chat_group
    poll = poll_message(conversation, owner)
    assert poll.content == "اختيار المجموعة"
    options = project(conversation, peer, poll)["poll"]["options"]
    first = command(conversation, peer, option_ids=[options[0]["id"]])
    assert change_poll(conversation, peer, poll.id, first)["poll"]["options"][0]["votes"] == 1
    change_poll(conversation, peer, poll.id, command(conversation, peer, option_ids=[options[1]["id"]]))
    replay = change_poll(conversation, peer, poll.id, first)
    assert replay["poll"]["options"][1]["is_mine"] and replay["poll"]["options"][0]["votes"] == 0
    assert not project(conversation, owner, poll)["poll"]["options"][1]["is_mine"]
    with pytest.raises(APIException):
        change_poll(conversation, peer, poll.id, command(conversation, peer), close=True)
    with pytest.raises(APIException):
        change_poll(conversation, peer, poll.id, command(conversation, peer, option_ids=[o["id"] for o in options]))
    with pytest.raises(APIException):
        change_poll(conversation, peer, poll.id, command(conversation, peer, option_ids=[str(uuid.uuid4())]))
    group.memberships.filter(user=peer).update(status="removed")
    assert project(conversation, owner, poll)["poll"]["voter_count"] == 0
    assert change_poll(conversation, owner, poll.id, command(conversation, owner), close=True)["poll"]["is_closed"]
    with pytest.raises(APIException):
        change_poll(conversation, owner, poll.id, command(conversation, owner, option_ids=[options[0]["id"]]))


@pytest.mark.django_db
def test_poll_validation_direct_restriction_and_forwarding(chat_group):
    _, conversation, owner, peer = chat_group
    with pytest.raises(APIException):
        send_group_message(
            conversation, owner, message_request("", kind="poll", poll={"question": "q", "options": ["Same", "same"]})
        )
    direct = get_or_create_direct_conversation(user=owner, other_user=peer)
    with pytest.raises(APIException):
        poll_message(direct, owner)
    message = poll_message(conversation, owner, True)
    assert "forward" not in project(conversation, peer, message)["allowed_actions"]
    with pytest.raises(APIException):
        forward_message(conversation, peer, message.id, forward_body(conversation, direct, peer, message))
    ids = [o["id"] for o in message.poll.options]
    voted = change_poll(conversation, peer, message.id, command(conversation, peer, option_ids=ids))
    assert voted["poll"]["voter_count"] == 1 and all(o["votes"] == 1 for o in voted["poll"]["options"])


def batch_body(source, targets, user, messages):
    return {
        "operation_id": str(uuid.uuid4()),
        "source_membership_period": str(authorize(source, user)[1].membership_period),
        "messages": [{"id": str(m.id), "expected_revision": m.revision} for m in messages],
        "destinations": [
            {"id": str(t.id), "membership_period": str(authorize(t, user)[1].membership_period)} for t in targets
        ],
    }


@pytest.mark.django_db
def test_batch_is_ordered_atomic_and_replayed_once(chat_group):
    _, source, owner, peer = chat_group
    targets = [target_group(owner, peer), get_or_create_direct_conversation(user=owner, other_user=peer)]
    messages = [send_group_message(source, owner, message_request(str(i))) for i in range(3)]
    body = batch_body(source, targets, peer, list(reversed(messages)))
    response = forward_batch(source, peer, body)
    for target in targets:
        assert list(target.messages.exclude(kind="system").order_by("sequence").values_list("content", flat=True)) == [
            "0",
            "1",
            "2",
        ]
    delete_group_message(source, owner, messages[0].id)
    assert forward_batch(source, peer, body) == response
    assert all(t.messages.exclude(kind="system").count() == 3 for t in targets)
    with pytest.raises(APIException):
        forward_batch(source, peer, {**body, "messages": body["messages"][:1]})


@pytest.mark.django_db
def test_batch_does_not_partially_forward_when_one_message_is_stale(chat_group):
    _, source, owner, peer = chat_group
    target = target_group(owner, peer)
    messages = [send_group_message(source, owner, message_request(str(i))) for i in range(2)]
    body = batch_body(source, [target], peer, messages)
    body["messages"][1]["expected_revision"] = 999
    with pytest.raises(APIException):
        forward_batch(source, peer, body)
    assert not target.messages.exclude(kind="system").exists()
    body = batch_body(source, [target], peer, messages)
    target.housing_group.memberships.filter(user=peer).update(status="removed")
    with pytest.raises(APIException):
        forward_batch(source, peer, body)
    assert not target.messages.exclude(kind="system").exists()


@pytest.mark.django_db
def test_quick_replies_owner_isolation_conflicts_and_tombstones(chat_group):
    _, _, owner, peer = chat_group
    identity = uuid.uuid4()
    body = {"title": "Availability", "content": "Let me check", "expected_revision": 0}
    first = save(owner, identity, body)
    assert save(owner, identity, body) == first
    assert listing(peer) == []
    with pytest.raises(APIException):
        save(peer, identity, body)
    second = save(owner, identity, {**body, "content": "Updated", "expected_revision": 1})
    assert second["revision"] == 2
    with pytest.raises(APIException):
        save(owner, identity, {**body, "content": "Stale", "expected_revision": 1})
    save(owner, identity)
    assert listing(owner) == []
    with pytest.raises(APIException):
        save(owner, identity, body)


@pytest.mark.django_db(transaction=True)
def test_batch_opposite_directions_duplicate_and_normal_send_do_not_deadlock(chat_group):
    from concurrent.futures import ThreadPoolExecutor
    from django.db import close_old_connections, connection

    _, source, owner, peer = chat_group
    target = target_group(owner, peer)
    direct = get_or_create_direct_conversation(user=owner, other_user=peer)
    first = send_group_message(source, owner, message_request("A"))
    second = send_group_message(target, peer, message_request("B"))
    a = batch_body(source, [target, direct], peer, [first])
    b = batch_body(target, [source, direct], owner, [second])

    def run(fn, *args):
        close_old_connections()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET lock_timeout = '8s'")
            return fn(*args)
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=4) as pool:
        calls = [
            pool.submit(run, forward_batch, source, peer, a),
            pool.submit(run, forward_batch, target, owner, b),
            pool.submit(run, forward_batch, source, peer, a),
            pool.submit(run, send_group_message, target, owner, message_request("ordinary")),
        ]
        values = [c.result(timeout=20) for c in calls]
    assert values[0] == values[2]
    assert direct.messages.filter(is_forwarded=True).count() == 2
    assert target.messages.filter(content="ordinary").count() == 1


@pytest.mark.django_db
def test_http_tools_require_auth_and_keep_private_responses(chat_group):
    _, conversation, owner, peer = chat_group
    message = send_group_message(conversation, owner, message_request("details"))
    root = f"/api/v1/chat/conversations/{conversation.id}"
    client = APIClient()
    assert client.get(f"{root}/starred/").status_code == 401
    client.force_authenticate(peer)
    response = client.put(
        f"{root}/messages/{message.id}/star/", command(conversation, peer, enabled=True), format="json"
    )
    assert response.status_code == 200 and response.data["is_starred"]
    assert response["Cache-Control"] == "private, no-store"
    assert client.get(f"{root}/messages/{message.id}/readers/").status_code == 403
    client.force_authenticate(owner)
    assert client.get(f"{root}/messages/{message.id}/readers/").data["count"] == 1
    poll = send_group_message(
        conversation, owner, message_request(kind="poll", poll={"question": "When?", "options": ["Today", "Tomorrow"]})
    )
    vote = client.put(
        f"{root}/messages/{poll.id}/poll/vote/",
        command(conversation, owner, option_ids=[poll.poll.options[0]["id"]]),
        format="json",
    )
    assert vote.status_code == 200 and vote.data["poll"]["voter_count"] == 1
    assert client.post(f"{root}/messages/{poll.id}/poll/close/", command(conversation, owner), format="json").data[
        "poll"
    ]["is_closed"]
    identity = uuid.uuid4()
    url = f"/api/v1/chat/quick-replies/{identity}/"
    assert (
        client.put(url, {"title": "Hello", "content": "Hello there", "expected_revision": 0}, format="json").status_code
        == 200
    )
    assert client.get("/api/v1/chat/quick-replies/").data["replies"][0]["id"] == str(identity)
    assert client.delete(url).status_code == 200
    assert client.get("/api/v1/chat/quick-replies/").data["replies"] == []


@pytest.mark.django_db
def test_delete_before_delayed_create_keeps_quick_reply_deleted(chat_group):
    owner = chat_group[2]
    identity = uuid.uuid4()
    save(owner, identity)
    with pytest.raises(APIException):
        save(owner, identity, {"title": "Late", "content": "Delayed creation", "expected_revision": 0})
    assert not listing(owner)


@pytest.mark.django_db
def test_direct_capabilities_do_not_advertise_poll(chat_group):
    _, _, owner, peer = chat_group
    conversation = get_or_create_direct_conversation(user=owner, other_user=peer)
    data = summary(conversation, owner)
    assert not data["supports_polls"]
    assert "poll" not in data["limits"]["message_kinds"]
