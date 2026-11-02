import uuid

import pytest
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError
from core_apps.chat.services.polls import normalize_poll, poll_voters, change_poll
from core_apps.chat.services.group_send import send_group_message
from core_apps.chat.services.group_projection import summary
from core_apps.chat.services.group_access import authorize
from core_apps.chat.services.message_service import get_or_create_direct_conversation
from .conftest import message_request
from .test_productivity import project


def poll_command(conversation, user, **extra):
    _, participant, _ = authorize(conversation, user)
    return {
        "membership_period": str(participant.membership_period),
        "operation_id": str(uuid.uuid4()),
        **extra,
    }


def poll_message(conversation, owner, **extra):
    return send_group_message(
        conversation,
        owner,
        message_request(
            "",
            kind="poll",
            poll={"question": "Which home?", "options": ["A", "B"], **extra},
        ),
    )


@pytest.mark.parametrize("links", [
    ["https://evil.test/properties/one", ""],
    ["https://sokoun.app/properties/one?token=secret", ""],
    ["https://sokoun.app/properties/one#private", ""],
    ["https://sokoun.app/owners/one", ""],
    ["https://sokoun.app/properties/one"],
])
def test_poll_links_are_public_property_links_and_match_option_count(links):
    with pytest.raises(ValidationError):
        normalize_poll({"question": "Which home?", "options": ["A", "B"], "links": links})


@pytest.mark.django_db
def test_links_survive_poll_projection_and_do_not_change_membership(chat_group):
    group, conversation, owner, peer = chat_group
    before = list(group.memberships.values_list("id", "status"))
    links = ["https://sokoun.app/properties/one/offers/a", "https://sokoun.app/properties/two/offers/b"]
    message = send_group_message(conversation, owner, message_request("", kind="poll", poll={"question": "Which home?", "options": ["A", "B"], "links": links}))
    payload = project(conversation, peer, message)
    assert [v["url"] for v in payload["poll"]["options"]] == links
    assert list(group.memberships.values_list("id", "status")) == before
    assert summary(conversation, peer)["supports_property_polls"] is True
    direct = get_or_create_direct_conversation(user=owner, other_user=peer)
    assert summary(direct, peer)["supports_property_polls"] is False


@pytest.mark.django_db
def test_poll_voters_are_grouped_and_respect_current_membership(chat_group):
    group, conversation, owner, peer = chat_group
    message = poll_message(conversation, owner, allow_multiple=True)
    options = [o["id"] for o in project(conversation, peer, message)["poll"]["options"]]
    change_poll(
        conversation,
        peer,
        message.id,
        poll_command(conversation, peer, option_ids=options),
    )
    change_poll(
        conversation,
        owner,
        message.id,
        poll_command(conversation, owner, option_ids=[options[1]]),
    )

    voters = poll_voters(conversation, peer, message.id)
    assert voters["voter_count"] == 2
    assert {v["id"] for v in voters["options"][0]["voters"]} == {str(peer.id)}
    assert {v["id"] for v in voters["options"][1]["voters"]} == {
        str(owner.id),
        str(peer.id),
    }

    group.memberships.filter(user=peer).update(status="removed")
    voters = poll_voters(conversation, owner, message.id)
    assert voters["voter_count"] == 1
    assert {v["id"] for v in voters["options"][1]["voters"]} == {str(owner.id)}
    assert voters["options"][0]["voters"] == []


@pytest.mark.django_db
def test_poll_voters_require_a_vote_until_the_poll_is_closed(chat_group):
    _, conversation, owner, peer = chat_group
    message = poll_message(conversation, owner)

    with pytest.raises(PermissionDenied):
        poll_voters(conversation, peer, message.id)
    assert poll_voters(conversation, owner, message.id)["voter_count"] == 0

    change_poll(
        conversation,
        owner,
        message.id,
        poll_command(conversation, owner),
        close=True,
    )
    assert poll_voters(conversation, peer, message.id)["is_closed"] is True


@pytest.mark.django_db
def test_poll_voters_reject_non_poll_messages(chat_group):
    _, conversation, owner, peer = chat_group
    message = send_group_message(conversation, owner, message_request("plain"))
    with pytest.raises(ValidationError):
        poll_voters(conversation, peer, message.id)
