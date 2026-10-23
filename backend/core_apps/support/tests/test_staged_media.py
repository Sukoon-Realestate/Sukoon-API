import io, uuid, hashlib
import pytest
from pypdf import PdfWriter
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError
from core_apps.common.private_media_policy import inspect
from core_apps.support.models import TicketAttachment
from core_apps.support.services.staged_attachments import scan_pending

pytestmark = pytest.mark.django_db


def pdf(encrypted=False):
    out = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    if encrypted:
        writer.encrypt("secret")
    writer.write(out)
    return out.getvalue()


@pytest.fixture
def media(settings):
    settings.EVIDENCE_STORAGE_PROVIDER = "database"
    settings.EVIDENCE_SCANNER_BACKEND = "fake"
    settings.RENTAL_RUNTIME_ENVIRONMENT = "test"
    settings.RENTAL_FAKE_PROVIDER_ALLOWED = True


def test_pdf_validation():
    assert inspect(pdf(), "application/pdf")["page_count"] == 1
    with pytest.raises(ValidationError):
        inspect(pdf(True), "application/pdf")
    with pytest.raises(ValidationError):
        inspect(b"%PDF-bad", "application/pdf")
    with pytest.raises(ValidationError):
        inspect(b"0000ftypbad", "video/mp4", student=True, deep=False)


def test_pdf_create_reply_recovery_and_private_download(user, another_user, media):
    api = APIClient()
    api.force_authenticate(user)
    key = str(uuid.uuid4())
    upload_id = str(uuid.uuid4())
    content = pdf()

    def upload(**context):
        return api.post(
            "/api/v1/support/uploads/",
            {
                "workspace": "tenant",
                "client_upload_id": str(uuid.uuid4()),
                "file": SimpleUploadedFile(
                    "proof.pdf", content, content_type="application/pdf"
                ),
                "sha256": hashlib.sha256(content).hexdigest(),
                **context,
            },
            format="multipart",
        )

    response = upload(creation_request_key=key)
    assert response.status_code == 201, response.content
    attachment = response.json()["data"]["id"]
    assert response.json()["data"]["status"] == "pending"
    payload = {
        "workspace": "tenant",
        "category": "other",
        "subject": "PDF proof",
        "description": "Detailed inquiry for support",
        "attachment_ids": [attachment],
    }
    assert (
        api.post(
            "/api/v1/support/tickets/", payload, format="json", HTTP_IDEMPOTENCY_KEY=key
        ).status_code
        == 400
    )
    assert scan_pending()["scanned"] == 1
    created = api.post(
        "/api/v1/support/tickets/", payload, format="json", HTTP_IDEMPOTENCY_KEY=key
    )
    assert created.status_code == 201, created.content
    ticket = created.json()["data"]["id"]
    response = upload(ticket_id=ticket)
    assert response.status_code == 201, response.content
    reply_attachment = response.json()["data"]["id"]
    scan_pending()
    reply_key = str(uuid.uuid4())
    url = f"/api/v1/support/tickets/{ticket}/replies/?workspace=tenant"
    response = api.post(
        url,
        {"body": "", "attachment_ids": [reply_attachment]},
        format="json",
        HTTP_IDEMPOTENCY_KEY=reply_key,
    )
    assert response.status_code == 200, response.content
    assert len(response.json()["data"]["messages"]) == 2
    response = api.post(
        url,
        {"body": "", "attachment_ids": [reply_attachment]},
        format="json",
        HTTP_IDEMPOTENCY_KEY=reply_key,
    )
    assert len(response.json()["data"]["messages"]) == 2
    receipt = api.post(
        f"/api/v1/support/tickets/{ticket}/reply-receipt/?workspace=tenant",
        {},
        format="json",
        HTTP_IDEMPOTENCY_KEY=reply_key,
    )
    assert receipt.json()["data"]["outcome"] == "acknowledged"
    downloaded = api.get(f"/api/v1/support/attachments/{attachment}/?workspace=tenant")
    assert downloaded.status_code == 200
    assert downloaded["Content-Type"] == "application/pdf"
    assert b"".join(downloaded.streaming_content) == content
    api.force_authenticate(another_user)
    assert (
        api.get(
            f"/api/v1/support/attachments/{attachment}/?workspace=tenant"
        ).status_code
        == 404
    )


def test_malformed_pdf_never_becomes_downloadable(user, media):
    api = APIClient()
    api.force_authenticate(user)
    response = api.post(
        "/api/v1/support/uploads/",
        {
            "workspace": "tenant",
            "client_upload_id": str(uuid.uuid4()),
            "creation_request_key": str(uuid.uuid4()),
            "file": SimpleUploadedFile(
                "bad.pdf", b"%PDF-invalid", content_type="application/pdf"
            ),
        },
        format="multipart",
    )
    assert response.status_code == 201
    scan_pending()
    item = TicketAttachment.objects.get(id=response.json()["data"]["id"])
    assert item.status == "failed"
    assert item.private_content is None
    assert (
        api.get(f"/api/v1/support/attachments/{item.id}/?workspace=tenant").status_code
        == 404
    )


def test_video_actual_inspection_and_student_rejection(tmp_path):
    import shutil, subprocess

    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg unavailable")
    path = tmp_path / "fault.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=teal:s=128x96:d=1",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(path),
        ],
        check=True,
    )
    content = path.read_bytes()
    metadata = inspect(content, "video/mp4")
    assert metadata["kind"] == "video"
    assert 0 < metadata["duration_ms"] <= 1100
    with pytest.raises(ValidationError):
        inspect(content, "video/mp4", student=True)


@pytest.mark.django_db(transaction=True)
def test_reply_timeout_fence_and_original_request_serialize(user, media):
    from django.db import connection

    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL row locks")
    from core_apps.support.services import create_ticket
    from core_apps.features.tests.test_cycle_concurrency import parallel_calls

    ticket = create_ticket(
        user,
        workspace="tenant",
        category="other",
        subject="Concurrent reply",
        description="A detailed inquiry for support",
    )
    key = str(uuid.uuid4())

    def operation(index):
        api = APIClient()
        api.force_authenticate(user)
        path = (
            f"/api/v1/support/tickets/{ticket.id}/"
            + ("replies/" if index == 0 else "reply-receipt/")
            + "?workspace=tenant"
        )
        return api.post(
            path,
            {"body": "One original reply"} if index == 0 else {},
            format="json",
            HTTP_IDEMPOTENCY_KEY=key,
        )

    responses = parallel_calls(operation)
    receipt = responses[1].json()["data"]
    assert receipt["outcome"] in {"acknowledged", "absent_final"}
    assert ticket.messages.count() == (2 if receipt["outcome"] == "acknowledged" else 1)


def test_operator_browser_session_upload_reply_and_private_download(user, media):
    from django.test import Client
    from core_apps.features.tests.test_rental_lifecycle_safety import operator
    from core_apps.support.services import create_ticket
    from core_apps.support.services.staff_replies import reply_as_staff

    agent = operator("support")
    ticket = create_ticket(
        user, "owner", "other", "Document review", "Review the attached document."
    )
    browser = Client()
    browser.force_login(agent)
    content = pdf()
    response = browser.post(
        "/api/v1/support/uploads/",
        {
            "workspace": "owner",
            "ticket_id": str(ticket.id),
            "client_upload_id": str(uuid.uuid4()),
            "file": SimpleUploadedFile(
                "reply.pdf", content, content_type="application/pdf"
            ),
        },
    )
    assert response.status_code == 201, response.content
    identity = response.json()["data"]["id"]
    assert scan_pending()["scanned"] == 1
    reply_as_staff(
        user=agent,
        ticket_id=ticket.id,
        body="Attached clarification",
        expected_revision=ticket.revision,
        request_key=str(uuid.uuid4()),
        attachment_ids=[identity],
    )
    response = browser.get(f"/api/v1/support/attachments/{identity}/")
    assert response.status_code == 200, response.content
    assert b"".join(response.streaming_content) == content
    agent.staff_profile.is_active = False
    agent.staff_profile.save(update_fields=["is_active"])
    assert browser.get(f"/api/v1/support/attachments/{identity}/").status_code == 404
