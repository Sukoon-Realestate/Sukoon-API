import hashlib
import uuid
from datetime import date

import pytest
from rest_framework.exceptions import NotFound
from rest_framework.test import APIClient

from core_apps.features.models import PaymentReceipt, PrivateAccessRevocation, RentalDocument, RentalEvidence
from core_apps.features.planning_models import ConditionReport
from core_apps.features.planning_condition_views_parts.condition_report_context import report_for, report_payload
from core_apps.features.planning_condition_views_parts.report_snapshot import report_snapshot
from core_apps.features.services.rental_phase3_parts.payment_attempt_payload import payment_attempt_payload
from .test_rental_phase3 import phase3_lease  # noqa: F401
from .test_rental_phase6 import phase6_lease, captured_payment  # noqa: F401

pytestmark = pytest.mark.django_db


def test_comparison_evidence_is_from_the_reviewed_baseline_not_later_edits(phase3_lease):
    owner, tenant, lease = phase3_lease
    def evidence(name):
        return RentalEvidence.objects.create(lease=lease, uploader=tenant, request_key=uuid.uuid4(),
            original_name=name, content_type="image/jpeg", size_bytes=10, sha256="a" * 64,
            storage_key=str(uuid.uuid4()), malware_status="safe")
    before = evidence("before.jpg")
    later = evidence("later.jpg")
    baseline = ConditionReport.objects.create(lease=lease, author=tenant, kind="move_in", status="final",
        inspected_on=date(2026, 1, 1), items=[{"id": "wall", "evidence_ids": [str(before.id)]}])
    baseline.evidence.add(before)
    report = ConditionReport.objects.create(lease=lease, author=owner, kind="move_out", inspected_on=date(2026, 6, 1),
        baseline=baseline, baseline_revision=baseline.revision, baseline_snapshot=report_snapshot(baseline))
    baseline.evidence.set([later])
    baseline.inspected_on = date(2026, 2, 1); baseline.save()
    payload = report_payload(report_for(tenant, report.id), tenant)
    assert payload["baseline_inspected_on"] == "2026-01-01"
    assert [item["id"] for item in payload["baseline_evidence"]] == [str(before.id)]
    assert "url" not in payload["baseline_evidence"][0]
    PrivateAccessRevocation.objects.create(lease=lease, user=tenant, reason="Revoked")
    with pytest.raises(NotFound):
        report_for(tenant, report.id)


def test_payment_share_references_only_the_actual_ready_receipt_document(phase6_lease):
    _, tenant, lease = phase6_lease
    _, attempt, _ = captured_payment(lease, tenant)
    receipt = PaymentReceipt.objects.create(payment_attempt=attempt)
    assert payment_attempt_payload(attempt, tenant)["receipt_document_id"] == ""
    item = RentalDocument.objects.create(lease=lease, document_type="receipt", source_reference=str(receipt.id), title="Receipt", status="queued")
    assert payment_attempt_payload(attempt, tenant)["receipt_document_id"] == ""
    item.status = "ready"; item.save(update_fields=["status"])
    assert payment_attempt_payload(attempt, tenant)["receipt_document_id"] == str(item.id)


def test_download_preview_returns_exact_revision_and_digest_and_rechecks_access(phase6_lease):
    _, tenant, lease = phase6_lease
    content = b"%PDF-test-content"
    document = RentalDocument.objects.create(
        lease=lease, document_type="contract", title="Contract", status="ready",
        revision=4, private_content=content, sha256=hashlib.sha256(content).hexdigest(),
        media_type="application/pdf",
    )
    client = APIClient()
    client.force_authenticate(tenant)
    path = f"/api/v1/features/v1/rental-documents/{document.id}/download/"
    response = client.get(path)
    assert response.status_code == 200
    assert response.data["id"] == str(document.id)
    assert response.data["subject_id"] == str(lease.id)
    assert response.data["revision"] == 4
    assert response.data["sha256"] == hashlib.sha256(content).hexdigest()
    PrivateAccessRevocation.objects.create(lease=lease, user=tenant, reason="Revoked")
    assert client.get(path).status_code == 404
