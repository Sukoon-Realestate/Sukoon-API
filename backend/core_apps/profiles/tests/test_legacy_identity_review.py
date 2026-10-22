import io
import json
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from core_apps.features.models import RentalAuditEvent

pytestmark = pytest.mark.django_db


def test_report_does_not_revoke_and_apply_requires_current_review(user, superuser):
    user.is_verified = True
    user.save()
    output = io.StringIO()
    call_command("review_legacy_identity", user_id=str(user.id), stdout=output)
    row = json.loads(output.getvalue())
    user.refresh_from_db()
    assert user.is_verified
    assert not row["bound_approval"]
    with pytest.raises(CommandError):
        call_command("review_legacy_identity", apply=True)
    args = dict(apply=True, user_id=str(user.id), reviewer_id=str(superuser.id), expected_state=row["expected_state"], reason="Independently reviewed synthetic fixture")
    with pytest.raises(CommandError):
        call_command("review_legacy_identity", decision="restore_verified", **args)
    call_command("review_legacy_identity", decision="require_review", **args, stdout=io.StringIO())
    user.refresh_from_db()
    assert not user.is_verified
    assert RentalAuditEvent.objects.filter(subject_id=user.id, action="identity.legacy.require_review").count() == 1
    with pytest.raises(CommandError):
        call_command("review_legacy_identity", decision="require_review", **args)


def test_schema_marker_has_no_population_wide_data_operation():
    import importlib
    migration = importlib.import_module("core_apps.admin_api.migrations.0006_reconcile_legacy_identity")
    assert migration.Migration.operations == []


def test_old_approval_cannot_restore_changed_current_evidence(user, superuser):
    from django.utils import timezone
    from core_apps.admin_api.models import KYCSubmission
    from core_apps.common.idempotency import fingerprint
    from core_apps.profiles.management.commands.review_legacy_identity import snapshot
    from core_apps.users.services.identity_submission import evidence_snapshot

    profile = user.profile
    profile.national_id = "synthetic-identity"
    profile.id_face = "image/authenticated/v1/test/front.png"
    profile.id_back = "image/authenticated/v1/test/back.png"
    profile.save()
    evidence = evidence_snapshot(profile)
    KYCSubmission.objects.create(profile=profile, status="approved", reviewer=superuser,
        reviewed_at=timezone.now(), evidence_snapshot=evidence, evidence_digest=fingerprint(evidence))
    original = snapshot(profile)
    assert original["bound_approval"]
    profile.id_face = "image/authenticated/v2/test/changed.png"
    profile.save(update_fields=["id_face"])
    changed = snapshot(profile)
    assert not changed["bound_approval"]
    assert changed["expected_state"] != original["expected_state"]
    with pytest.raises(CommandError):
        call_command("review_legacy_identity", apply=True, user_id=str(user.id), reviewer_id=str(superuser.id),
            expected_state=changed["expected_state"], decision="restore_verified", reason="Synthetic stale approval test")
    user.refresh_from_db()
    assert not user.is_verified
