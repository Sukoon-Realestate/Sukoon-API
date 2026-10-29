"""Readable termination clauses with immutable reviewed signing input.

Database cases use fresh pytest records and no provider transport. These are
source tests, not evidence of hosted signing or a deployed document upgrade.
"""

import copy
import hashlib
from unittest.mock import patch

import pytest

from core_apps.features.models import RentalChange, RentalSigningDocument
from core_apps.features.services import signing_documents
from core_apps.features.services.rental_phase2 import RentalConflict
from .test_rental_phase5 import phase5_lease


def policy():
    return {
        "notice_days": 30,
        "notice_method": "written",
        "clause_text": "يُرسل الإخطار كتابيًا مع بقاء الالتزامات المالية.",
    }


def test_structured_clause_renders_every_field_and_escapes_untrusted_text():
    clause = {
        **policy(),
        "notice_days": 0,
        "clause_text": 'إخطار <script>alert("x")</script> & التزامات',
        "extra_<condition>": {"details": ["<img src=x onerror=alert(1)>", None, False]},
    }
    snapshot = {"terms": {"termination_policy": clause}}
    original = copy.deepcopy(snapshot)
    rendered = signing_documents.render(snapshot, []).decode()

    assert "شروط الإنهاء / Termination" in rendered
    assert "مهلة الإخطار بالأيام / Notice days</th><td>0" in rendered
    assert "طريقة الإخطار / Notice method</th><td>كتابي / Written" in rendered
    assert "نص البند / Clause text" in rendered
    assert "إخطار &lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt; &amp; التزامات" in rendered
    assert "extra_&lt;condition&gt;" in rendered
    assert "&lt;img src=x onerror=alert(1)&gt;" in rendered
    assert "<li>—</li>" in rendered and "<li>لا / No</li>" in rendered
    assert "<script>" not in rendered and "<img " not in rendered
    assert "&amp;lt;" not in rendered
    assert snapshot == original


def test_written_translation_is_limited_to_the_notice_method_value():
    rendered = signing_documents.render(
        {"terms": {"termination_policy": {
            "notice_method": "written", "clause_text": "written", "custom": "written",
        }}},
        [],
    ).decode()
    assert rendered.count("كتابي / Written") == 1
    assert "نص البند / Clause text</th><td>written" in rendered
    assert "<th>custom</th><td>written" in rendered
    assert signing_documents._display("other_<method>", "notice_method") == "other_&lt;method&gt;"


@pytest.fixture
def termination_document_source(phase5_lease, settings):
    settings.SIGNWELL_TEST_ENABLED = True
    settings.SIGNWELL_API_KEY = "synthetic-document-test-key"
    settings.SIGNWELL_WEBHOOK_ID = "synthetic-document-test-webhook"
    settings.RENTAL_RUNTIME_ENVIRONMENT = "test"
    owner, tenant, lease = phase5_lease
    terms = {**copy.deepcopy(lease.terms), "termination_policy": policy()}
    change = RentalChange.objects.create(
        lease=lease, requester=owner, kind="amendment", status="accepted",
        terms=terms, previous_terms=copy.deepcopy(lease.terms),
        approvals=[str(owner.id), str(tenant.id)],
    )
    return lease, change


@pytest.mark.django_db
def test_new_document_keeps_canonical_snapshot_and_hashes_its_rendered_source(
    termination_document_source,
):
    lease, change = termination_document_source
    original_terms = copy.deepcopy(change.terms)
    with patch.object(signing_documents.signwell_client, "_request", side_effect=AssertionError("No transport")):
        generated = signing_documents.prepare(change.id, change.revision, change.terms)
        replayed = signing_documents.prepare(change.id, change.revision, change.terms)

    document = RentalSigningDocument.objects.get(id=generated.document_id)
    content = bytes(document.source_content)
    assert generated.document_id == replayed.document_id
    assert generated.digest == replayed.digest == document.source_hash == hashlib.sha256(content).hexdigest()
    assert document.source_revision == document.snapshot["source_revision"] == change.revision
    assert document.snapshot["source_id"] == str(change.id)
    assert document.snapshot["lease_id"] == str(lease.id)
    assert document.snapshot["terms"] == original_terms
    assert document.snapshot["terms"]["termination_policy"]["notice_method"] == "written"
    assert "كتابي / Written" in content.decode()
    assert "نص البند / Clause text" in content.decode()
    assert document.status == "prepared" and document.provider_document_id is None
    assert RentalSigningDocument.objects.filter(change=change).count() == 1
    change.refresh_from_db()
    assert change.terms == original_terms
    assert change.status == "accepted" and not change.signing_sessions.exists()


@pytest.mark.django_db
def test_preexisting_source_is_not_regenerated_after_label_translation_changes(
    termination_document_source, monkeypatch,
):
    _, change = termination_document_source
    current_display = signing_documents._display

    def previous_display(value, field=""):
        # Model the previous renderer without copying any production document.
        return current_display(value, "" if field == "notice_method" else field)

    with monkeypatch.context() as previous:
        previous.delitem(signing_documents.LABELS, "notice_method")
        previous.delitem(signing_documents.LABELS, "clause_text")
        previous.setattr(signing_documents, "_display", previous_display)
        original = signing_documents.prepare(change.id, change.revision, change.terms)
    document = RentalSigningDocument.objects.get(id=original.document_id)
    frozen = {
        "snapshot": copy.deepcopy(document.snapshot),
        "content": bytes(document.source_content),
        "hash": document.source_hash,
        "recipients": copy.deepcopy(document.recipients),
        "updated_at": document.updated_at,
    }
    assert "<th>notice_method</th><td>written" in frozen["content"].decode()
    assert signing_documents.render(document.snapshot, document.recipients) != frozen["content"]

    with pytest.raises(RentalConflict) as conflict:
        signing_documents.prepare(change.id, change.revision, change.terms)
    assert conflict.value.get_codes() == "document_changed"
    document.refresh_from_db()
    assert document.snapshot == frozen["snapshot"]
    assert bytes(document.source_content) == frozen["content"]
    assert document.source_hash == frozen["hash"] == original.digest
    assert document.source_hash == hashlib.sha256(frozen["content"]).hexdigest()
    assert document.recipients == frozen["recipients"]
    assert document.updated_at == frozen["updated_at"]
    assert RentalSigningDocument.objects.filter(change=change).count() == 1


@pytest.mark.django_db
def test_changed_canonical_clause_cannot_replace_the_same_frozen_revision(
    termination_document_source,
):
    _, change = termination_document_source
    generated = signing_documents.prepare(change.id, change.revision, change.terms)
    document = RentalSigningDocument.objects.get(id=generated.document_id)
    original_snapshot = copy.deepcopy(document.snapshot)
    original_content = bytes(document.source_content)
    change.terms = {**change.terms, "termination_policy": {**policy(), "notice_days": 60}}
    change.save(update_fields=["terms"])

    with pytest.raises(RentalConflict) as conflict:
        signing_documents.prepare(change.id, change.revision, change.terms)
    assert conflict.value.get_codes() == "document_changed"
    document.refresh_from_db()
    assert document.snapshot == original_snapshot
    assert bytes(document.source_content) == original_content
    assert document.source_hash == generated.digest == hashlib.sha256(original_content).hexdigest()
    assert RentalSigningDocument.objects.filter(change=change).count() == 1
