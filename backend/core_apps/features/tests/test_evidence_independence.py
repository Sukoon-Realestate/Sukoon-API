import hashlib
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone
from core_apps.features.models import RentalEvidence
from core_apps.features.tasks import scan_rental_evidence
from core_apps.features.services import evidence_storage
from .test_rental_phase4 import phase4_lease, upload_evidence, client_for

pytestmark = pytest.mark.django_db


def test_evidence_upload_scan_and_read_without_payment_provider(phase4_lease, settings):
    settings.RENTAL_PROVIDER_BACKEND = "disabled"
    owner, tenant, lease = phase4_lease
    response = upload_evidence(tenant, lease)
    assert response.status_code == 201
    item = RentalEvidence.objects.get()
    assert item.storage_provider == "pending"
    assert scan_rental_evidence()["safe"] == 1
    item.refresh_from_db()
    assert item.storage_provider == "database"
    assert item.scan_sha256 == item.sha256
    assert item.scan_engine == "synthetic-test-only"
    link = client_for(tenant).get(f"/api/v1/features/v1/rental-attachments/{item.id}/download/").data
    assert client_for(tenant).get(link["url"]).content == bytes(item.private_content)
    assert client_for(owner).get(link["url"]).status_code == 404
    item.deleted_at = timezone.now()
    item.save()
    assert client_for(tenant).get(link["url"]).status_code == 404


def test_png_header_is_not_accepted_as_decodable_evidence(phase4_lease):
    _, tenant, lease = phase4_lease
    assert upload_evidence(tenant, lease, b"\x89PNG\r\n\x1a\nheader-only").status_code == 400
    assert not RentalEvidence.objects.exists()


def test_scan_lease_prevents_duplicate_inspection_and_failures_preserve_bytes(phase4_lease):
    _, tenant, lease = phase4_lease
    assert upload_evidence(tenant, lease).status_code == 201
    original = bytes(RentalEvidence.objects.get().private_content)
    with patch.object(evidence_storage, "scan", side_effect=TimeoutError):
        assert scan_rental_evidence()["failed"] == 1
    item = RentalEvidence.objects.get()
    assert item.malware_status == "pending" and bytes(item.private_content) == original
    assert scan_rental_evidence()["safe"] == 0
    item.scan_until = timezone.now() - timedelta(seconds=1)
    item.save()

    def inspect(content):
        assert scan_rental_evidence()["safe"] == 0
        return evidence_storage.ScanResult(True, "fixture-engine", hashlib.sha256(content).hexdigest())

    with patch.object(evidence_storage, "scan", side_effect=inspect) as mock:
        assert scan_rental_evidence()["safe"] == 1
        assert mock.call_count == 1
    assert scan_rental_evidence()["safe"] == 0


def test_no_fake_inspection_or_fake_download_in_production(settings):
    settings.RENTAL_RUNTIME_ENVIRONMENT = "production"
    settings.EVIDENCE_SCANNER_BACKEND = "fake"
    assert evidence_storage.available() is False
    with pytest.raises(evidence_storage.PrivateStorageUnavailable):
        evidence_storage.scan(b"clean")


def test_clamav_errors_and_detection_are_distinct(settings, monkeypatch):
    from subprocess import CompletedProcess, TimeoutExpired
    settings.EVIDENCE_SCANNER_BACKEND = "clamav"
    monkeypatch.setattr(evidence_storage.shutil, "which", lambda value: "/verified/clamscan")
    for returncode, safe in [(0, True), (1, False), (2, None)]:
        with patch.object(evidence_storage.subprocess, "run", side_effect=[CompletedProcess([], 0, b"ClamAV 1.4.3/123/test\n"), CompletedProcess([], returncode, b"")]):
            if safe is None:
                with pytest.raises(evidence_storage.PrivateStorageUnavailable): evidence_storage.scan(b"fixture")
            else:
                assert evidence_storage.scan(b"fixture").safe is safe
    with patch.object(evidence_storage.subprocess, "run", side_effect=TimeoutExpired("scan", 45)):
        with pytest.raises(evidence_storage.PrivateStorageUnavailable): evidence_storage.scan(b"fixture")


def test_corruption_is_quarantined_without_endless_scanner_retries(phase4_lease):
    _, tenant, lease = phase4_lease
    upload_evidence(tenant, lease)
    item = RentalEvidence.objects.get()
    item.private_content = b"modified"
    item.save()
    with patch.object(evidence_storage, "scan") as inspect:
        assert scan_rental_evidence()["failed"] == 1
        assert scan_rental_evidence()["failed"] == 0
        inspect.assert_not_called()
    item.refresh_from_db()
    assert item.malware_status == "failed" and item.scan_error_code == "integrity_mismatch"


def test_existing_cloudinary_content_is_readable_when_new_uploads_disabled(settings, monkeypatch):
    from types import SimpleNamespace
    import io
    payload = b"original"
    settings.EVIDENCE_STORAGE_PROVIDER = "disabled"
    monkeypatch.setattr(evidence_storage.EvidencePrivateStorage, "open", lambda *a, **k: io.BytesIO(payload))
    item = SimpleNamespace(storage_provider="cloudinary", storage_key="existing.png", size_bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
    assert evidence_storage.EvidencePrivateStorage().remote
    assert evidence_storage.read(item) == payload
