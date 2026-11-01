import pytest
from rest_framework.exceptions import ValidationError
from core_apps.chat.services.polls import normalize_poll
from core_apps.chat.services.group_send import send_group_message
from core_apps.chat.services.group_projection import summary
from core_apps.chat.services.group_access import authorize
from core_apps.chat.services.message_service import get_or_create_direct_conversation
from .conftest import message_request
from .test_productivity import project


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
