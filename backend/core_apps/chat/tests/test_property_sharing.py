import uuid
import pytest
from django.urls import reverse
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.exceptions import PermissionDenied, ValidationError

from core_apps.properties.models import Property, PropertyType, City, Governorate
from core_apps.chat.models import Message
from core_apps.chat.services.group_access import authorize
from core_apps.chat.services.group_send import send_group_message
from core_apps.chat.services.group_projection import message_payload, summary
from core_apps.chat.services.group_operations import delete_group_message
from core_apps.chat.services.group_limits import ChatConflict
from core_apps.chat.services.property_sharing import (
    ChatPropertyUnavailable,
    property_card,
    properties_for_messages,
)
from .conftest import message_request

pytestmark = pytest.mark.django_db


@pytest.fixture
def shared_property(chat_group):
    _, _, owner, _ = chat_group
    governorate, _ = Governorate.objects.get_or_create(
        slug="chat-cairo", defaults={"name": "Cairo"}
    )
    city, _ = City.objects.get_or_create(
        slug="chat-cairo", governorate=governorate, defaults={"name": "Cairo"}
    )
    kind, _ = PropertyType.objects.get_or_create(
        slug="apartment", defaults={"name": "Apartment"}
    )
    return Property.objects.create(
        owner=owner,
        title="Student apartment",
        price="2500.00",
        status=Property.Status.VERIFIED,
        property_type=kind,
        governorate=governorate,
        city=city,
        district="University",
        area=100,
    )


def property_request(prop, **extra):
    return message_request(
        "", kind="property", property={"property_id": str(prop.id)}, **extra
    )


def test_reference_is_server_projected_and_read_after_restart(
    chat_group, shared_property, api_client
):
    _, conversation, sender, recipient = chat_group
    request = property_request(shared_property)
    message = send_group_message(conversation, sender, request)
    assert message.property_reference == {
        "property_id": str(shared_property.id),
        "offer_id": None,
    }
    api_client.force_authenticate(recipient)
    response = api_client.get(reverse("message-list", kwargs={"id": conversation.id}))
    assert response.status_code == 200
    card = response.json()["data"][0]["property"]
    assert card["title"] == shared_property.title and card["price"] == "2500.00"
    assert card["availability"] == "available"
    assert not {
        "owner",
        "owner_id",
        "owner_phone",
        "is_saved",
        "ownership_proof",
    } & set(card)
    shared_property.price = "2700.00"
    shared_property.save(update_fields=["price"])
    assert property_card(message.property_reference)["price"] == "2700.00"


def test_exact_retry_after_removal_and_conflicting_payload(chat_group, shared_property):
    _, conversation, sender, _ = chat_group
    request = property_request(shared_property)
    original = send_group_message(conversation, sender, request)
    shared_property.status = Property.Status.HIDDEN
    shared_property.save(update_fields=["status"])
    assert send_group_message(conversation, sender, request).id == original.id
    assert Message.objects.filter(conversation=conversation).count() == 1
    with pytest.raises(ChatConflict):
        send_group_message(conversation, sender, {**request, "content": "different"})
    with pytest.raises(ChatPropertyUnavailable):
        send_group_message(conversation, sender, property_request(shared_property))
    _, participant, member = authorize(conversation, sender)
    assert message_payload(original, participant, member)["property"] == {
        **original.property_reference,
        "availability": "unavailable",
    }


@pytest.mark.parametrize(
    "changes",
    [
        {"property": {"property_id": "bad"}},
        {"property": {"property_id": str(uuid.uuid4()), "title": "forged"}},
        {"kind": "text"},
        {"attachment_ids": [str(uuid.uuid4())]},
        {"location": {"latitude": 30, "longitude": 31}},
    ],
)
def test_rejects_invalid_or_mixed_payload(chat_group, shared_property, changes):
    _, conversation, sender, _ = chat_group
    with pytest.raises(ValidationError):
        send_group_message(
            conversation, sender, {**property_request(shared_property), **changes}
        )
    assert not Message.objects.filter(conversation=conversation).exists()


def test_offer_identity_and_availability(chat_group, shared_property):
    _, conversation, sender, _ = chat_group
    shared_property.rental_inventory = {
        "schema_version": 1,
        "offers": [
            {
                "id": "offer-room",
                "name": "Room one",
                "rental_scope": "room",
                "availability": "available",
                "terms": {"price": "800.00", "price_period": "monthly"},
            },
        ],
    }
    shared_property.save(update_fields=["rental_inventory"])
    request = property_request(shared_property)
    request["property"]["offer_id"] = "offer-room"
    message = send_group_message(conversation, sender, request)
    card = property_card(message.property_reference)
    assert card["offer_id"] == "offer-room" and card["price"] == "800.00"
    assert card["offer_label"] == "Room one"
    request["client_message_id"] = str(uuid.uuid4())
    request["property"]["offer_id"] = "another-property-offer"
    with pytest.raises(ChatPropertyUnavailable):
        send_group_message(conversation, sender, request)
    shared_property.rental_inventory["offers"][0]["archived"] = True
    shared_property.save(update_fields=["rental_inventory"])
    assert property_card(message.property_reference)["availability"] == "unavailable"


def test_membership_direct_scope_and_support(chat_group, shared_property):
    from core_apps.chat.services.message_service import (
        get_or_create_direct_conversation,
    )

    group, conversation, sender, recipient = chat_group
    direct = get_or_create_direct_conversation(user=sender, other_user=recipient)
    assert "property" in summary(conversation, sender)["limits"]["message_kinds"]
    assert "property" not in summary(direct, sender)["limits"]["message_kinds"]
    with pytest.raises(ValidationError):
        send_group_message(direct, sender, property_request(shared_property))
    group.memberships.filter(user=sender).update(status="left")
    with pytest.raises(PermissionDenied):
        send_group_message(conversation, sender, property_request(shared_property))


def test_delete_and_reply_redaction(chat_group, shared_property):
    _, conversation, sender, recipient = chat_group
    original = send_group_message(
        conversation, sender, property_request(shared_property)
    )
    reply = send_group_message(
        conversation,
        recipient,
        message_request("Looks good", reply_to_message_id=str(original.id)),
    )
    _, participant, member = authorize(conversation, recipient)
    assert message_payload(reply, participant, member)["reply_to"]["kind"] == "property"
    deleted = delete_group_message(conversation, sender, original.id)
    assert deleted["property"] is None
    reply.refresh_from_db()
    assert message_payload(reply, participant, member)["reply_to"] == {
        "id": str(original.id),
        "availability": "unavailable",
    }


def test_groups_filter_runs_before_pagination(chat_group, api_client):
    from core_apps.chat.services.message_service import (
        get_or_create_direct_conversation,
    )

    _, conversation, sender, recipient = chat_group
    get_or_create_direct_conversation(
        user=sender, other_user=recipient, workspace="student"
    )
    api_client.force_authenticate(sender)
    response = api_client.get(
        reverse("conversation-list"),
        {"workspace": "student", "conversation_type": "housing_group", "page_size": 1},
    )
    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["conversation_id"] == str(conversation.id)
    assert (
        api_client.get(
            reverse("conversation-list"),
            {"workspace": "individual", "conversation_type": "housing_group"},
        ).data["count"]
        == 0
    )


def test_property_projection_is_batched(chat_group, shared_property):
    _, conversation, sender, _ = chat_group
    messages = [
        send_group_message(conversation, sender, property_request(shared_property))
        for _ in range(4)
    ]
    with CaptureQueriesContext(connection) as queries:
        properties = properties_for_messages(messages)
        cards = [
            property_card(message.property_reference, properties)
            for message in messages
        ]
    assert len(queries) == 1
    assert all(card["availability"] == "available" for card in cards)


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_property_two_sockets_rest_retry_and_current_redaction(
    chat_group, shared_property
):
    from channels.db import database_sync_to_async
    from core_apps.chat.consumers import ChatConsumer
    from core_apps.common.testing import WebsocketCommunicator
    from rest_framework.test import APIClient

    _, conversation, sender, recipient = chat_group
    sockets = []
    body = property_request(shared_property)
    packet = {
        "type": "message.send",
        "protocol": "group.v1",
        "conversation_id": str(conversation.id),
        **body,
    }
    try:
        for actor in (sender, recipient):
            socket = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/")
            socket.scope["user"] = actor
            assert (await socket.connect())[0]
            sockets.append(socket)
        await sockets[0].send_json_to(packet)
        sent = [await sockets[0].receive_json_from() for _ in range(2)]
        assert {event["type"] for event in sent} == {"message.ack", "message.new"}
        received = await sockets[1].receive_json_from()
        assert received["type"] == "message.new"
        card = received["payload"]["property"]
        assert card["property_id"] == str(shared_property.id)
        assert card["title"] == shared_property.title
        identity = received["payload"]["id"]

        @database_sync_to_async
        def replay_then_withdraw():
            client = APIClient()
            client.force_authenticate(sender)
            url = reverse("message-create", kwargs={"id": conversation.id})
            replay = client.post(url, body, format="json")
            assert replay.status_code == 201
            assert replay.json()["data"]["id"] == identity
            assert Message.objects.filter(conversation=conversation).count() == 1
            shared_property.status = Property.Status.HIDDEN
            shared_property.save(update_fields=["status"])
            denied = client.post(url, property_request(shared_property), format="json")
            assert denied.status_code == 422
            client.force_authenticate(recipient)
            history = client.get(
                reverse("message-list", kwargs={"id": conversation.id})
            )
            assert history.json()["data"][0]["property"] == {
                "property_id": str(shared_property.id),
                "offer_id": None,
                "availability": "unavailable",
            }

        await replay_then_withdraw()
        await sockets[0].send_json_to(
            {**packet, "client_message_id": str(uuid.uuid4())}
        )
        error = await sockets[0].receive_json_from()
        assert error["type"] == "chat.error"
        assert error["payload"]["code"] == "chat_property_unavailable"
        assert error["payload"]["status"] == 422
    finally:
        for socket in sockets:
            await socket.disconnect()


def test_property_event_respects_membership_visibility(chat_group, shared_property):
    from core_apps.chat.models import ChatEvent
    from core_apps.chat.services.group_events import event_payload

    _, conversation, sender, recipient = chat_group
    message = send_group_message(
        conversation, sender, property_request(shared_property)
    )
    event = ChatEvent.objects.get(message=message, kind="message.new")
    participant = conversation.participant_set.get(user=recipient)
    participant.visible_from_sequence = message.sequence + 1
    participant.save(update_fields=["visible_from_sequence"])
    assert event_payload(event, recipient) is None
