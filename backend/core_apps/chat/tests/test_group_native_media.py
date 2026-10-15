"""Optional native evidence: use actual device recordings, never synthetic claims.

Set CHAT_NATIVE_ANDROID_CLIP / CHAT_NATIVE_IOS_CLIP to private QA recordings.
The files and authenticated binary responses are not checked into source control.
"""

import os
import uuid
from pathlib import Path
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from .conftest import message_request

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("platform", ["ANDROID", "IOS"])
def test_native_recording_upload_send_and_other_member_download(
    chat_group, api_client, platform
):
    path = os.environ.get(f"CHAT_NATIVE_{platform}_CLIP")
    if not path:
        pytest.skip(f"Provide CHAT_NATIVE_{platform}_CLIP from the native voice spike")
    _, conversation, sender, recipient = chat_group
    body = Path(path).read_bytes()
    api_client.force_authenticate(sender)
    base = f"/api/v1/chat/conversations/{conversation.id}/"
    upload = api_client.post(
        base + "attachments/",
        {
            "client_upload_id": str(uuid.uuid4()),
            "kind": "voice",
            "file": SimpleUploadedFile("native.m4a", body, content_type="audio/mp4"),
        },
        format="multipart",
    )
    assert upload.status_code == 201, upload.data
    attachment = upload.json()["data"]
    assert attachment["mime_type"] == "audio/mp4"
    assert 1000 <= attachment["duration_ms"] <= 120000
    sent = api_client.post(
        base + "messages/create/",
        message_request("", kind="voice", attachment_ids=[attachment["id"]]),
        format="json",
    )
    assert sent.status_code == 201, sent.data
    api_client.force_authenticate(recipient)
    download = api_client.get("/api/v1/" + attachment["content_path"])
    assert download.status_code == 200
    assert b"".join(download.streaming_content) == body
    assert download["Cache-Control"] == "private, no-store"
