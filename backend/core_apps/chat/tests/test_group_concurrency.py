from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
import pytest
from django.db import close_old_connections, connection, transaction
from core_apps.chat.models import (
    ChatEvent,
    ChatNotificationDelivery,
    Conversation,
    Message,
)
from core_apps.chat.services.group_provisioning import provision_group
from core_apps.chat.services.group_send import send_group_message
from core_apps.chat.services.group_outbox import deliver_event, deliver_pushes
from core_apps.chat.services.group_operations import set_preference
from .conftest import message_request

pytestmark = pytest.mark.django_db(transaction=True)


def race(first, second):
    if connection.vendor != "postgresql":
        pytest.skip("Row-lock evidence requires PostgreSQL")
    barrier = Barrier(2)

    def run(operation):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            return operation()
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run, x) for x in [first, second]]
        return [x.result(timeout=20) for x in futures]


def test_postgres_concurrent_provisioning(chat_group):
    group, conversation, _, _ = chat_group
    results = race(lambda: provision_group(group).id, lambda: provision_group(group).id)
    assert results == [conversation.id, conversation.id]
    assert Conversation.objects.filter(housing_group=group).count() == 1


def test_postgres_concurrent_send_same_identity(chat_group):
    _, conversation, user, _ = chat_group
    payload = message_request()
    result = race(
        lambda: send_group_message(conversation, user, payload).id,
        lambda: send_group_message(conversation, user, payload).id,
    )
    assert result[0] == result[1]
    assert Message.objects.filter(conversation=conversation).count() == 1
    assert (
        ChatEvent.objects.filter(conversation=conversation, kind="message.new").count()
        == 1
    )


def test_outbox_crash_retry_and_muted_delayed_push(chat_group):
    _, conversation, user, member = chat_group
    send_group_message(conversation, user, message_request())
    event = ChatEvent.objects.get(conversation=conversation, kind="message.new")
    with patch("core_apps.chat.services.group_outbox.get_channel_layer") as layer:

        async def crash(*args, **kwargs):
            raise RuntimeError("worker died before fanout")

        layer.return_value.group_send = crash
        with pytest.raises(RuntimeError):
            deliver_event(event.pk)
    event.refresh_from_db()
    assert event.delivered_at is None
    assert deliver_event(event.pk)
    assert not deliver_event(event.pk)
    assert ChatNotificationDelivery.objects.count() == 1
    set_preference(conversation, member, True)
    with patch(
        "core_apps.notifications.services.fcm_service.FCMService.send_push_to_user"
    ) as push:
        deliver_pushes()
        deliver_pushes()
        push.assert_not_called()


def test_committed_removal_blocks_queued_outbound_content(chat_group):
    from core_apps.chat.services.group_events import event_payload

    group, conversation, user, member = chat_group
    send_group_message(conversation, user, message_request("Private"))
    event = ChatEvent.objects.get(conversation=conversation, kind="message.new")
    group.memberships.filter(user=member).update(status="removed")
    assert event_payload(event, member) is None
    deliver_event(event.pk)
    assert not ChatNotificationDelivery.objects.exists()


def test_send_racing_removal_serializes_on_the_roster(chat_group):
    from rest_framework.exceptions import PermissionDenied
    from core_apps.features.planning_models import HousingGroup
    from core_apps.chat.services.group_events import event_payload

    group, conversation, _, member = chat_group

    def send():
        try:
            return send_group_message(conversation, member, message_request()).id
        except PermissionDenied:
            return None

    def remove():
        with transaction.atomic():
            HousingGroup.objects.select_for_update().get(pk=group.pk)
            group.memberships.filter(user=member).update(status="removed")

    sent, _ = race(send, remove)
    assert conversation.messages.count() == (1 if sent else 0)
    for event in ChatEvent.objects.filter(conversation=conversation):
        assert event_payload(event, member) is None


def test_cleanup_racing_attach_preserves_committed_media(chat_group):
    import uuid
    from datetime import timedelta
    from django.utils import timezone
    from rest_framework.exceptions import ValidationError
    from core_apps.chat.models import ChatAttachment
    from core_apps.chat.services.group_media_storage import (
        upload_attachment,
        cleanup_orphans,
        private_path,
    )
    from .test_group_media import image_file

    _, conversation, user, _ = chat_group
    image = upload_attachment(conversation, user, image_file(), uuid.uuid4(), "image")
    ChatAttachment.objects.filter(pk=image.pk).update(
        created_at=timezone.now() - timedelta(days=2)
    )

    def attach():
        try:
            return send_group_message(
                conversation,
                user,
                message_request(kind="image", attachment_ids=[str(image.id)]),
            ).id
        except ValidationError:
            return None

    sent, _ = race(attach, cleanup_orphans)
    image.refresh_from_db()
    assert image.state == ("attached" if sent else "expired")
    assert private_path(image.storage_key).exists() == bool(sent)
