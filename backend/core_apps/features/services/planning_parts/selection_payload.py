"""Planning: selection payload."""

from datetime import date
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from config.planning import SERVICES
from core_apps.properties.models import Property
from core_apps.users.models import User
from ...pagination import FeaturePagination
from ..commands import command_identity
from ..rental_phase2 import RentalConflict, remember_mutation, replay_operation


def enabled_services():
    from config.advanced_housing import SERVICES as ADVANCED_SERVICES
    from config.student_housing import SERVICES as STUDENT_SERVICES

    return (
        ["company_housing", "residential_portfolios"]
        + [
            x
            for x in SERVICES
            if x in getattr(settings, "PLANNING_ENABLED_SERVICES", [])
        ]
        + [
            x
            for x in STUDENT_SERVICES
            if x in getattr(settings, "STUDENT_ENABLED_SERVICES", [])
        ]
        + [
            x
            for x in ADVANCED_SERVICES
            if x in getattr(settings, "ADVANCED_HOUSING_ENABLED_SERVICES", [])
        ]
    )


def require_planning(user, capability):
    from ..planning_providers import ready_services

    if not user.is_active or not user.is_verified:
        raise PermissionDenied(
            {
                "message": "A verified active account is required.",
                "code": "account_verification_required",
            }
        )
    if capability is not None and capability not in ready_services(enabled_services()):
        raise PermissionDenied(
            {
                "message": "This planning service is disabled.",
                "code": "capability_unavailable",
            }
        )


def page(request, items, serialize):
    paginator = FeaturePagination()
    subset = paginator.paginate_queryset(items, request)
    return paginator.get_paginated_response([serialize(x) for x in subset])


def check_revision(actual, expected):
    if type(expected) is not int or expected < 0:
        raise ValidationError(
            {"expected_revision": "Supply a nonnegative integer revision."}
        )
    if actual != expected:
        raise RentalConflict(
            "Refresh and review the current revision.", code="stale_revision"
        )


@transaction.atomic
def mutate(request, operation, load, apply, serialize, *, creating=False):
    key, revision = command_identity(request.data)
    # Serialize identical creations for one actor; shared resource locks are taken
    # by load() for commands by different actors.
    User.objects.select_for_update(no_key=True).get(pk=request.user.pk)
    parent = load()
    replay = replay_operation(request.user, operation, key, request.data)
    if replay:
        return Response(replay[0], status=replay[1])
    if creating:
        check_revision(0, revision)
    elif parent is not None:
        check_revision(parent.revision, revision)
    item = apply(parent, revision)
    from ..planning_notifications import record_event

    record_event(item, request.user, operation)
    response_status = 201 if creating else 200
    output = remember_mutation(
        user=request.user,
        operation=operation,
        request_key=key,
        payload=request.data,
        request_subject_id=parent.id if parent is not None else request.user.id,
        result_subject_id=item.id,
        result_revision=item.revision,
        resource=serialize(item),
        response_status=response_status,
    )
    return Response(output, status=response_status)


def display_name(user):
    # Never substitute an email address or phone number for a disclosed name.
    return (
        " ".join(x for x in [user.first_name, user.last_name] if x).strip() or "Member"
    )


def text_field(data, key, *, required=False, limit=2000):
    value = data.get(key, "")
    if (
        not isinstance(value, str)
        or len(value) > limit
        or (required and not value.strip())
    ):
        raise ValidationError(
            {
                key: f"Supply {'nonempty ' if required else ''}text of at most {limit} characters."
            }
        )
    return value.strip()


def civil_date(value, field="date", *, future=False):
    try:
        parsed = date.fromisoformat(value)
    except (ValueError, TypeError):
        raise ValidationError({field: "Use YYYY-MM-DD."})
    if future and parsed < timezone.localdate():
        raise ValidationError({field: "The date cannot be in the past."})
    return parsed


def public_properties():
    from core_apps.chat.moderation.policy import visible_properties
    return visible_properties(Property.objects.filter(
        status="verified",
        is_verified=True,
        owner__is_active=True,
        owner__is_verified=True,
    ))


def eligible_owner(user):
    return public_properties().filter(owner=user, is_ownership_verified=True).exists()


def selection_payload(raw):
    """Canonical wire defaults match RentalSelection/RentalTerms round trips."""
    terms = raw.get("terms") or {}
    if not isinstance(terms, dict):
        raise ValidationError({"terms": "Supply a terms object."})
    result = {
        "property_id": "",
        "offer_id": "",
        "offer_revision": 0,
        "rental_scope": None,
        "name": "",
        "room_ids": [],
        "room_names": [],
        "bed_id": "",
        "bed_name": "",
        "availability": None,
        "archived": False,
        "capacity": None,
        "bathroom_access": [],
        "offer_link": "",
        **raw,
    }
    result["bed_id"] = result.get("bed_id") or ""
    result["bed_name"] = result.get("bed_name") or ""
    bathroom = result["bathroom_access"]
    result["bathroom_access"] = (
        [bathroom] if isinstance(bathroom, str) and bathroom else (bathroom or [])
    )
    result["terms"] = {
        "price": "",
        "price_period": "",
        "rental_period": 0,
        "deposit": "",
        "suitable_for": "",
        "description": "",
        "smoking_allowed": None,
        "rules": [],
        **terms,
    }
    for key in ("price", "deposit", "description"):
        result["terms"][key] = str(result["terms"].get(key) or "").strip()
    return result
