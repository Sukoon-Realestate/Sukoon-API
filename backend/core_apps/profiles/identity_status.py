"""Private, versioned identity preparation projection; no document URLs or PII."""

from core_apps.common.idempotency import fingerprint
from .identity_media import reference

DOCUMENT_FIELDS = {
    "national_id": "national_id",
    "front_id_image": "id_face",
    "back_id_image": "id_back",
    "selfie_image": "confirmation_selfi",
}


def revision(profile, submission):
    # Bind to a review decision as well as the immutable evidence version.
    return fingerprint({
        "profile": str(profile.id),
        "submission": str(submission.id) if submission else None,
        "digest": submission.evidence_digest if submission else None,
        "status": submission.status if submission else "incomplete",
        "reviewed_at": str(submission.reviewed_at) if submission else None,
        "decisions": submission.document_decisions if submission else {},
        "updated_at": str(profile.updated_at),
    })


def documents(profile, submission):
    rows = []
    for wire, field in DOCUMENT_FIELDS.items():
        present = bool(getattr(profile, field))
        decision = (submission.document_decisions or {}).get(wire, {}) if submission else {}
        state = decision.get("status") or (submission.status if submission and present else "missing")
        if not present:
            state = "missing"
        # Legacy whole-submission decisions remain explicit, never inferred approval.
        reason = decision.get("reason", "")
        if state == "rejected" and not reason:
            reason = submission.rejection_reason
        editable = not submission or submission.status == "rejected"
        rows.append({
            "id": f"{submission.id if submission else profile.id}:{wire}",
            "field": wire,
            "revision": fingerprint({"value": reference(getattr(profile, field))}) if present and field != "national_id" else revision(profile, submission),
            "status": state,
            "reason": reason,
            "present": present,
            "required": wire != "selfie_image",
            "can_replace": editable and state in {"missing", "rejected"},
        })
    return rows


def projection(profile, submission):
    return {
        "status": submission.status if submission else "incomplete",
        "full_name": profile.user.get_full_name or profile.user.first_name or profile.user.email,
        "submitted_at": submission.created_at.isoformat() if submission else None,
        "rejection_reason": submission.rejection_reason if submission and submission.status == "rejected" else "",
        "submission_id": str(submission.id) if submission else None,
        "revision": revision(profile, submission),
        "documents": documents(profile, submission),
    }


def current_projection(user):
    from django.db import transaction
    from core_apps.users.models import User
    from .models import Profile

    # Same lock order as upload/review; one response cannot mix two decisions.
    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=user.pk)
        profile, _ = Profile.objects.get_or_create(user=user)
        profile = Profile.objects.select_for_update().select_related("user").get(pk=profile.pk)
        latest = profile.kyc_submissions.order_by("-created_at", "-pk").first()
        return projection(profile, latest)
