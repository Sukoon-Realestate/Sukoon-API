"""Older ORM writes remain readable after additive metadata migrations.

This covers schema compatibility only. Downgrading the storage implementation
or financial/provider policy still requires separate release acceptance.
"""

import hashlib
import uuid

import pytest
from django.core.files.base import ContentFile
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from core_apps.features.models import RentalEvidence
from core_apps.support.models import TicketAttachment
from core_apps.support.services import create_ticket
from core_apps.support.tests.test_private_attachments import upload

pytestmark = pytest.mark.django_db


def historical_model(app, migration, model):
    return MigrationExecutor(connection).loader.project_state(
        [(app, migration)]
    ).apps.get_model(app, model)


def test_pre_digest_writer_retains_private_attachment_and_current_reader(user, auth_client):
    ticket = create_ticket(user, "tenant", "other", "Rollback QA", "Synthetic only")
    original = upload().read()
    previous = historical_model("support", "0006_private_attachments", "TicketAttachment")
    old = previous.objects.create(
        message_id=ticket.messages.first().pk,
        name="synthetic.png",
        private_file=ContentFile(original, name="synthetic.png"),
    )
    current = TicketAttachment.objects.get(pk=old.pk)
    assert current.content_sha256 is None
    with current.private_file.open("rb") as source:
        assert source.read() == original
    response = auth_client.get(current.file_url, {"workspace": "tenant"})
    assert response.status_code == 200
    assert response["Cache-Control"] == "private, no-store"
    assert b"".join(response.streaming_content).startswith(b"\xff\xd8")
    assert auth_client.get(current.file_url, {"workspace": "owner"}).status_code == 404
    current.refresh_from_db()
    assert current.content_sha256 is None  # Reading does not invent verification.


def test_pre_inspection_writer_retains_pending_evidence_bytes_and_identity(user):
    previous = historical_model(
        "features", "0062_companysavedlist_companysaveditem_and_more", "RentalEvidence"
    )
    content = b"synthetic evidence for schema compatibility only"
    key = uuid.uuid4()
    old = previous.objects.create(
        uploader_id=user.pk,
        purpose="student",
        request_key=key,
        original_name="synthetic.txt",
        content_type="text/plain",
        size_bytes=len(content),
        sha256=hashlib.sha256(content).hexdigest(),
        storage_provider="database",
        storage_key=f"schema-qa/{key}",
        private_content=content,
    )
    current = RentalEvidence.objects.get(pk=old.pk)
    assert current.id == old.id and current.request_key == key
    assert bytes(current.private_content) == content
    assert current.sha256 == hashlib.sha256(content).hexdigest()
    assert current.malware_status == RentalEvidence.MalwareStatus.PENDING
    assert current.scan_engine is current.scan_sha256 is current.scan_error_code is None
    assert current.scan_token is current.scan_until is None
