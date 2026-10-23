"""Typed evidence follows the same original-command and private-download fences."""

import hashlib
import uuid
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from core_apps.features.models import RentalEvidence
from core_apps.features.tasks import scan_rental_evidence
from core_apps.features.tests.test_rental_phase4 import phase4_lease, client_for
from core_apps.features.tests.test_rental_phase2 import rental_participants
from core_apps.support.tests.test_staged_media import pdf
from config.student_housing import SERVICES

pytestmark = pytest.mark.django_db
API = "/api/v1/features/v1/"


@pytest.fixture(autouse=True)
def media_policy(settings):
    settings.STUDENT_ENABLED_SERVICES = list(SERVICES)
    settings.EVIDENCE_STORAGE_PROVIDER = "database"
    settings.EVIDENCE_SCANNER_BACKEND = "fake"
    settings.RENTAL_RUNTIME_ENVIRONMENT = "test"
    settings.RENTAL_FAKE_PROVIDER_ALLOWED = True


def test_rental_pdf_retains_bytes_and_private_grant(phase4_lease):
    owner, tenant, lease = phase4_lease
    content = pdf()
    response = client_for(tenant).post(
        API + "rental-attachments/",
        {
            "lease_id": str(lease.id),
            "request_key": str(uuid.uuid4()),
            "mime_type": "application/pdf",
            "sha256": hashlib.sha256(content).hexdigest(),
            "file": SimpleUploadedFile(
                "condition.pdf", content, content_type="application/pdf"
            ),
        },
        format="multipart",
    )
    assert response.status_code == 201, response.data
    evidence = RentalEvidence.objects.get(id=response.data["resource"]["id"])
    assert scan_rental_evidence()["safe"] == 1
    link = client_for(tenant).get(API + f"rental-attachments/{evidence.id}/download/")
    assert link.status_code == 200, link.data
    downloaded = client_for(tenant).get(link.data["url"])
    assert downloaded.status_code == 200
    assert downloaded["Content-Type"] == "application/pdf"
    assert downloaded.content == content
    assert client_for(owner).get(link.data["url"]).status_code == 404


def test_student_pdf_is_private_and_video_rejected(rental_participants):
    owner, student, stranger, _, _ = rental_participants
    api = client_for(student)
    profile = api.post(
        API + "student-profile/",
        {
            "request_key": str(uuid.uuid4()),
            "expected_revision": 0,
            "enrollment_status": "admission_pending",
        },
        format="json",
    )
    assert profile.status_code == 200, profile.data
    content = pdf()
    response = api.post(
        API + "student-evidence/upload/",
        {
            "request_key": str(uuid.uuid4()),
            "sha256": hashlib.sha256(content).hexdigest(),
            "file": SimpleUploadedFile(
                "enrollment.pdf", content, content_type="application/pdf"
            ),
        },
        format="multipart",
    )
    assert response.status_code == 201, response.data
    identity = response.data["resource"]["id"]
    assert scan_rental_evidence()["safe"] == 1
    downloaded = api.get(API + f"student-evidence/{identity}/")
    assert downloaded.status_code == 200, downloaded.content
    assert downloaded["Content-Type"] == "application/pdf"
    assert downloaded.content == content
    for viewer in [owner, stranger]:
        assert (
            client_for(viewer).get(API + f"student-evidence/{identity}/").status_code
            == 404
        )
    rejected = api.post(
        API + "student-evidence/upload/",
        {
            "request_key": str(uuid.uuid4()),
            "file": SimpleUploadedFile(
                "enrollment.mp4", b"0000ftypbad", content_type="video/mp4"
            ),
        },
        format="multipart",
    )
    assert rejected.status_code == 400
