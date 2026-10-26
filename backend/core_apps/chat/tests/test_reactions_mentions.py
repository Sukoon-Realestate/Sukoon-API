import uuid
from unittest.mock import patch
import pytest
from channels.db import database_sync_to_async
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError
from core_apps.chat.models import (
    ChatEvent,
    MessageReaction,
    ChatNotificationDelivery,
    Conversation,
)
from core_apps.chat.consumers import ChatConsumer
from core_apps.chat.services.group_access import authorize
from core_apps.chat.services.group_projection import message_payload, sender_payload
from core_apps.chat.services.group_send import send_group_message
from core_apps.chat.services.group_limits import ChatConflict
from core_apps.chat.services.reactions import set_reaction
from core_apps.chat.services.message_mutations import mutate_message
from core_apps.chat.services.group_outbox import _notify, deliver_pushes
from core_apps.common.testing import WebsocketCommunicator
from .conftest import message_request
from .test_direct_media import direct_chat  # noqa: F401
from core_apps.features.tests.test_company_housing import (
    company_setup,
    rental_participants,
    policy,
    proposed,
)


def reaction_request(conversation, user, emoji="👍"):
    _, participant, _ = authorize(conversation, user)
    return {
        "emoji": emoji,
        "membership_period": str(participant.membership_period),
        "operation_id": str(uuid.uuid4()),
    }


def mention_request(user, prefix="😀 أهلًا "):
    label = "@" + sender_payload(user)["name"]
    start = len(prefix.encode("utf-16-le")) // 2
    return message_request(
        prefix + label + " تعال هنا",
        mentions=[
            {
                "user_id": str(user.id),
                "start": start,
                "end": start + len(label.encode("utf-16-le")) // 2,
            }
        ],
    )


@pytest.mark.django_db
@pytest.mark.parametrize("chat", ["chat_group", "direct_chat"])
def test_reactions_are_per_user_replaceable_removable_and_idempotent(request, chat):
    fixture = request.getfixturevalue(chat)
    conversation, owner, peer = fixture[1:] if chat == "chat_group" else fixture
    message = send_group_message(conversation, owner, message_request())
    first = reaction_request(conversation, peer)
    initial = set_reaction(conversation, peer, message.id, first)
    assert initial["reactions"] == [{"emoji": "👍", "count": 1, "is_mine": True}]
    assert initial["revision"] == 1  # Does not conflict with an open text editor.
    assert (
        set_reaction(conversation, peer, message.id, first)["reactions_revision"] == 1
    )
    second = set_reaction(
        conversation, owner, message.id, reaction_request(conversation, owner)
    )
    assert second["reactions"] == [{"emoji": "👍", "count": 2, "is_mine": True}]
    changed = set_reaction(
        conversation, peer, message.id, reaction_request(conversation, peer, "❤️")
    )
    assert len(changed["reactions"]) == 2
    # A late retry of the original operation must not restore the old emoji.
    replay = set_reaction(conversation, peer, message.id, first)
    assert next(r for r in replay["reactions"] if r["is_mine"])["emoji"] == "❤️"
    removed = set_reaction(
        conversation, peer, message.id, reaction_request(conversation, peer, None)
    )
    assert removed["reactions"] == [{"emoji": "👍", "count": 1, "is_mine": False}]
    assert MessageReaction.objects.filter(message=message).count() == 1
    assert (
        ChatEvent.objects.filter(message=message, kind="message.reaction").count() == 4
    )


@pytest.mark.django_db
@pytest.mark.parametrize("emoji", ["👍🏽", "👨‍👩‍👧‍👦", "🇪🇬", "❤️", "1️⃣", "🫶"])
def test_multicodepoint_emoji_reactions(chat_group, emoji):
    _, conversation, owner, peer = chat_group
    message = send_group_message(conversation, owner, message_request())
    result = set_reaction(
        conversation, peer, message.id, reaction_request(conversation, peer, emoji)
    )
    assert result["reactions"][0]["emoji"] == emoji


@pytest.mark.django_db
@pytest.mark.parametrize("emoji", ["hello", "👍👍", "", "🏻", "@someone", "\x00"])
def test_reactions_reject_nonemoji_payloads(chat_group, emoji):
    _, conversation, owner, peer = chat_group
    message = send_group_message(conversation, owner, message_request())
    with pytest.raises(ValidationError):
        set_reaction(
            conversation, peer, message.id, reaction_request(conversation, peer, emoji)
        )


@pytest.mark.django_db
def test_reaction_api_current_access_hidden_message_and_tombstone(
    chat_group, superuser
):
    group, conversation, owner, peer = chat_group
    message = send_group_message(conversation, owner, message_request())
    body = reaction_request(conversation, peer)
    client = APIClient()
    url = (
        f"/api/v1/chat/conversations/{conversation.id}/messages/{message.id}/reaction/"
    )
    client.force_authenticate(superuser)
    assert client.put(url, body, format="json").status_code == 403
    client.force_authenticate(peer)
    response = client.put(url, body, format="json")
    assert response.status_code == 200, response.content
    assert response.json()["data"]["reactions"][0]["is_mine"]
    assert client.put(url, {**body, "emoji": "😂"}, format="json").status_code == 409
    participant = conversation.participant_set.get(user=peer)
    participant.visible_from_sequence = message.sequence + 1
    participant.save()
    assert client.put(url, body, format="json").status_code == 404
    participant.visible_from_sequence = 1
    participant.save()
    message.deleted_at = message.created_at
    message.save()
    assert (
        client.put(url, reaction_request(conversation, peer), format="json").status_code
        == 400
    )
    _, participant, member = authorize(conversation, peer)
    assert message_payload(message, participant, member)["reactions"] == []
    group.memberships.filter(user=peer).update(status="removed")
    assert client.put(url, body, format="json").status_code == 403


@pytest.mark.django_db
def test_group_members_are_current_authorized_and_never_direct(
    direct_chat, chat_group, superuser
):
    group, conversation, owner, peer = chat_group
    client = APIClient()
    url = f"/api/v1/chat/conversations/{conversation.id}/members/"
    client.force_authenticate(owner)
    response = client.get(url)
    assert response.status_code == 200, response.content
    assert {p["id"] for p in response.json()["data"]} == {str(owner.id), str(peer.id)}
    group.memberships.filter(user=peer).update(status="removed")
    assert [p["id"] for p in client.get(url).json()["data"]] == [str(owner.id)]
    client.force_authenticate(superuser)
    assert client.get(url).status_code == 403
    direct, user, _ = direct_chat
    client.force_authenticate(user)
    assert (
        client.get(f"/api/v1/chat/conversations/{direct.id}/members/").status_code
        == 404
    )


@pytest.mark.django_db
def test_mentions_keep_exact_ids_utf16_spans_and_original_send_identity(chat_group):
    _, conversation, owner, peer = chat_group
    body = mention_request(peer)
    message = send_group_message(conversation, owner, body)
    assert message.mentions[0]["user_id"] == str(peer.id)
    assert message.mentions[0]["start"] == body["mentions"][0]["start"]
    assert send_group_message(conversation, owner, body).id == message.id
    with pytest.raises(ChatConflict):
        send_group_message(conversation, owner, {**body, "mentions": []})
    _, participant, member = authorize(conversation, peer)
    payload = message_payload(message, participant, member)
    assert payload["mentions"][0]["name"] == sender_payload(peer)["name"]
    assert "membership_period" not in payload["mentions"][0]


@pytest.mark.django_db
def test_mentions_reject_nonmembers_removed_members_and_forged_spans(
    chat_group, superuser
):
    group, conversation, owner, peer = chat_group
    for body in [mention_request(superuser), mention_request(peer, prefix="")]:
        if body["mentions"][0]["user_id"] == str(peer.id):
            body["mentions"][0]["end"] += 1
        with pytest.raises(ValidationError):
            send_group_message(conversation, owner, body)
    group.memberships.filter(user=peer).update(status="removed")
    with pytest.raises(ValidationError):
        send_group_message(conversation, owner, mention_request(peer))


@pytest.mark.django_db
def test_mentions_only_notifies_once_and_suppresses_ordinary_messages(
    chat_group,
):
    _, conversation, owner, peer = chat_group
    conversation.participant_set.filter(user=peer).update(notification_mode="mentions")
    body = mention_request(peer)
    message = send_group_message(conversation, owner, body)
    event = ChatEvent.objects.get(message=message, kind="message.new")
    _notify(event, peer)
    _notify(event, peer)
    send_group_message(conversation, owner, body)
    delivery = ChatNotificationDelivery.objects.get(event=event, user=peer)
    assert delivery.notification.data["is_mention"] == "true"
    assert delivery.notification.data["message_id"] == str(message.id)
    assert "الإشارة" in delivery.notification.title
    assert ChatNotificationDelivery.objects.filter(event=event, user=peer).count() == 1
    assert not ChatNotificationDelivery.objects.filter(event=event, user=owner).exists()
    ordinary = send_group_message(conversation, owner, message_request("Ordinary"))
    _notify(ChatEvent.objects.get(message=ordinary, kind="message.new"), peer)
    assert not ChatNotificationDelivery.objects.filter(
        event__message=ordinary, user=peer
    ).exists()


@pytest.mark.django_db
def test_editing_retains_unchanged_mention_and_drops_changed_name(chat_group):
    _, conversation, owner, peer = chat_group
    message = send_group_message(conversation, owner, mention_request(peer))
    _, participant, _ = authorize(conversation, owner)
    packet = {
        "type": "message.edit",
        "operation_id": str(uuid.uuid4()),
        "message_id": str(message.id),
        "membership_period": str(participant.membership_period),
        "expected_revision": 1,
        "content": "👍 " + message.content,
    }
    changed = mutate_message(conversation, owner, packet)
    assert changed["mentions"][0]["start"] == message.mentions[0]["start"] + 3
    packet.update(
        operation_id=str(uuid.uuid4()), expected_revision=2, content="No mention now"
    )
    assert mutate_message(conversation, owner, packet)["mentions"] == []


@pytest.mark.django_db
def test_mention_push_is_claimed_once_and_revoked_member_is_not_notified(chat_group):
    from core_apps.notifications.models import DeviceToken
    from core_apps.notifications.services.push_delivery import dispatch

    group, conversation, owner, peer = chat_group
    device = DeviceToken.objects.create(user=peer, token="mention-device")
    conversation.participant_set.filter(user=peer).update(notification_mode="mentions")
    message = send_group_message(conversation, owner, mention_request(peer))
    event = ChatEvent.objects.get(message=message, kind="message.new")
    _notify(event, peer)
    with patch(
        "core_apps.notifications.services.fcm_service.FCMService.send_push_to_device", return_value=True
    ) as push:
        deliver_pushes(event_pk=event.pk)
        deliver_pushes(event_pk=event.pk)
        assert dispatch() == 1
        push.assert_called_once()
        assert push.call_args.kwargs["data"]["is_mention"] == "true"
        assert push.call_args.kwargs["token"] == device.token
        newer = send_group_message(conversation, owner, mention_request(peer))
        newer_event = ChatEvent.objects.get(message=newer, kind="message.new")
        _notify(newer_event, peer)
        group.memberships.filter(user=peer).update(status="removed")
        deliver_pushes(event_pk=newer_event.pk)
        assert dispatch() == 0
        push.assert_called_once()


@pytest.mark.django_db
def test_company_discussion_mentions_and_reactions_follow_case_membership(
    company_setup,
):
    proposed(company_setup)
    coordinator, approver = company_setup[1:3]
    conversation = Conversation.objects.get(company_request=company_setup[-1])
    message = send_group_message(conversation, coordinator, mention_request(approver))
    result = set_reaction(
        conversation, approver, message.id, reaction_request(conversation, approver)
    )
    assert result["reactions"][0]["is_mine"]
    event = ChatEvent.objects.get(message=message, kind="message.new")
    _notify(event, approver)
    notification = ChatNotificationDelivery.objects.get(
        event=event, user=approver
    ).notification
    assert notification.data["type"] == "company_request_chat"
    assert notification.data["is_mention"] == "true"
    assert notification.data["message_id"] == str(message.id)


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("chat", ["chat_group", "direct_chat"])
async def test_reaction_reaches_both_authorized_sockets(request, chat):
    fixture = await database_sync_to_async(request.getfixturevalue)(chat)
    conversation, owner, peer = fixture[1:] if chat == "chat_group" else fixture
    message = await database_sync_to_async(send_group_message)(
        conversation, owner, message_request()
    )
    sockets = []
    try:
        for user in (owner, peer):
            socket = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/")
            socket.scope["user"] = user
            assert (await socket.connect())[0]
            sockets.append(socket)
        body = await database_sync_to_async(reaction_request)(conversation, peer)
        await database_sync_to_async(set_reaction)(conversation, peer, message.id, body)
        for index, socket in enumerate(sockets):
            event = await socket.receive_json_from()
            assert event["type"] == "message.reaction"
            assert event["payload"]["id"] == str(message.id)
            assert event["payload"]["reactions"][0]["is_mine"] == (index == 1)
    finally:
        for socket in sockets:
            await socket.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("broadcast", [False, True])
async def test_group_mention_is_delivered_with_identity_on_both_sockets(chat_group, broadcast):
    _, conversation, owner, peer = chat_group
    sockets = []
    try:
        for user in (owner, peer):
            socket = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/")
            socket.scope["user"] = user
            assert (await socket.connect())[0]
            sockets.append(socket)
        body = await database_sync_to_async(mention_request)(peer)
        if broadcast:
            body = message_request("@all", mentions=[{"kind": "all", "start": 0, "end": 4}])
        await sockets[0].send_json_to(
            {
                "type": "message.send",
                "protocol": "group.v1",
                "conversation_id": str(conversation.id),
                **body,
            }
        )
        sender_packets = [await sockets[0].receive_json_from() for _ in range(2)]
        assert {p["type"] for p in sender_packets} == {"message.ack", "message.new"}
        received = await sockets[1].receive_json_from()
        assert received["type"] == "message.new"
        mention = received["payload"]["mentions"][0]
        assert mention.get("kind") == "all" if broadcast else mention["user_id"] == str(peer.id)
        assert received["payload"]["content"] == body["content"]
        assert await database_sync_to_async(
            lambda: ChatNotificationDelivery.objects.filter(
                event__message__id=received["payload"]["id"],
                user=peer,
                notification__data__is_mention="true",
            ).exists()
        )()
        from core_apps.chat.services.mention_navigation import see_mention
        _, participant, _ = await database_sync_to_async(authorize)(conversation, peer)
        await database_sync_to_async(see_mention)(conversation, peer, received["payload"]["id"], participant.membership_period)
        assert (await sockets[1].receive_json_from())["type"] == "mentions.updated"
        assert await sockets[0].receive_nothing(timeout=0.1)
    finally:
        for socket in sockets:
            await socket.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("broadcast", [False, True])
def test_mention_is_queued_after_commit_and_sent_by_device_worker(chat_group, broadcast):
    from core_apps.notifications.models import DeviceToken, PushDelivery
    from core_apps.notifications.services.push_delivery import dispatch

    _, conversation, owner, peer = chat_group
    DeviceToken.objects.create(user=peer, token="committed-mention-device")
    conversation.participant_set.filter(user=peer).update(notification_mode="mentions")
    with patch("core_apps.notifications.services.fcm_service.FCMService.send_push_to_device", return_value=True) as push:
        body = message_request("@all", mentions=[{"kind": "all", "start": 0, "end": 4}]) if broadcast else mention_request(peer)
        message = send_group_message(conversation, owner, body)
        push.assert_not_called()
        assert PushDelivery.objects.filter(notification__data__message_id=str(message.id)).count() == 1
        assert dispatch() == 1
        push.assert_called_once()
        assert push.call_args.kwargs["data"]["message_id"] == str(message.id)
        assert push.call_args.kwargs["data"]["is_mention"] == "true"
        deliver_pushes()
        assert dispatch() == 0
        push.assert_called_once()


def test_general_chat_maintenance_recovers_pending_pushes():
    from core_apps.common.tasks import maintain_chat
    with (
        patch("core_apps.chat.moderation.queue.process_one"),
        patch("core_apps.chat.moderation.notifications.deliver_pending"),
        patch("core_apps.chat.services.group_outbox.drain_outbox"),
        patch("core_apps.chat.services.group_outbox.deliver_pushes") as deliver,
    ):
        maintain_chat()
        deliver.assert_called_once_with(limit=20)
