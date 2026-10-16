from datetime import date
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from ...student_models import StudentOfferPolicy
from ..rental_phase2 import RentalConflict
from ..rental_lifecycle.common import audit
from ..planning import check_revision
from ..tenancy_invitations import resolve_offer_snapshot
from .profiles import enrollment
from .plans import json_value


def policy_for(prop, offer_id):
    return StudentOfferPolicy.objects.filter(
        property=prop, offer_id=offer_id, active=True
    ).first()


def snapshot_for(prop, offer_id):
    item = policy_for(prop, offer_id)
    return policy_payload(item) if item else {}


def response_policy_current(response):
    item = policy_for(response.property, response.selection.get("offer_id"))
    if not item:
        return not response.student_policy_snapshot
    return (
        str(item.id) == response.student_policy_snapshot.get("id")
        and item.expires_at > timezone.now()
        and item.offer_revision == response.selection.get("offer_revision")
    )


def policy_payload(item):
    return {
        "id": str(item.id),
        "revision": item.revision,
        "offer_id": item.offer_id,
        "status": (
            "current" if item.active and item.expires_at > timezone.now() else "expired"
        ),
        "offer_revision": item.offer_revision,
        "eligibility": item.eligibility,
        "period_kinds": item.period_kinds,
        "starts_on": str(item.starts_on),
        "ends_on_exclusive": str(item.ends_on_exclusive),
        "expires_at": item.expires_at.isoformat(),
        "terms": item.terms,
        "billing_period": "monthly",
        "currency": "EGP",
        "conditional_cancellation_guarantee": False,
        "renewal_is_reservation": False,
        "allowed_actions": [],
        "blocking_reasons": [],
    }


def save_policy(user, prop, data):
    _, selection = resolve_offer_snapshot(
        prop, data["offer_id"], data["offer_revision"]
    )
    if selection["terms"].get("price_period") != "monthly":
        raise ValidationError(
            {"offer_id": "Academic agreements use supported monthly EGP billing."}
        )
    if (
        not data["starts_on"] < data["ends_on_exclusive"]
        or data["expires_at"] <= timezone.now()
    ):
        raise ValidationError(
            {"expires_at": "Supply future expiry and valid accommodation dates."}
        )
    old = policy_for(prop, data["offer_id"])
    check_revision(old.revision if old else 0, data["expected_revision"])
    if old:
        old.active = False
        old.save(update_fields=["active", "updated_at"])
    item = StudentOfferPolicy.objects.create(
        property=prop,
        recorded_by=user,
        offer_id=data["offer_id"],
        offer_revision=data["offer_revision"],
        revision=old.revision + 1 if old else 1,
        eligibility=data["eligibility"],
        period_kinds=data["period_kinds"],
        starts_on=data["starts_on"],
        ends_on_exclusive=data["ends_on_exclusive"],
        expires_at=data["expires_at"],
        terms={
            key: data[key]
            for key in (
                "exam_extension_requests",
                "renewal_requests",
                "summer_storage_requests",
            )
        },
    )
    audit(item, user, "student_offer_policy.saved")
    return item


def validate_occupants(prop, selection, occupants, start, end, *, occupant_count=None):
    policy = policy_for(prop, selection.get("offer_id"))
    if not policy:
        return
    if (
        policy.offer_revision != selection.get("offer_revision")
        or policy.expires_at <= timezone.now()
    ):
        raise RentalConflict(
            "Review current academic offer terms.", code="student_policy_changed"
        )
    if start < policy.starts_on or end > policy.ends_on_exclusive:
        raise RentalConflict(
            "The dates do not match this academic offer policy.",
            code="student_dates_unavailable",
        )
    if policy.eligibility != "open":
        if occupant_count is not None and occupant_count != len(occupants):
            raise RentalConflict(
                "Each intended occupant needs individual eligibility review.",
                code="occupant_eligibility_required",
            )
        if not all(
            enrollment(
                person, allow_admission=policy.eligibility == "admission_or_enrollment"
            )
            for person in occupants
        ):
            raise RentalConflict(
                "An intended occupant does not currently meet this offer's student policy.",
                code="student_eligibility_required",
            )


def validate_response(request, prop, selection):
    from ..rental_lifecycle.inventory import assert_available

    plan = request.academic_plan
    # No hold is created: availability is an observation at this instant.
    assert_available(prop, selection, plan.starts_on, plan.ends_on_exclusive)
    people = [
        row.user
        for row in plan.participants.exclude(status="withdrawn").select_related("user")
    ]
    validate_occupants(
        prop,
        selection,
        people,
        plan.starts_on,
        plan.ends_on_exclusive,
        occupant_count=len(people),
    )
    policy = policy_for(prop, selection["offer_id"])
    if policy and plan.period_kind not in policy.period_kinds:
        raise RentalConflict(
            "This offer does not cover the requested academic period.",
            code="student_period_unavailable",
        )
