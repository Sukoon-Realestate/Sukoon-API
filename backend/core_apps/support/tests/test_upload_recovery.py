import hashlib
import uuid
from datetime import timedelta

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient

from core_apps.support.models import TicketAttachment
from core_apps.support.services.staged_attachments import scan_pending
from core_apps.support.storage import SupportPrivateStorage
from .test_staged_media import media, pdf
from .test_durable_storage import durable

pytestmark = pytest.mark.django_db


def staged(user):
    content = pdf()
    api = APIClient()
    api.force_authenticate(user)
    response = api.post(
        "/api/v1/support/uploads/",
        {
            "workspace": "tenant",
            "client_upload_id": str(uuid.uuid4()),
            "creation_request_key": str(uuid.uuid4()),
            "file": SimpleUploadedFile(
                "proof.pdf", content, content_type="application/pdf"
            ),
        },
        format="multipart",
    )
    assert response.status_code == 201, response.content
    return api, TicketAttachment.objects.get(id=response.json()["data"]["id"]), content


def test_retry_after_remote_success_and_lost_response_has_one_object(
    user, media, durable, monkeypatch
):
    api, item, content = staged(user)
    original = SupportPrivateStorage.ensure_remote
    calls = 0

    def lost_response(storage, name):
        nonlocal calls
        digest = original(storage, name)
        calls += 1
        if calls == 1:
            raise OSError("synthetic lost response after durable storage")
        return digest

    monkeypatch.setattr(SupportPrivateStorage, "ensure_remote", lost_response)
    assert scan_pending()["scanned"] == 0
    item.refresh_from_db()
    assert item.status == "pending" and bytes(item.private_content) == content
    first_name = item.private_file.name
    assert len(durable) == 1
    TicketAttachment.objects.filter(pk=item.pk).update(
        scan_until=timezone.now() - timedelta(seconds=1)
    )
    assert scan_pending()["scanned"] == 1
    item.refresh_from_db()
    assert item.status == "ready" and item.private_file.name == first_name
    assert len(durable) == 1
    assert item.content_sha256 == hashlib.sha256(content).hexdigest()
    assert (
        api.get(f"/api/v1/support/attachments/{item.id}/?workspace=tenant").status_code
        == 404
    )


def test_late_scan_cannot_delete_a_newer_workers_ready_file(
    user, media, durable, monkeypatch
):
    _, item, content = staged(user)
    original = SupportPrivateStorage.save_immutable

    def newer_worker(storage, name, data, digest):
        result = original(storage, name, data, digest)
        TicketAttachment.objects.filter(pk=item.pk).update(
            status="ready", scan_token=uuid.uuid4(), scan_until=None
        )
        return result

    monkeypatch.setattr(SupportPrivateStorage, "save_immutable", newer_worker)
    scan_pending()
    item.refresh_from_db()
    assert item.status == "ready"
    assert item.private_file.read() == content
    item.private_file.close()
    assert len(durable) == 1


def test_cancelled_upload_cleanup_retries_without_scanner(
    user, media, durable, settings, monkeypatch
):
    api, item, _ = staged(user)
    scan_pending()
    item.refresh_from_db()
    assert item.status == "ready" and len(durable) == 1
    path = f"/api/v1/support/uploads/{item.client_upload_id}/"
    assert api.delete(path).status_code == 204
    assert api.delete(path).status_code == 204
    settings.EVIDENCE_SCANNER_BACKEND = "disabled"
    from core_apps.virtual_tours import cloudinary_storage

    original = cloudinary_storage.remove
    with monkeypatch.context() as patch:
        patch.setattr(
            cloudinary_storage,
            "remove",
            lambda *args, **kwargs: (_ for _ in ()).throw(OSError("offline")),
        )
        scan_pending()
        item.refresh_from_db()
        assert item.private_file.name and item.private_content is None
    scan_pending()
    item.refresh_from_db()
    assert item.status == "expired" and not item.private_file.name
    assert not durable


def test_upload_identity_is_bound_to_owner_context_and_digest(
    user, another_user, media
):
    api, item, content = staged(user)
    changed = api.post(
        "/api/v1/support/uploads/",
        {
            "workspace": "owner",
            "client_upload_id": str(item.client_upload_id),
            "creation_request_key": str(item.creation_request_key),
            "file": SimpleUploadedFile(
                "proof.pdf", content, content_type="application/pdf"
            ),
        },
        format="multipart",
    )
    assert changed.status_code == 400
    api.force_authenticate(another_user)
    assert (
        api.get(f"/api/v1/support/uploads/{item.client_upload_id}/").status_code == 404
    )
    assert (
        api.delete(f"/api/v1/support/uploads/{item.client_upload_id}/").status_code
        == 404
    )
    assert TicketAttachment.objects.count() == 1


def test_pdf_annotation_action_is_rejected():
    import io
    from pypdf import PdfWriter
    from pypdf.generic import (
        ArrayObject,
        DictionaryObject,
        NameObject,
        TextStringObject,
    )
    from rest_framework.exceptions import ValidationError
    from core_apps.common.private_media_policy import inspect

    writer = PdfWriter()
    page = writer.add_blank_page(width=100, height=100)
    page[NameObject("/Annots")] = ArrayObject(
        [
            DictionaryObject(
                {
                    NameObject("/A"): DictionaryObject(
                        {
                            NameObject("/S"): NameObject("/JavaScript"),
                            NameObject("/JS"): TextStringObject("app.alert(1)"),
                        }
                    )
                }
            )
        ]
    )
    output = io.BytesIO()
    writer.write(output)
    with pytest.raises(ValidationError):
        inspect(output.getvalue(), "application/pdf")


def test_disabled_inspection_is_reported_and_rejects_new_uploads(user, settings):
    settings.EVIDENCE_SCANNER_BACKEND = "disabled"
    api = APIClient()
    api.force_authenticate(user)
    policy = api.get("/api/v1/support/attachment-policy/").json()["data"]
    assert policy["available"] is False
    assert policy["blocking_reasons"] == ["private_media_inspection_unavailable"]
    response = api.post(
        "/api/v1/support/uploads/",
        {
            "workspace": "tenant",
            "client_upload_id": str(uuid.uuid4()),
            "creation_request_key": str(uuid.uuid4()),
            "file": SimpleUploadedFile(
                "proof.pdf", pdf(), content_type="application/pdf"
            ),
        },
        format="multipart",
    )
    assert response.status_code == 403
    assert not TicketAttachment.objects.exists()
