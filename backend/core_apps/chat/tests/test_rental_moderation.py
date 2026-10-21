"""Provider judgments are fixtures; policy, storage, transport and receipts are real."""

import uuid
from datetime import timedelta
from unittest.mock import patch
import pytest
from django.utils import timezone
from rest_framework.exceptions import APIException
from rest_framework.test import APIClient
from core_apps.chat.models import (
    RentalChatContext,
    ChatModerationInput,
    ChatModerationBatch,
    ChatModerationCase,
    ChatPolicyConsent,
    ChatPolicyNotice,
    AccountRestriction,
    Message,
)
from core_apps.chat.services.message_service import (
    get_or_create_direct_conversation,
    send_message,
)
from core_apps.chat.moderation.policy import VERSION, require_send, restricted
from core_apps.chat.moderation.queue import (
    process_one,
    claim,
    validated_verdicts,
    enqueue,
)
from core_apps.chat.moderation.decisions import acknowledge, appeal, review, complete
from core_apps.chat.moderation.provider import ProviderUnavailable
from core_apps.chat.moderation.sealed import unseal

pytestmark = pytest.mark.django_db


@pytest.fixture
def rental_chat(user, another_user, settings):
    settings.CHAT_MODERATION_MODE = "enforce"
    for p in (user, another_user):
        p.is_verified = True
        p.save(update_fields=["is_verified"])
    chat = get_or_create_direct_conversation(user=user, other_user=another_user)
    RentalChatContext.objects.create(conversation=chat, owner=user)
    for p in (user, another_user):
        ChatPolicyConsent.objects.create(user=p, version=VERSION)
    return chat, user, another_user


class Reviewer:
    model, label, calls = "fixture", "circumvention", 0

    def __init__(self, heartbeat):
        self.heartbeat = heartbeat

    def classify(self, messages, verify=False):
        Reviewer.calls += 1
        self.heartbeat()
        latest = [m for m in messages if m["new"]][-1]
        return {
            "verdicts": [
                {
                    "actor_id": latest["actor_id"],
                    "label": self.label,
                    "confidence": 0.99,
                    "evidence": [
                        {
                            "message_id": latest["message_id"],
                            "source": "text",
                            "quote": latest["text"],
                        }
                    ],
                }
            ]
        }


def send(chat, user, text="Let us pay privately outside Sokoun to avoid its fees."):
    return send_message(
        conversation=chat, sender=user, content=text, client_message_id=uuid.uuid4()
    )


def due():
    ChatModerationInput.objects.filter(state="pending").update(
        due_at=timezone.now() - timedelta(seconds=1)
    )


def run():
    due()
    assert process_one(Reviewer)
    batch = ChatModerationBatch.objects.latest("created_at")
    assert batch.state == "complete", batch.diagnostics
    return batch


def test_first_dirty_window_idempotency_idle_and_encryption(rental_chat):
    chat, user, _ = rental_chat
    message = send(chat, user)
    row = ChatModerationInput.objects.get()
    assert message.content not in row.ciphertext
    assert unseal(row.ciphertext)["text"] == message.content
    enqueue(message)
    send(chat, user, "Some new details")
    assert ChatModerationInput.objects.count() == 2
    assert {r.due_at for r in ChatModerationInput.objects.all()} == {row.due_at}
    assert process_one(Reviewer) is False
    Reviewer.calls = 0
    run()
    count = Reviewer.calls
    assert process_one(Reviewer) is False and Reviewer.calls == count


def test_warning_ack_repeat_only_actor_and_admin_release(rental_chat, superuser):
    chat, user, other = rental_chat
    send(chat, user)
    run()
    notice = ChatPolicyNotice.objects.get(kind="warning")
    assert notice.user == user and not restricted(user) and not restricted(other)
    with pytest.raises(APIException) as error:
        send(chat, user, "acknowledge first")
    assert error.value.status_code == 403
    require_send(chat, other)
    unread = chat.participant_set.get(user=other).unread_count
    acknowledge(user, chat, {"policy_version": VERSION, "notice_id": notice.id})
    assert chat.participant_set.get(user=other).unread_count == unread
    send(chat, user)
    run()
    assert restricted(user) and not restricted(other)
    user.refresh_from_db()
    assert user.is_active
    case = ChatModerationCase.objects.get(state="pending_review")
    key = uuid.uuid4()
    explanation = "This was a misunderstanding, please review the context."
    result = appeal(user, case.id, key, explanation)
    assert result["appeal_submitted"]
    assert appeal(user, case.id, key, explanation)["revision"] == result["revision"]
    with pytest.raises(APIException):
        appeal(other, case.id, uuid.uuid4(), explanation)
    with pytest.raises(APIException):
        review(superuser, case.id, uuid.uuid4(), 1, "release", explanation)
    action = uuid.uuid4()
    final = review(
        superuser, case.id, action, result["revision"], "release", explanation
    )
    assert final["state"] == "released" and not restricted(user)
    assert (
        review(superuser, case.id, action, result["revision"], "release", explanation)[
            "revision"
        ]
        == final["revision"]
    )
    assert case.actions.count() == 1


@pytest.mark.parametrize("label", ["compliant", "off_topic", "uncertain"])
def test_non_violation_never_restricts(rental_chat, label):
    chat, user, _ = rental_chat
    send(chat, user, "Call 01012345678 for directions; we will pay in Sokoun.")
    with patch.object(Reviewer, "label", label):
        run()
    assert not AccountRestriction.objects.exists()
    assert not ChatPolicyNotice.objects.filter(kind="warning").exists()
    assert ChatModerationCase.objects.filter(state="review").count() == (
        1 if label == "uncertain" else 0
    )


def test_provider_down_retains_retry_and_never_sanctions(rental_chat):
    chat, user, _ = rental_chat
    send(chat, user)
    due()
    with patch.object(
        Reviewer, "classify", side_effect=ProviderUnavailable("provider_http_429")
    ):
        assert process_one(Reviewer)
    assert ChatModerationBatch.objects.get().state == "retry"
    assert not ChatModerationCase.objects.exists() and not process_one(Reviewer)
    ChatModerationBatch.objects.update(
        next_attempt_at=timezone.now() - timedelta(seconds=1)
    )
    assert process_one(Reviewer)
    assert ChatPolicyNotice.objects.count() == 1


def test_expired_worker_is_fenced_and_inputs_retained(rental_chat):
    chat, user, _ = rental_chat
    send(chat, user)
    due()
    old = claim()
    ChatModerationBatch.objects.filter(pk=old.pk).update(
        lease_until=timezone.now() - timedelta(seconds=1)
    )
    replacement = claim()
    assert old.pk == replacement.pk and old.lease_token != replacement.lease_token
    with pytest.raises(ProviderUnavailable):
        complete(old, [], [], [], "fixture")
    assert not ChatModerationCase.objects.exists()


def test_deleted_message_during_analysis_cannot_warn(rental_chat):
    chat, user, _ = rental_chat
    message = send(chat, user)
    old = Reviewer.classify

    def classify(self, messages, verify=False):
        result = old(self, messages, verify=verify)
        Message.objects.filter(pk=message.pk).update(
            deleted_at=timezone.now(), revision=2
        )
        return result

    with patch.object(Reviewer, "classify", classify):
        run()
    assert (
        not ChatPolicyNotice.objects.filter(kind="warning").exists()
        and not AccountRestriction.objects.exists()
    )


def test_forged_evidence_and_innocent_recipient_rejected(rental_chat):
    chat, user, other = rental_chat
    message = send(chat, user)
    sample = unseal(ChatModerationInput.objects.get().ciphertext)
    sample.update(new=True, media=[])
    raw = {
        "verdicts": [
            {
                "actor_id": str(other.id),
                "label": "circumvention",
                "confidence": 0.99,
                "evidence": [
                    {
                        "message_id": str(message.id),
                        "source": "text",
                        "quote": message.content,
                    }
                ],
            }
        ]
    }
    with pytest.raises(ProviderUnavailable):
        validated_verdicts(raw, [sample])
    raw["verdicts"][0]["actor_id"] = str(user.id)
    raw["verdicts"][0]["evidence"][0]["quote"] = "invented evidence"
    with pytest.raises(ProviderUnavailable):
        validated_verdicts(raw, [sample])


def test_policy_api_authorization_ack_and_legacy_send_gate(rental_chat, superuser):
    chat, user, _ = rental_chat
    client = APIClient()
    client.force_authenticate(user)
    ChatPolicyConsent.objects.filter(user=user).delete()
    base = f"/api/v1/chat/conversations/{chat.id}/"
    response = client.get(base + "chat/")
    assert response.status_code == 200, response.data
    assert response.data["policy"]["consent_required"]
    assert (
        client.post(
            base + "messages/create/", {"content": "hello"}, format="json"
        ).status_code
        == 403
    )
    assert (
        client.post(
            base + "policy/", {"policy_version": VERSION}, format="json"
        ).status_code
        == 200
    )
    assert client.get(base + "chat/").data["policy"]["consent_required"] is False
    client.force_authenticate(superuser)
    assert client.get(base + "policy/").status_code == 403


def test_shadow_mode_generates_no_notices(rental_chat, settings):
    settings.CHAT_MODERATION_MODE = "shadow"
    chat, user, _ = rental_chat
    send(chat, user)
    run()
    assert (
        not ChatModerationCase.objects.exists()
        and not AccountRestriction.objects.exists()
    )


def test_property_visibility_new_business_and_original_publication_survive(
    rental_chat, superuser
):
    from core_apps.virtual_tours.tests.conftest import property_obj as fixture
    from core_apps.chat.moderation.policy import (
        visible_properties,
        require_new_business,
    )
    from core_apps.properties.models import Property
    from core_apps.properties.serializers import PropertyDetailSerializer
    from types import SimpleNamespace

    chat, user, other = rental_chat
    prop = fixture.__wrapped__(user)
    send(chat, user)
    run()
    notice = ChatPolicyNotice.objects.get(kind="warning")
    acknowledge(user, chat, {"policy_version": VERSION, "notice_id": notice.id})
    send(chat, user)
    run()
    case = ChatModerationCase.objects.get(state="pending_review")
    assert not visible_properties(Property.objects.all()).filter(pk=prop.pk).exists()
    payload = PropertyDetailSerializer(
        prop, context={"request": SimpleNamespace(user=other)}
    ).data
    assert payload["status"] == "policy_blocked"
    assert "owner" not in payload and "rental_inventory" not in payload
    prop.refresh_from_db()
    assert prop.status == "verified"
    with pytest.raises(APIException):
        require_new_business(user)
    require_new_business(other)
    review(
        superuser,
        case.id,
        uuid.uuid4(),
        case.revision,
        "release",
        "Verified context does not justify continued restriction.",
    )
    assert visible_properties(Property.objects.all()).filter(pk=prop.pk).exists()
    assert prop.status == "verified"


def test_notice_is_durable_without_chat_unread_inflation(rental_chat):
    from core_apps.notifications.models import Notification

    chat, user, other = rental_chat
    send(chat, user)
    before = chat.participant_set.get(user=other).unread_count
    run()
    case = ChatModerationCase.objects.get()
    assert case.notification is not None
    assert case.notification.user == user
    assert case.notification.category == "account_policy"
    assert chat.participant_set.get(user=other).unread_count == before
    assert not process_one(Reviewer)
    assert Notification.objects.filter(category="account_policy").count() == 1


def test_private_provider_gate_precedes_any_request_or_quota_reservation(
    rental_chat, settings
):
    from core_apps.chat.moderation.provider import GeminiReviewer
    from core_apps.chat.models import GeminiUsageReservation

    settings.CHAT_MODERATION_PRIVATE_INPUTS_APPROVED = False
    with patch("core_apps.chat.moderation.provider.requests.post") as request:
        with pytest.raises(ProviderUnavailable, match="private_input_gate"):
            GeminiReviewer().classify([])
    request.assert_not_called()
    assert not GeminiUsageReservation.objects.exists()


def test_scope_cannot_be_forged_and_old_content_is_not_enqueued(rental_chat):
    from core_apps.chat.moderation.policy import attach_context

    chat, user, other = rental_chat
    with pytest.raises(APIException):
        attach_context(chat, user, {"property_id": str(uuid.uuid4())})
    with pytest.raises(APIException):
        attach_context(chat, user, {"property_id": "invalid"})
    Message.objects.create(
        conversation=chat, sender=user, content="Old unreviewed history"
    )
    assert not ChatModerationInput.objects.exists()


@pytest.mark.django_db(transaction=True)
def test_postgres_moderation_claims_are_exclusive(user, another_user, settings):
    from concurrent.futures import ThreadPoolExecutor
    from django.db import connection, close_old_connections
    from threading import Barrier

    if connection.vendor != "postgresql":
        pytest.skip("Real row-lock proof requires PostgreSQL")
    settings.CHAT_MODERATION_MODE = "shadow"
    chat = get_or_create_direct_conversation(user=user, other_user=another_user)
    RentalChatContext.objects.create(conversation=chat, owner=user)
    ChatPolicyConsent.objects.create(user=user, version=VERSION)
    send(chat, user)
    due()
    barrier = Barrier(2)

    def worker():
        close_old_connections()
        try:
            barrier.wait(timeout=5)
            value = claim()
            return value.pk if value else None
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: worker(), range(2)))
    assert len([result for result in results if result is not None]) == 1
    assert ChatModerationBatch.objects.count() == 1


def test_admin_original_media_is_case_scoped_and_private(
    rental_chat, superuser, settings, tmp_path
):
    from core_apps.chat.models import ChatAttachment
    from core_apps.chat.moderation.sealed import seal
    from core_apps.chat.services.group_media_storage import private_path

    chat, user, other = rental_chat
    settings.CHAT_PRIVATE_MEDIA_ROOT = tmp_path / "private"
    message = send(chat, user)
    run()
    case = ChatModerationCase.objects.get()
    attachment = ChatAttachment.objects.create(
        conversation=chat,
        uploader=user,
        membership_period=uuid.uuid4(),
        client_upload_id=uuid.uuid4(),
        kind="image",
        state="attached",
        fingerprint="a" * 64,
        storage_key="case-test.jpg",
        mime_type="image/jpeg",
        byte_size=4,
        message=message,
    )
    path = private_path(attachment.storage_key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"test")
    data = unseal(case.evidence_ciphertext)
    data["messages"][0]["media"] = [
        {"source": str(attachment.id), "text": "readable fixture", "uncertain": False}
    ]
    case.evidence_ciphertext = seal(data)
    case.save()
    client = APIClient()
    url = f"/api/v1/chat/admin/policy-cases/{case.id}/attachments/{attachment.id}/"
    client.force_authenticate(user)
    assert client.get(url).status_code == 403
    client.force_authenticate(superuser)
    response = client.get(url)
    assert response.status_code == 200
    assert response["Cache-Control"] == "private, no-store"
    assert b"".join(response.streaming_content) == b"test"
    data["messages"][0]["media"] = []
    case.evidence_ciphertext = seal(data)
    case.save()
    assert client.get(url).status_code == 404


@pytest.mark.parametrize("finish", ["MAX_TOKENS", "SAFETY", None])
def test_incomplete_provider_response_cannot_be_used(rental_chat, settings, finish):
    from core_apps.chat.moderation.provider import GeminiReviewer

    settings.CHAT_MODERATION_PRIVATE_INPUTS_APPROVED = True
    settings.GEMINI_API_KEY = "synthetic-test-key"
    with patch("core_apps.chat.moderation.provider.requests.post") as call:
        call.return_value.status_code = 200
        call.return_value.json.return_value = {
            "candidates": [
                {
                    "finishReason": finish,
                    "content": {"parts": [{"text": '{"verdicts": []}'}]},
                }
            ]
        }
        with pytest.raises(ProviderUnavailable, match="provider_incomplete_response"):
            GeminiReviewer().classify([])
    assert not ChatModerationCase.objects.exists()


def test_provider_ignores_thought_parts_and_reports_timeout(rental_chat, settings):
    import requests
    from core_apps.chat.moderation.provider import GeminiReviewer

    settings.CHAT_MODERATION_PRIVATE_INPUTS_APPROVED = True
    settings.GEMINI_API_KEY = "synthetic-test-key"
    with patch("core_apps.chat.moderation.provider.requests.post") as call:
        call.return_value.status_code = 200
        call.return_value.json.return_value = {
            "candidates": [
                {
                    "finishReason": "STOP",
                    "content": {
                        "parts": [
                            {"thought": True, "text": "Untrusted hidden commentary"},
                            {"text": '{"verdicts": []}'},
                        ]
                    },
                }
            ]
        }
        assert GeminiReviewer().classify([]) == {"verdicts": []}
        call.side_effect = requests.ReadTimeout()
        with pytest.raises(ProviderUnavailable, match="provider_timeout"):
            GeminiReviewer().classify([])


def test_status_is_staff_only_and_contains_no_message_content(rental_chat, superuser):
    chat, user, _ = rental_chat
    message = send(chat, user)
    client = APIClient()
    client.force_authenticate(user)
    assert client.get("/api/v1/chat/admin/policy-status/").status_code == 403
    client.force_authenticate(superuser)
    response = client.get("/api/v1/chat/admin/policy-status/")
    assert response.status_code == 200
    assert response.data["pending"]["count"] == 1
    assert message.content.encode() not in response.content


def test_retention_expires_backlog_but_preserves_live_lease_and_review(rental_chat):
    from core_apps.chat.management.commands.run_chat_policy_worker import purge

    chat, user, _ = rental_chat
    send(chat, user)
    due()
    batch = claim()
    ChatModerationInput.objects.update(created_at=timezone.now() - timedelta(days=8))
    ChatModerationBatch.objects.update(created_at=timezone.now() - timedelta(days=8))
    purge()
    assert ChatModerationInput.objects.get().ciphertext
    ChatModerationBatch.objects.update(
        lease_until=timezone.now() - timedelta(seconds=1)
    )
    purge()
    assert ChatModerationInput.objects.get().ciphertext == ""
    batch.refresh_from_db()
    assert batch.state == "failed" and batch.lease_token is None
    assert not ChatModerationCase.objects.exists()
