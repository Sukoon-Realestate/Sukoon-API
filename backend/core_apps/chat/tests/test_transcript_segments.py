import json
import os
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from core_apps.chat.models import ChatAttachment, Message, VoiceTranscription
from core_apps.chat.services.transcription import request_transcription, process_one, payload
from core_apps.chat.services.transcript_segments import validated_segments
from core_apps.chat.services.group_media_storage import private_path
from .test_direct_media import direct_chat

pytestmark = pytest.mark.django_db
SEGMENTS = [{"start_ms": 0, "end_ms": 1200, "text": "Fixture entrance"},
            {"start_ms": 1500, "end_ms": 2900, "text": "Meet upstairs"}]


@pytest.fixture
def direct_voice(direct_chat, settings, tmp_path):
    conversation, sender, reader = direct_chat
    settings.CHAT_TRANSCRIPTION_ENABLED = True
    settings.CHAT_MODERATION_PRIVATE_INPUTS_APPROVED = True
    settings.GEMINI_API_KEY = "mock-only"
    settings.CHAT_PRIVATE_MEDIA_ROOT = tmp_path
    message = Message.objects.create(conversation=conversation, sender=sender, content="", kind="voice", sequence=1)
    attachment = ChatAttachment.objects.create(conversation=conversation, uploader=sender,
        membership_period=uuid.uuid4(), client_upload_id=uuid.uuid4(), kind="voice", state="attached",
        fingerprint="b" * 64, storage_key=f"{uuid.uuid4()}.m4a", mime_type="audio/mp4",
        byte_size=4, duration_ms=3000, message=message)
    path = private_path(attachment.storage_key); path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(b"test")
    return attachment, sender, reader


@pytest.mark.parametrize("segments", [None, [], [{"start_ms": True, "end_ms": 10, "text": "bad"}],
    [{"start_ms": -1, "end_ms": 10, "text": "bad"}], [{"start_ms": 0, "end_ms": 3001, "text": "bad"}],
    [{"start_ms": 0, "end_ms": 2000, "text": "one"}, {"start_ms": 1000, "end_ms": 3000, "text": "two"}],
    [{"start_ms": 0.0, "end_ms": 1000, "text": "bad"}], [{"start_ms": 0, "end_ms": 1000, "text": " "}]])
def test_invalid_segment_set_falls_back_to_plain_text(segments):
    assert validated_segments(segments, 3000) == []


def test_encrypted_segments_authorized_search_and_deletion(direct_voice, superuser):
    attachment, sender, reader = direct_voice
    request_transcription(attachment, sender)
    with patch("core_apps.chat.services.transcription.GeminiReviewer._call", return_value={
        "text": "Fixture entrance. Meet upstairs", "intelligible": True, "segments": SEGMENTS}):
        assert process_one()
    job = VoiceTranscription.objects.get()
    assert "upstairs" not in job.ciphertext
    assert payload(job)["segments"] == SEGMENTS
    api = APIClient(); api.force_authenticate(reader)
    url = f"/api/v1/chat/conversations/{attachment.conversation.id}/attachments/{attachment.id}/transcription/"
    response = api.get(url)
    assert response.status_code == 200 and response.data["segments"] == SEGMENTS
    exported = os.environ.get("MVP_FIXTURE_DIR")
    if exported:
        (Path(exported) / "voice_transcript_segments.json").write_text(json.dumps(response.data), encoding="utf8")
    result = api.get("/api/v1/chat/messages/search/", {"q": "upstairs"})
    assert result.status_code == 200, result.content
    rows = result.json()["data"]["results"]
    assert len(rows) == 1 and rows[0]["transcripts"][0]["attachment_id"] == str(attachment.id)
    api.force_authenticate(superuser)
    assert api.get(url).status_code in {403, 404}
    assert not api.get("/api/v1/chat/messages/search/", {"q": "upstairs"}).json()["data"]["results"]
    api.force_authenticate(reader)
    attachment.state = "revoked"; attachment.save(update_fields=["state"])
    assert api.get(url).status_code == 404
    assert not api.get("/api/v1/chat/messages/search/", {"q": "upstairs"}).json()["data"]["results"]
    attachment.state = "attached"; attachment.save(update_fields=["state"])
    attachment.message.deleted_at = timezone.now(); attachment.message.save()
    assert not api.get("/api/v1/chat/messages/search/", {"q": "upstairs"}).json()["data"]["results"]


def test_invalid_provider_timing_preserves_searchable_plain_text(direct_voice):
    attachment, sender, reader = direct_voice
    request_transcription(attachment, sender)
    with patch("core_apps.chat.services.transcription.GeminiReviewer._call", return_value={
        "text": "Preserved plain wording", "intelligible": True,
        "segments": [{"start_ms": 0, "end_ms": 99999, "text": "invalid"}]}):
        process_one()
    value = payload(VoiceTranscription.objects.get())
    assert value["text"] == "Preserved plain wording" and value["segments"] == []
    api = APIClient(); api.force_authenticate(reader)
    assert len(api.get("/api/v1/chat/messages/search/", {"q": "preserved"}).json()["data"]["results"]) == 1
