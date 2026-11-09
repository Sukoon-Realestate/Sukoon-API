import uuid

import pytest
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError
from core_apps.chat.services.polls import normalize_poll, change_poll
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


# Contract (Sprint 00, A5-12): polls expose aggregate counts and the viewer's own
# choice only. No voter-identity list was ever implemented, routed or consumed by a
# client; adding one is a separate product/privacy decision, not test repair.


def fresh(message):
    # Projections read message.poll; re-fetch so a cached poll row never hides a committed change.
    return type(message).objects.get(pk=message.pk)


def option_counts(payload):
    return [option["votes"] for option in payload["poll"]["options"]]


@pytest.mark.django_db
def test_poll_counts_are_aggregate_and_respect_current_membership(chat_group):
    group, conversation, owner, peer = chat_group
    message = poll_message(conversation, owner, allow_multiple=True)
    options = [o["id"] for o in project(conversation, peer, message)["poll"]["options"]]
    change_poll(conversation, peer, message.id, poll_command(conversation, peer, option_ids=options))
    change_poll(conversation, owner, message.id, poll_command(conversation, owner, option_ids=[options[1]]))

    seen_by_peer = project(conversation, peer, fresh(message))
    assert seen_by_peer["poll"]["voter_count"] == 2
    assert option_counts(seen_by_peer) == [1, 2]
    assert [o["is_mine"] for o in seen_by_peer["poll"]["options"]] == [True, True]
    assert [o["is_mine"] for o in project(conversation, owner, fresh(message))["poll"]["options"]] == [False, True]
    for option in seen_by_peer["poll"]["options"]:
        assert set(option) <= {"id", "text", "url", "votes", "is_mine"}

    group.memberships.filter(user=peer).update(status="removed")
    seen_by_owner = project(conversation, owner, fresh(message))
    assert seen_by_owner["poll"]["voter_count"] == 1
    assert option_counts(seen_by_owner) == [0, 1]


@pytest.mark.django_db
def test_closed_poll_reports_closed_and_rejects_new_votes(chat_group):
    _, conversation, owner, peer = chat_group
    message = poll_message(conversation, owner)
    options = [o["id"] for o in project(conversation, peer, message)["poll"]["options"]]
    assert project(conversation, peer, message)["poll"]["voter_count"] == 0

    with pytest.raises(PermissionDenied):
        change_poll(conversation, peer, message.id, poll_command(conversation, peer), close=True)
    change_poll(conversation, owner, message.id, poll_command(conversation, owner), close=True)
    assert project(conversation, peer, fresh(message))["poll"]["is_closed"] is True
    with pytest.raises(ValidationError):
        change_poll(conversation, peer, message.id, poll_command(conversation, peer, option_ids=[options[0]]))


@pytest.mark.django_db
def test_poll_commands_reject_non_poll_messages(chat_group):
    _, conversation, owner, peer = chat_group
    message = send_group_message(conversation, owner, message_request("plain"))
    with pytest.raises(ValidationError):
        change_poll(conversation, peer, message.id, poll_command(conversation, peer))
    assert project(conversation, peer, message).get("poll") is None
