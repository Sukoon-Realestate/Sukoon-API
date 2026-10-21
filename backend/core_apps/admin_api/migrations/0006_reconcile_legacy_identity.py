"""Legacy boolean assurance cannot establish which documents were approved.

Preserve historical decisions; queue complete, non-rejected evidence for a new
review. This migration does not grant identity or email assurance and does not
alter leases, consent, money, inventory, or historical review outcomes.
"""

import hashlib
import json
from django.db import migrations
from django.utils import timezone


def reconcile(apps, schema_editor):
    User = apps.get_model("users", "User")
    Profile = apps.get_model("profiles", "Profile")
    Submission = apps.get_model("admin_api", "KYCSubmission")
    database = schema_editor.connection.alias
    User.objects.using(database).filter(is_verified=True).update(is_verified=False)
    for profile in Profile.objects.using(database).select_related("user").iterator():
        latest = (
            Submission.objects.using(database)
            .filter(profile_id=profile.pk)
            .order_by("-created_at", "-pk")
            .first()
        )
        if latest and latest.evidence_digest:
            encoded = json.dumps(
                latest.evidence_snapshot,
                sort_keys=True,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode()
            if (
                latest.status == "approved"
                and latest.reviewed_at
                and latest.reviewer_id
                and not latest.superseded_at
                and hashlib.sha256(encoded).hexdigest() == latest.evidence_digest
                and all(
                    latest.evidence_snapshot.get(key)
                    for key in ("national_id", "id_face", "id_back")
                )
            ):
                User.objects.using(database).filter(pk=profile.user_id).update(
                    is_verified=True
                )
            continue
        if latest and latest.status == "rejected":
            continue
        if not (profile.national_id and profile.id_face and profile.id_back):
            continue

        def image(field):
            value = getattr(profile, field)
            return value.url if value and hasattr(value, "url") else str(value or "")

        snapshot = {
            "national_id": profile.national_id,
            "full_name": f"{profile.user.first_name} {profile.user.last_name}".strip(),
            "birth_date": str(profile.birth_date or ""),
            "gender": profile.gender,
            "id_face": image("id_face"),
            "id_back": image("id_back"),
            "confirmation_selfi": image("confirmation_selfi"),
        }
        digest = hashlib.sha256(
            json.dumps(
                snapshot, sort_keys=True, ensure_ascii=False, separators=(",", ":")
            ).encode()
        ).hexdigest()
        Submission.objects.using(database).filter(
            profile_id=profile.pk, superseded_at__isnull=True
        ).update(superseded_at=timezone.now())
        Submission.objects.using(database).create(
            profile_id=profile.pk,
            evidence_snapshot=snapshot,
            evidence_digest=digest,
            notes="Legacy evidence requires a version-bound review; no prior approval was inferred.",
        )


class Migration(migrations.Migration):
    dependencies = [
        ("admin_api", "0005_kycsubmission_evidence_digest_and_more"),
        ("users", "0005_user_is_email_verified"),
        ("profiles", "0005_profile_phone_number"),
    ]
    operations = [migrations.RunPython(reconcile, migrations.RunPython.noop)]
