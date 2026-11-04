import hashlib
import io
import json
import os
from pathlib import Path
from uuid import uuid4
import pytest
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from core_apps.support.models import TicketInformationRequest, TicketEvidenceSubmission, TicketAttachment
from core_apps.support.services.staged_attachments import scan_pending
from .test_information_requests import inquiry, command, answer

pytestmark = pytest.mark.django_db


@pytest.fixture
def private_media(settings, tmp_path):
    settings.SUPPORT_PRIVATE_STORAGE_PROVIDER = "local"
    settings.SUPPORT_PRIVATE_MEDIA_ROOT = tmp_path / "support"
    settings.EVIDENCE_STORAGE_PROVIDER = "database"
    settings.EVIDENCE_SCANNER_BACKEND = "fake"
    settings.RENTAL_RUNTIME_ENVIRONMENT = "test"
    settings.RENTAL_FAKE_PROVIDER_ALLOWED = True


def upload(api, user, ticket, color):
    api.force_authenticate(user)
    out = io.BytesIO(); Image.new("RGB", (30, 30), color).save(out, "PNG"); content = out.getvalue()
    response = api.post(reverse("support-upload"), {"workspace": "tenant", "ticket_id": str(ticket.id),
        "client_upload_id": str(uuid4()), "file": SimpleUploadedFile("proof.png", content, content_type="image/png"),
        "sha256": hashlib.sha256(content).hexdigest()}, format="multipart")
    assert response.status_code == 201, response.data
    assert scan_pending()["scanned"] == 1
    return response.data["id"]


def test_evidence_versions_keep_conflicts_and_never_decide_the_ticket(api_client, user, inquiry, private_media):
    ticket, staff = inquiry
    assert command(api_client, ticket, staff, "request_evidence", prompt="Attach a photo of the entrance.").status_code == 200
    row = TicketInformationRequest.objects.get()
    snapshot = row.evidence_requirement.copy()
    assert snapshot["required_from_user_id"] == str(user.id) and snapshot["case_type"] == "support.other"
    assert answer(api_client, ticket, user, row, body="Text alone cannot meet the evidence requirement.").status_code == 400
    first = upload(api_client, user, ticket, "teal")
    response = answer(api_client, ticket, user, row, body="", attachment_ids=[str(first)], review_status="accepted")
    assert response.status_code == 200, response.data
    row.refresh_from_db(); ticket.refresh_from_db()
    first_version = TicketEvidenceSubmission.objects.get()
    assert first_version.review_status == "submitted" and ticket.status == "in_progress" and row.status == "answer_sent"
    assert command(api_client, ticket, staff, "mark_evidence_conflicting", information_request_id=str(row.id),
        information_revision=row.revision, reason="The entrance differs from the description.").status_code == 200
    row.refresh_from_db()
    second = upload(api_client, user, ticket, "navy")
    assert answer(api_client, ticket, user, row, body="Correct entrance photo.", attachment_ids=[str(second)]).status_code == 200
    row.refresh_from_db()
    assert command(api_client, ticket, staff, "accept_information", information_request_id=str(row.id), information_revision=row.revision).status_code == 200
    first_version.refresh_from_db(); row.refresh_from_db(); ticket.refresh_from_db()
    assert first_version.review_status == "conflicting"
    assert list(row.evidence_versions.order_by("version").values_list("review_status", flat=True)) == ["conflicting", "accepted"]
    assert TicketAttachment.objects.filter(id__in=[first, second], status="attached").count() == 2
    assert row.evidence_requirement == snapshot and row.status == "accepted" and ticket.status == "in_progress"
    api_client.force_authenticate(user)
    detail = api_client.get(reverse("support-ticket-detail", args=[ticket.id]))
    exported = os.environ.get("MVP_FIXTURE_DIR")
    if exported:
        (Path(exported) / "support_evidence_ticket.json").write_text(json.dumps(detail.data, default=str), encoding="utf8")


def test_evidence_isolation_and_revocation_are_rechecked_before_review(api_client, user, superuser, inquiry, private_media):
    ticket, staff = inquiry
    assert command(api_client, ticket, staff, "request_evidence", prompt="Attach an entrance image.").status_code == 200
    row = TicketInformationRequest.objects.get()
    identity = upload(api_client, user, ticket, "blue")
    assert answer(api_client, ticket, superuser, row, body="", attachment_ids=[str(identity)]).status_code == 404
    assert answer(api_client, ticket, user, row, body="", attachment_ids=[str(identity)]).status_code == 200
    row.refresh_from_db()
    assert command(api_client, ticket, user, "accept_information", information_request_id=str(row.id), information_revision=row.revision).status_code == 403
    TicketAttachment.objects.filter(id=identity).update(status="unsafe")
    assert command(api_client, ticket, staff, "accept_information", information_request_id=str(row.id), information_revision=row.revision).status_code == 400
    api_client.force_authenticate(user)
    detail = api_client.get(reverse("support-ticket-detail", args=[ticket.id])).data
    version = detail["information_requests"][0]["evidence_versions"][0]
    assert version["review_status"] == "submitted" and version["files"][0]["available"] is False
    assert api_client.get(reverse("support-attachment", args=[identity]) + "?workspace=tenant").status_code == 404


def test_open_evidence_request_has_versioned_owner_scoped_policy(api_client, user, inquiry):
    ticket, staff = inquiry
    assert command(api_client, ticket, staff, "request_evidence", prompt="Attach an entrance photo.").status_code == 200
    api_client.force_authenticate(user)
    response = api_client.get(reverse("support-ticket-detail", args=[ticket.id]))
    requirement = response.data["information_requests"][0]
    assert requirement["can_answer"] is True and requirement["evidence_versions"] == []
    assert requirement["evidence_requirement"]["policy_revision"] == 2
    assert requirement["evidence_requirement"]["required_from_user_id"] == str(user.id)
    exported = os.environ.get("MVP_FIXTURE_DIR")
    if exported:
        (Path(exported) / "support_evidence_request_open.json").write_text(json.dumps(response.data, default=str), encoding="utf8")
