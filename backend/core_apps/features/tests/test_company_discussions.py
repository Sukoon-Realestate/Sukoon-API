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
