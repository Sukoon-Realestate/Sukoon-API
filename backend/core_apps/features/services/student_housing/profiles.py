from django.shortcuts import get_object_or_404
from ...student_models import StudentProfile, Campus
from ...models import RentalVerificationClaim
from ..planning import check_revision
from ..rental_lifecycle.claims import current_claims, claim_current
from ..rental_lifecycle.common import audit
from .plans import json_value


def enrollment(user, *, allow_admission=False, campus_id=None):
    claims = current_claims(
        RentalVerificationClaim.objects.filter(
            subject_user=user,
            subject_kind="student_enrollment",
            claim_code__in=(
                ["enrollment", "admission"] if allow_admission else ["enrollment"]
            ),
        )
    )
    if campus_id:
        claims = claims.filter(campus__id=campus_id)
    return next(
        (claim for claim in claims.order_by("-checked_at") if claim_current(claim)),
        None,
    )


def campus_payload(item, language="en"):
    from core_apps.properties.catalog_labels import location_label

    return {
        "id": str(item.id),
        "name": item.name_ar if language.startswith("ar") else item.name_en,
        "university_id": str(item.university.id),
        "university": (
            item.university.name_ar
            if language.startswith("ar")
            else item.university.name_en
        ),
        "city_id": str(item.city.id),
        "city": location_label(item.city, language),
        "revision": item.revision,
        "university_revision": item.university.revision,
        "active": item.active and item.university.active,
        "latitude": float(item.latitude) if item.latitude is not None else None,
        "longitude": float(item.longitude) if item.longitude is not None else None,
        "checked_on": str(item.checked_on) if item.checked_on else None,
    }


def requirements_payload(value):
    from django.utils.translation import get_language

    names, campuses = {}, []
    for campus in Campus.objects.filter(
        id__in=value.get("campus_ids", [])
    ).select_related("university", "city"):
        item = campus_payload(campus, get_language() or "en")
        names[str(campus.id)] = item["university"] + " · " + item["name"]
        campuses.append(item)
    return {**value, "campus_labels": names, "campuses": campuses}


def profile_payload(item, user):
    claim = enrollment(user, allow_admission=True)
    return {
        "id": str(item.id if item else user.id),
        "revision": item.revision if item else 0,
        "campus_id": str(item.campus.id) if item and item.campus_id else None,
        "institution_name": item.institution_name if item else "",
        "academic_stage": item.academic_stage if item else "",
        "enrollment_status": item.enrollment_status if item else "admission_pending",
        "study_start": str(item.study_start) if item and item.study_start else None,
        "study_end": str(item.study_end) if item and item.study_end else None,
        "preferences": item.preferences if item else {},
        "roommate_disclosures": item.roommate_disclosures if item else [],
        "identity_verified": user.is_verified,
        "review_case_ids": [
            str(case.id)
            for case in user.opened_rental_cases.filter(
                kind="student_verification"
            ).order_by("-created_at")
        ],
        "student_verification": {
            "status": claim.claim_code if claim else "unverified",
            "expires_at": claim.expires_at.isoformat() if claim else None,
        },
        "allowed_actions": ["save_profile"],
        "blocking_reasons": [],
    }


def save_profile(user, data):
    item = StudentProfile.objects.select_for_update().filter(user=user).first()
    scope_fields = (
        "campus_id",
        "institution_name",
        "enrollment_status",
        "study_start",
        "study_end",
    )
    previous_scope = tuple(getattr(item, key) for key in scope_fields) if item else None
    check_revision(item.revision if item else 0, data["expected_revision"])
    if item:
        item.revision += 1
    else:
        item = StudentProfile(user=user)
    previous_campus = item.campus if item.pk else None
    item.campus = (
        get_object_or_404(Campus, id=data["campus_id"])
        if data.get("campus_id")
        else None
    )
    from core_apps.properties.catalog_access import require_current_selection

    require_current_selection(item.campus, previous=previous_campus, field="campus_id")
    for key in (
        "institution_name",
        "academic_stage",
        "enrollment_status",
        "preferences",
        "roommate_disclosures",
    ):
        setattr(item, key, data[key])
    item.study_start, item.study_end = data.get("study_start"), data.get("study_end")
    item.save()
    if previous_scope is not None and previous_scope != tuple(
        getattr(item, key) for key in scope_fields
    ):
        from django.utils import timezone

        for claim in RentalVerificationClaim.objects.select_for_update().filter(
            subject_user=user,
            subject_kind="student_enrollment",
            revoked_at__isnull=True,
        ):
            claim.revoked_at = timezone.now()
            claim.save(update_fields=["revoked_at", "updated_at"])
            audit(
                claim,
                user,
                "student_verification.affiliation_changed",
                "Academic affiliation or study status changed; a new review is required for future eligibility.",
            )
    audit(item, user, "student_profile.saved")
    return item


def roommate_disclosures(user):
    """Explicitly selected profile text only; never used for ranking or eligibility."""
    from django.conf import settings

    if "student_planning" not in getattr(settings, "STUDENT_ENABLED_SERVICES", []):
        return {}
    profile = StudentProfile.objects.filter(user=user).first()
    if not profile:
        return {}
    value = {
        key: text
        for key, text in profile.preferences.items()
        if key in profile.roommate_disclosures and text
    }
    if "campus" in profile.roommate_disclosures and profile.campus_id:
        item = campus_payload(profile.campus)
        value["campus"] = item["university"] + " · " + item["name"]
    return value
