"""Company authorization on the existing sequenced chat protocol."""

import uuid
from unittest.mock import patch
import pytest
from django.db import connection
from rest_framework.exceptions import PermissionDenied
from core_apps.users.models import User
from core_apps.chat.models import (
    Conversation,
    Message,
    ChatEvent,
    ChatNotificationDelivery,
)
from core_apps.chat.services.group_access import authorize
from core_apps.chat.services.group_projection import summary
from core_apps.chat.services.group_send import send_group_message
from core_apps.chat.services.group_events import event_payload
from core_apps.chat.services.group_outbox import deliver_event
from core_apps.chat.services.group_media_storage import upload_attachment
from core_apps.chat.views.group_attachments import accessible_attachment
from core_apps.features.company_models import Company, CompanyMembership
from core_apps.features.services.company import approval_routing, membership, bookings
from core_apps.features.tests.test_company_housing import (
    company_setup,
    rental_participants,
    policy,
    proposed,
    authenticated,
    API,
)
from core_apps.features.tests.test_cycle_concurrency import parallel_calls


def message(content="Synthetic company discussion"):
    return {"client_message_id": str(uuid.uuid4()), "kind": "text", "content": content}


@pytest.mark.django_db
def test_unknown_company_send_can_retry_exact_identity_with_membership_fence(
    company_setup,
):
    _, coordinator, _, company = company_setup[:4]
    request = company_setup[-1]
    conversation = Conversation.objects.get(company_request=request)
    client = authenticated(coordinator)
    projection = client.get(
        f"{API}companies/{company.id}/housing-requests/{request.id}/discussion/"
    ).json()["data"]
    assert projection["idempotent_message_retry"] is True
    data = {**message(), "membership_period": projection["membership_period"]}
    base = f"/api/v1/chat/conversations/{conversation.id}/messages/"
    lookup = base + f"by-client-id/{data['client_message_id']}/"
    assert client.get(lookup).status_code == 404
    first = client.post(base + "create/", data, format="json")
    second = client.post(base + "create/", data, format="json")
    assert first.status_code == second.status_code == 201
    assert first.json()["data"]["id"] == second.json()["data"]["id"]
    assert Message.objects.filter(
        conversation=conversation, client_message_id=data["client_message_id"]
    ).count() == 1
    assert ChatEvent.objects.filter(
        conversation=conversation, kind="message.new"
    ).count() == 1
    changed = client.post(
        base + "create/", {**data, "content": "Changed"}, format="json"
    )
    assert changed.status_code == 409


@pytest.mark.django_db(transaction=True)
def test_late_original_and_company_retry_commit_once(company_setup):
    if connection.vendor != "postgresql":
        pytest.skip("Real row-lock proof requires PostgreSQL")
    coordinator = company_setup[1]
    conversation = Conversation.objects.get(company_request=company_setup[-1])
    original = message()
    retry = {
        **original,
        "membership_period": summary(conversation, coordinator)["membership_period"],
    }
    results = parallel_calls(
        lambda index: send_group_message(
            conversation, coordinator, original if index == 0 else retry
        ).id
    )
    assert results[0] == results[1]
    assert Message.objects.filter(conversation=conversation).count() == 1
    assert ChatEvent.objects.filter(
        conversation=conversation, kind="message.new"
    ).count() == 1


@pytest.mark.django_db
def test_company_retry_rejects_wrong_period_and_authority_revocation(company_setup):
    coordinator, company = company_setup[1], company_setup[3]
    conversation = Conversation.objects.get(company_request=company_setup[-1])
    client = authenticated(coordinator)
    base = f"/api/v1/chat/conversations/{conversation.id}/messages/"
    original = {
        **message(),
        "membership_period": summary(conversation, coordinator)["membership_period"],
    }
    wrong_period = client.post(
        base + "create/",
        {**original, "membership_period": str(uuid.uuid4())},
        format="json",
    )
    assert wrong_period.status_code == 409
    lookup = base + f"by-client-id/{original['client_message_id']}/"
    assert client.get(lookup).status_code == 404
    CompanyMembership.objects.filter(company=company, user=coordinator).update(
        is_active=False
    )
    assert client.post(base + "create/", original, format="json").status_code == 403
    assert not Message.objects.filter(conversation=conversation).exists()


def backup(company):
    user = User.objects.create_user(
        email="backup-case@example.invalid",
        password="synthetic",
        first_name="Backup",
        is_verified=True,
    )
    return CompanyMembership.objects.create(
        company=company, user=user, is_approver=True
    )


@pytest.mark.django_db
def test_discussion_grants_case_access_and_never_approves_from_text(company_setup):
    owner, coordinator, approver, company = company_setup[:4]
    request = company_setup[-1]
    conversation = Conversation.objects.get(company_request=request)
    assert conversation.housing_group_id is None
    with pytest.raises(PermissionDenied):
        authorize(conversation, approver)
    with pytest.raises(PermissionDenied):
        authorize(conversation, owner)
    item = proposed(company_setup)
    assert summary(conversation, approver)["conversation_type"] == "company_request"
    payload = message("Approved")
    first = send_group_message(conversation, approver, payload)
    assert send_group_message(conversation, approver, payload).id == first.id
    item.refresh_from_db()
    assert item.status == "approval_pending" and not item.approvals.exists()
    card = conversation.messages.get(kind="system")
    assert card.system_data["item_id"] == str(item.id)
    assert "snapshot" not in card.system_data
    # Global direct/group inbox does not silently merge business discussions.
    client = authenticated(coordinator)
    ids = str(
        client.get("/api/v1/chat/conversations/", {"include_groups": "true"}).json()
    )
    assert str(conversation.id) not in ids
    response = client.get(
        f"{API}companies/{company.id}/housing-requests/{request.id}/discussion/"
    )
    assert response.status_code == 200 and response.json()["data"]["company_id"] == str(
        company.id
    )
    wrong = Company.objects.create(
        name="Other", registration_number="OTHER", contact_email="other@example.invalid"
    )
    CompanyMembership.objects.create(company=wrong, user=coordinator, is_admin=True)
    assert (
        client.get(
            f"{API}companies/{wrong.id}/housing-requests/{request.id}/discussion/"
        ).status_code
        == 404
    )


@pytest.mark.django_db
def test_reassignment_revokes_old_actor_and_preserves_business_history(company_setup):
    _, coordinator, approver, company = company_setup[:4]
    item = proposed(company_setup)
    conversation = Conversation.objects.get(company_request=item.request)
    previous = send_group_message(conversation, coordinator, message())
    replacement = backup(company)
    approval_routing.reassign(
        coordinator,
        item.id,
        {
            "expected_revision": item.revision,
            "approver_id": replacement.id,
            "reason": "Synthetic reassignment",
        },
    )
    with pytest.raises(PermissionDenied):
        authorize(conversation, approver)
    assert event_payload(ChatEvent.objects.get(message=previous), approver) is None
    assert (
        event_payload(ChatEvent.objects.get(message=previous), replacement.user)
        is not None
    )
    revoked = ChatEvent.objects.filter(
        conversation=conversation,
        kind="conversation.access_revoked",
        data__user_id=str(approver.id),
    ).last()
    assert event_payload(revoked, approver)["type"] == "conversation.access_revoked"
    assert (
        authenticated(approver)
        .get(f"/api/v1/chat/conversations/{conversation.id}/messages/")
        .status_code
        == 403
    )


@pytest.mark.django_db
def test_company_role_loss_revokes_private_attachments_and_delayed_notifications(
    company_setup, settings, tmp_path
):
    from core_apps.chat.tests.test_group_media import image_file

    _, coordinator, approver, company = company_setup[:4]
    item = proposed(company_setup)
    conversation = Conversation.objects.get(company_request=item.request)
    settings.CHAT_PRIVATE_MEDIA_ROOT = str(tmp_path)
    image = upload_attachment(
        conversation, coordinator, image_file(), uuid.uuid4(), "image"
    )
    sent = send_group_message(
        conversation,
        coordinator,
        {
            **message("Internal evidence"),
            "kind": "image",
            "attachment_ids": [str(image.id)],
        },
    )
    assert (
        accessible_attachment(conversation, approver, identity=image.id).id == image.id
    )
    member = CompanyMembership.objects.get(company=company, user=approver)
    membership.update_member(
        coordinator,
        company.id,
        member.id,
        {
            "expected_revision": member.revision,
            "roles": [],
            "is_active": False,
            "reason": "Offboarded",
        },
    )
    with pytest.raises(PermissionDenied):
        accessible_attachment(conversation, approver, identity=image.id)
    with patch(
        "core_apps.chat.services.group_outbox.get_channel_layer", return_value=None
    ):
        assert deliver_event(ChatEvent.objects.get(message=sent).pk)
    assert not ChatNotificationDelivery.objects.filter(
        event__message=sent, user=approver
    ).exists()
    item.refresh_from_db()
    assert item.status == "approval_pending"


@pytest.mark.django_db(transaction=True)
def test_concurrent_case_send_uses_one_canonical_message(company_setup):
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL locking evidence")
    item = proposed(company_setup)
    conversation = Conversation.objects.get(company_request=item.request)
    payload = message()
    results = parallel_calls(
        lambda _: send_group_message(conversation, company_setup[1], payload).id
    )
    assert results[0] == results[1]
    assert (
        Message.objects.filter(
            conversation=conversation, client_message_id=payload["client_message_id"]
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_company_chat_tools_keep_coordinator_and_personal_boundaries(company_setup):
    from core_apps.chat.services.message_tools import set_message_tool
    from core_apps.chat.services.polls import change_poll
    from core_apps.chat.services.quick_replies import save, listing
    _, coordinator, approver, company = company_setup[:4]
    conversation = Conversation.objects.get(company_request=company_setup[-1])
    resource = send_group_message(conversation, coordinator, message('Pinned company note'))
    projection = summary(conversation, coordinator)
    assert projection['supports_polls'] and projection['supports_quick_replies']
    body = {'membership_period': projection['membership_period'], 'operation_id': str(uuid.uuid4()), 'enabled': True}
    assert set_message_tool(conversation, coordinator, resource.id, body, pin=True)['pinned_messages']
    save(coordinator, uuid.uuid4(), {'title':'Private','content':'My template','expected_revision':0})
    assert not listing(approver)
    poll = send_group_message(conversation, coordinator, {**message(), 'kind':'poll', 'poll':{'question':'Choose','options':['A','B']}})
    voted = change_poll(conversation, coordinator, poll.id, {**body, 'operation_id':str(uuid.uuid4()), 'option_ids':[poll.poll.options[0]['id']]})
    assert voted['poll']['voter_count'] == 1
    CompanyMembership.objects.filter(company=company, user=coordinator).update(is_active=False)
    with pytest.raises(PermissionDenied):
        set_message_tool(conversation, coordinator, resource.id, {**body,'operation_id':str(uuid.uuid4())},pin=True)
