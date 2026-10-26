from datetime import timedelta
from unittest.mock import patch
import pytest
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from core_apps.chat.models import ChatEvent, ChatNotificationDelivery
from core_apps.chat.services.conversation_preferences import (
    update_preferences,
    preferences_payload,
)
from core_apps.chat.services.group_notification_preferences import allows_message
from core_apps.chat.services.group_outbox import _notify, deliver_pushes
from core_apps.chat.services.group_send import send_group_message
from core_apps.chat.services.mention_navigation import navigation_payload
from .conftest import message_request
from .test_reactions_mentions import mention_request
from .test_all_mentions_navigation import all_request
from .test_direct_media import direct_chat  # noqa: F401

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "mode,receive_all,expected",
    [
        ("all", True, (True, True, True)),
        ("all", False, (True, True, False)),
        ("mentions", True, (False, True, True)),
        ("mentions", False, (False, True, False)),
        ("muted", True, (False, False, False)),
        ("muted", False, (False, False, False)),
    ],
)
def test_delivery_matrix_and_mention_navigation(
    chat_group, mode, receive_all, expected
):
    _, chat, owner, peer = chat_group
    update_preferences(
        chat, peer, {"notification_mode": mode, "notify_all_mentions": receive_all}
    )
    assert preferences_payload(chat, peer)["notification_mode"] == mode
    assert preferences_payload(chat, owner)["notification_mode"] == "all"
    for body, wanted in zip(
        [message_request(), mention_request(peer), all_request()], expected
    ):
        msg = send_group_message(chat, owner, body)
        event = ChatEvent.objects.get(message=msg, kind="message.new")
        p = chat.participant_set.get(user=peer)
        assert allows_message(p, msg) == wanted
        _notify(event, peer)
        assert (
            ChatNotificationDelivery.objects.filter(event=event, user=peer).exists()
            == wanted
        )
    assert navigation_payload(chat, p)["count"] == 2


def test_personal_mention_wins_over_disabled_all(chat_group):
    _, chat, owner, peer = chat_group
    update_preferences(
        chat, peer, {"notification_mode": "mentions", "notify_all_mentions": False}
    )
    body = mention_request(peer)
    end = len(body["content"].encode("utf-16-le")) // 2
    body["content"] += " @all"
    body["mentions"].append({"kind": "all", "start": end + 1, "end": end + 5})
    msg = send_group_message(chat, owner, body)
    assert allows_message(chat.participant_set.get(user=peer), msg)


def test_timed_mute_resumes_mentions_preference(chat_group):
    _, chat, _, peer = chat_group
    update_preferences(
        chat, peer, {"notification_mode": "mentions", "notify_all_mentions": False}
    )
    update_preferences(chat, peer, {"mute_duration": "hour"})
    assert preferences_payload(chat, peer)["notification_mode"] == "muted"
    chat.participant_set.filter(user=peer).update(
        muted_until=timezone.now() - timedelta(seconds=1)
    )
    assert preferences_payload(chat, peer)["notification_mode"] == "mentions"
    assert not preferences_payload(chat, peer)["notify_all_mentions"]


@pytest.mark.parametrize(
    "change",
    [
        {"notification_mode": "invalid"},
        {"notify_all_mentions": "false"},
        {"notification_mode": "all", "mute_duration": "hour"},
    ],
)
def test_invalid_settings_do_not_partially_save(chat_group, change):
    _, chat, _, peer = chat_group
    with pytest.raises(ValidationError):
        update_preferences(chat, peer, change)
    assert preferences_payload(chat, peer)["notification_mode"] == "all"


def test_group_settings_unavailable_for_direct_chat(direct_chat):  # noqa: F811
    chat, owner, peer = direct_chat
    with pytest.raises(ValidationError):
        update_preferences(chat, peer, {"notification_mode": "mentions"})


@pytest.mark.parametrize(
    "change", [{"notification_mode": "muted"}, {"notify_all_mentions": False}]
)
def test_queued_push_rechecks_latest_preference(chat_group, change):
    _, chat, owner, peer = chat_group
    msg = send_group_message(chat, owner, all_request())
    event = ChatEvent.objects.get(message=msg, kind="message.new")
    _notify(event, peer)
    update_preferences(chat, peer, change)
    with patch(
        "core_apps.notifications.services.fcm_service.FCMService.send_push_to_user"
    ) as push:
        deliver_pushes(event_pk=event.pk)
        push.assert_not_called()


@pytest.mark.parametrize(
    "change", [{"notification_mode": "muted"}, {"notify_all_mentions": False}]
)
def test_durable_dispatch_rechecks_current_mode(chat_group, change):
    from types import SimpleNamespace
    from core_apps.notifications.services.push_delivery import allowed

    _, chat, owner, peer = chat_group
    message = send_group_message(chat, owner, all_request())
    event = ChatEvent.objects.get(message=message, kind="message.new")
    _notify(event, peer)
    notice = ChatNotificationDelivery.objects.get(event=event, user=peer).notification
    item = SimpleNamespace(
        notification=notice,
        device=SimpleNamespace(is_active=True, user_id=peer.pk, auth_session=None),
    )
    assert allowed(item)
    update_preferences(chat, peer, change)
    assert not allowed(item)


def test_database_defaults_support_previous_release_memberships():
    from django.db import connection

    if connection.vendor != "postgresql":
        pytest.skip("Rolling deployment uses PostgreSQL")
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT column_name, column_default FROM information_schema.columns "
            "WHERE table_name = 'chat_conversationparticipant' "
            "AND column_name IN ('notification_mode', 'notify_all_mentions')"
        )
        defaults = dict(cursor.fetchall())
    assert defaults["notification_mode"] == "'all'::character varying"
    assert defaults["notify_all_mentions"] == "true"
