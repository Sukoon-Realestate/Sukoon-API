"""Versioned identity submission, shared by registration and resubmission."""

from django.db import transaction
from django.utils import timezone
from core_apps.common.idempotency import execute_idempotent, fingerprint
from core_apps.admin_api.models import KYCSubmission
from core_apps.profiles.models import Profile
from core_apps.users.models import User


def evidence_snapshot(profile):
    def image(field):
        from core_apps.profiles.identity_media import reference

        value = getattr(profile, field)
        return reference(value)

    return {
        "national_id": profile.national_id or "",
        "full_name": profile.user.get_full_name,
        "birth_date": str(profile.birth_date or ""),
        "gender": profile.gender,
        "id_face": image("id_face"),
        "id_back": image("id_back"),
        "confirmation_selfi": image("confirmation_selfi"),
    }


def result_for(profile, submission):
    fields = {
        "national_id": profile.national_id,
        "front_id_image": profile.id_face,
        "back_id_image": profile.id_back,
    }
    missing = [name for name, value in fields.items() if not value]
    return {
        "registration_complete": not missing,
        "verification_status": (
            submission.status if submission and not missing else "incomplete"
        ),
        "missing_fields": missing,
        "submission_id": str(submission.id) if submission else None,
        "evidence_digest": submission.evidence_digest if submission else None,
    }


@transaction.atomic
def submit_identity(user, data, *, request_key=None):
    user = User.objects.select_for_update().get(pk=user.pk)
    if user.closed_at or not user.is_active:
        from rest_framework.exceptions import PermissionDenied

        raise PermissionDenied("Account unavailable.")
    profile = Profile.objects.select_for_update().get(user=user)
    supplied_fingerprint = fingerprint(data)
    latest = profile.kyc_submissions.order_by("-created_at", "-pk").first()

    def apply():
        from core_apps.profiles.identity_status import documents, revision, DOCUMENT_FIELDS
        from rest_framework.exceptions import APIException, ValidationError

        expected = data.get("expected_revision")
        if expected and expected != revision(profile, latest):
            conflict = APIException("Identity review changed. Refresh before submitting.")
            conflict.status_code = 409
            conflict.default_code = "identity_revision_conflict"
            raise conflict
        # Granular accepted evidence is immutable during a correction, including
        # requests from older clients that do not send the new revision field.
        if expected or (latest and latest.status == "rejected" and latest.document_decisions):
            for item in documents(profile, latest):
                if data.get(item["field"]) and not item["can_replace"]:
                    raise ValidationError({item["field"]: "This identity document cannot be replaced in the current review."})
        if (
            latest
            and latest.submission_fingerprint == supplied_fingerprint
            and latest.status != "rejected"
        ):
            return result_for(profile, latest), 200, latest.id
        for source, target in (
            ("national_id", "national_id"),
            ("front_id_image", "id_face"),
            ("back_id_image", "id_back"),
            ("selfie_image", "confirmation_selfi"),
        ):
            if data.get(source):
                setattr(profile, target, data[source])
        profile.save()
        snapshot = evidence_snapshot(profile)
        if (
            latest
            and latest.evidence_digest == fingerprint(snapshot)
            and latest.status != "rejected"
        ):
            return result_for(profile, latest), 200, latest.id
        complete = all(snapshot[name] for name in ("national_id", "id_face", "id_back"))
        submission = None
        if complete:
            profile.kyc_submissions.filter(superseded_at__isnull=True).update(
                superseded_at=timezone.now()
            )
            submission = KYCSubmission.objects.create(
                profile=profile,
                evidence_snapshot=snapshot,
                evidence_digest=fingerprint(snapshot),
                submission_fingerprint=supplied_fingerprint,
                document_decisions={
                    wire: {"status": "approved", "reason": ""}
                    for wire, field in DOCUMENT_FIELDS.items()
                    if latest
                    and (latest.document_decisions or {}).get(wire, {}).get("status") == "approved"
                    and latest.evidence_snapshot.get(field) == snapshot.get(field)
                    and snapshot.get(field)
                },
            )
        # A new version cannot inherit an approval of older evidence.
        user.is_verified = False
        user.save(update_fields=["is_verified"])
        return (
            result_for(profile, submission),
            200,
            submission.id if submission else profile.id,
        )

    result, _, _ = execute_idempotent(
        user=user,
        operation="identity.submit",
        key=request_key,
        payload=data,
        action=apply,
    )
    return result
