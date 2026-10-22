import hashlib
import io
import json
import uuid
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from core_apps.features.student_models import University

pytestmark = pytest.mark.django_db


def manifest(tmp_path, **values):
    path = tmp_path / "catalog.json"
    document = {"version": 1, "kind": "university", "records": [{"id": str(uuid.uuid4()), "expected_state": "absent", "values": {
        "name_ar": "جامعة اختبار اصطناعية", "name_en": "Synthetic test university", "active": True,
        "source_url": "https://example.org/approved-catalog", "checked_on": "2026-10-22", **values}}]}
    path.write_text(json.dumps(document))
    return path, document


def test_catalog_dry_run_and_exact_reviewed_import(tmp_path, superuser):
    path, document = manifest(tmp_path)
    before = University.objects.count()
    report = io.StringIO()
    call_command("import_student_catalog", manifest=str(path), stdout=report)
    assert University.objects.count() == before
    args = dict(manifest=str(path), apply=True, reviewer_id=str(superuser.id), reason="Reviewed synthetic input",
        manifest_sha256=json.loads(report.getvalue())["manifest_sha256"])
    call_command("import_student_catalog", **args, stdout=io.StringIO())
    assert University.objects.filter(id=document["records"][0]["id"]).count() == 1
    # Old create intent is not silently turned into an overwrite or duplicate.
    with pytest.raises(CommandError): call_command("import_student_catalog", **args)
    assert University.objects.count() == before + 1


def test_changed_file_and_stale_row_are_rejected(tmp_path, superuser):
    path, document = manifest(tmp_path)
    original_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    document["records"][0]["values"]["name_en"] = "Different input"
    path.write_text(json.dumps(document))
    with pytest.raises(CommandError):
        call_command("import_student_catalog", manifest=str(path), apply=True, reviewer_id=str(superuser.id),
            reason="Test", manifest_sha256=original_hash)
    assert not University.objects.filter(id=document["records"][0]["id"]).exists()


@pytest.mark.parametrize("values", [{"name_ar": ""}, {"source_url": "http://example.org"}, {"checked_on": "2099-01-01"}])
def test_bad_provenance_or_translation_is_not_imported(tmp_path, values):
    path, document = manifest(tmp_path, **values)
    with pytest.raises(CommandError): call_command("import_student_catalog", manifest=str(path))
    assert not University.objects.filter(id=document["records"][0]["id"]).exists()


@pytest.mark.parametrize("reviewer", ["invalid-uuid", str(uuid.uuid4())])
def test_invalid_or_missing_reviewer_is_a_controlled_rejection(tmp_path, reviewer):
    path, document = manifest(tmp_path)
    with pytest.raises(CommandError, match="current authorized system owner"):
        call_command("import_student_catalog", manifest=str(path), apply=True,
            reviewer_id=reviewer, reason="Reviewed synthetic input",
            manifest_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    assert not University.objects.filter(id=document["records"][0]["id"]).exists()
