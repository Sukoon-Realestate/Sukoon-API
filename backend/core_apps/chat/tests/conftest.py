import uuid
import pytest
from core_apps.features.planning_models import GroupMembership, HousingGroup
from core_apps.chat.services.group_provisioning import provision_group


@pytest.fixture
def chat_group(user, another_user, settings, tmp_path):
    for member in (user, another_user):
        member.is_verified = True
        member.save(update_fields=["is_verified"])
    settings.CHAT_PRIVATE_MEDIA_ROOT = tmp_path / "chat-private"
    group = HousingGroup.objects.create(name="Private fixture", capacity=4)
    GroupMembership.objects.create(group=group, user=user, role="admin")
    GroupMembership.objects.create(group=group, user=another_user)
    return group, provision_group(group), user, another_user


def message_request(content="Hello", **extra):
    return {
        "client_message_id": str(uuid.uuid4()),
        "kind": "text",
        "content": content,
        "attachment_ids": [],
        "reply_to_message_id": None,
        **extra,
    }
