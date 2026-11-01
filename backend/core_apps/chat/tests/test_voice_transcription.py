import uuid
from unittest.mock import patch
import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from core_apps.chat.models import ChatAttachment, Message, VoiceTranscription
from core_apps.chat.services.transcription import (
    request_transcription,
    process_one,
    payload,
)
from core_apps.chat.services.group_media_storage import private_path


@pytest.fixture
def voice(chat_group, settings):
    group, conversation, user, other = chat_group
    settings.CHAT_TRANSCRIPTION_ENABLED = True
    settings.CHAT_MODERATION_PRIVATE_INPUTS_APPROVED = True
    settings.GEMINI_API_KEY = "test-only-never-sent"
    settings.CHAT_TRANSCRIPTION_MODEL = "gemini-test"
    message = Message.objects.create(
        conversation=conversation, sender=user, content="", kind="voice", sequence=1
    )
    attachment = ChatAttachment.objects.create(
        conversation=conversation,
        uploader=user,
        membership_period=uuid.uuid4(),
        client_upload_id=uuid.uuid4(),
        kind="voice",
        state="attached",
        fingerprint="a" * 64,
        storage_key=f"{uuid.uuid4()}.m4a",
        mime_type="audio/mp4",
        byte_size=4,
        duration_ms=3000,
        message=message,
    )
    path = private_path(attachment.storage_key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"test")
    return attachment, user, other


@pytest.mark.django_db
def test_deduplication_encryption_and_deletion(voice):
    attachment, user, other = voice
    assert request_transcription(attachment, user)["state"] == "queued"
    assert request_transcription(attachment, other)["state"] == "queued"
    assert VoiceTranscription.objects.count() == 1
    with patch(
        "core_apps.chat.services.transcription.GeminiReviewer._call",
        return_value={"text": "مرحبا بك", "intelligible": True},
    ) as call:
        assert process_one()
        assert not process_one()
        assert call.call_count == 1
    job = VoiceTranscription.objects.get()
    assert "مرحبا" not in job.ciphertext
    assert payload(job)["text"] == "مرحبا بك"
    client = APIClient()
    client.force_authenticate(other)
    url = f"/api/v1/chat/conversations/{attachment.conversation.id}/attachments/{attachment.id}/transcription/"
    assert client.get(url).status_code == 200
    attachment.message.deleted_at = timezone.now()
    attachment.message.save()
    assert client.get(url).status_code == 404
    process_one()
    assert not VoiceTranscription.objects.exists()


@pytest.mark.django_db
def test_unavailable_provider_never_enqueues(voice, settings):
    attachment, user, _ = voice
    settings.CHAT_TRANSCRIPTION_ENABLED = False
    assert request_transcription(attachment, user)["state"] == "unavailable"
    assert not VoiceTranscription.objects.exists()


@pytest.mark.django_db
def test_private_access_and_provider_failure(voice, superuser):
    attachment, user, _ = voice
    client = APIClient()
    client.force_authenticate(superuser)
    url = f"/api/v1/chat/conversations/{attachment.conversation.id}/attachments/{attachment.id}/transcription/"
    assert client.post(url, {}, format="json").status_code in {403, 404}
    request_transcription(attachment, user)
    with patch(
        "core_apps.chat.services.transcription.GeminiReviewer._call",
        side_effect=RuntimeError("private error must not escape"),
    ):
        process_one()
    job = VoiceTranscription.objects.get()
    assert job.state == "failed"
    assert job.error_code == "transcription_failed"
    assert job.ciphertext == ""
