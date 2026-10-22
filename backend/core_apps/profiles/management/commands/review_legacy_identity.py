"""No PII in the report; no decisions inferred from the historical boolean."""

import json
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core_apps.common.idempotency import fingerprint
from core_apps.profiles.identity_media import reference
from core_apps.profiles.models import Profile
from core_apps.users.models import User
from core_apps.users.services.identity_submission import evidence_snapshot


def snapshot(profile):
    latest = profile.kyc_submissions.order_by("-created_at", "-pk").first()
    evidence = latest.evidence_snapshot if latest else {}
    current_evidence = evidence_snapshot(profile)
    bound_approval = bool(
        latest and latest.status == "approved" and latest.reviewed_at and latest.reviewer_id
        and not latest.superseded_at and latest.evidence_digest
        and fingerprint(evidence) == latest.evidence_digest
        and fingerprint(current_evidence) == latest.evidence_digest
        and latest.reviewer_id != profile.user_id
        and all(evidence.get(key) for key in ("national_id", "id_face", "id_back"))
    )
    state = {
        "verified": profile.user.is_verified, "active": profile.user.is_active,
        "profile_fingerprint": fingerprint(current_evidence),
        "latest_submission": str(latest.id) if latest else None,
        "submission_state": fingerprint({
            "evidence": evidence, "evidence_digest": latest.evidence_digest,
            "status": latest.status, "reviewer": latest.reviewer_id,
            "reviewed_at": latest.reviewed_at, "superseded_at": latest.superseded_at,
        }) if latest else None,
    }
    return {
        "user_id": str(profile.user.id), "profile_id": str(profile.id),
        "is_verified": profile.user.is_verified, "bound_approval": bound_approval,
        "complete_current_evidence": bool(profile.national_id and profile.id_face and profile.id_back),
        "private_fields": {key: reference(getattr(profile, key)).startswith("image/authenticated/") for key in ("id_face", "id_back", "confirmation_selfi")},
        "expected_state": fingerprint(state), "decision": "review_required",
    }


class Command(BaseCommand):
    help = "Report historical identity state; apply one independently reviewed, digest-bound account decision."

    def add_arguments(self, parser):
        parser.add_argument("--user-id")
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--expected-state")
        parser.add_argument("--reviewer-id")
        parser.add_argument("--decision", choices=["retain", "require_review", "restore_verified"])
        parser.add_argument("--reason")

    def handle(self, *args, **options):
        if not options["apply"]:
            rows = Profile.objects.select_related("user").order_by("pk")
            if options["user_id"]:
                rows = rows.filter(user__id=options["user_id"])
            for row in rows.iterator():
                self.stdout.write(json.dumps(snapshot(row), sort_keys=True))
            return
        if not all(options.get(key) for key in ("user_id", "expected_state", "reviewer_id", "decision", "reason")):
            raise CommandError("Apply requires one account, expected state, independent reviewer, decision and reason.")
        from core_apps.admin_api.permissions import require_staff_actor
        from core_apps.admin_api.models import StaffProfile
        from core_apps.features.models import RentalAuditEvent

        with transaction.atomic():
            users = list(User.objects.select_for_update().filter(id__in=[options["user_id"], options["reviewer_id"]]).order_by("pk"))
            if len(users) != 2:
                raise CommandError("Supply existing, distinct subject and reviewer accounts.")
            subject = next(u for u in users if str(u.id) == str(options["user_id"]))
            reviewer = next(u for u in users if str(u.id) == str(options["reviewer_id"]))
            require_staff_actor(reviewer, {StaffProfile.RoleName.SYSTEM_OWNER, StaffProfile.RoleName.KYC_REVIEWER}, lock=True)
            profile = Profile.objects.select_for_update().select_related("user").get(user=subject)
            state = snapshot(profile)
            if state["expected_state"] != options["expected_state"]:
                raise CommandError("Identity state changed. Produce and review a fresh report.")
            decision = options["decision"]
            if decision == "restore_verified" and not state["bound_approval"]:
                raise CommandError("A current version-bound approval is required; no historical approval may be invented.")
            if decision != "retain":
                subject.is_verified = decision == "restore_verified"
                subject.save(update_fields=["is_verified"])
            RentalAuditEvent.objects.create(
                actor=reviewer, subject_kind="legacy_identity", subject_id=subject.id,
                subject_revision=1,
                action=f"identity.legacy.{decision}", reason=options["reason"],
                metadata={"before_digest": state["expected_state"], "was_verified": state["is_verified"], "is_verified": subject.is_verified},
            )
        self.stdout.write(json.dumps({"user_id": str(subject.id), "decision": decision, "obligations_changed": False}))
