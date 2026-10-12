"""Planning API permissions, command receipts, and authoritative accommodation."""

from datetime import date
from decimal import Decimal, InvalidOperation
from functools import wraps

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core_apps.properties.models import City, Property
from core_apps.users.models import User
from ..pagination import FeaturePagination
from ..renderers import FeatureJsonRenderer
from .commands import command_identity, money_minor
from .rental_phase2 import RentalConflict, remember_mutation, replay_operation
from .tenancy_invitations import resolve_offer_snapshot


SERVICES = (
    "lifestyle",
    "roommates",
    "housing_groups",
    "group_visits",
    "group_applications",
    "housing_requests",
    "housing_offers",
    "condition_reports",
    "move_out_notices",
    "replacements",
    "commute",
    "tenant_assistant",
)


def enabled_services():
    return [
        x for x in SERVICES if x in getattr(settings, "PLANNING_ENABLED_SERVICES", [])
    ]


def require_planning(user, capability):
    if not user.is_active or not user.is_verified:
        raise PermissionDenied(
            {
                "message": "A verified active account is required.",
                "code": "account_verification_required",
            }
        )
    if capability is not None and capability not in enabled_services():
        raise PermissionDenied(
            {
                "message": "This planning service is disabled.",
                "code": "capability_unavailable",
            }
        )


def planning_api(methods, capability):
    def decorate(fn):
        @api_view(methods)
        @permission_classes([IsAuthenticated])
        @renderer_classes([FeatureJsonRenderer])
        @wraps(fn)
        def endpoint(request, *args, **kwargs):
            require_planning(request.user, capability)
            if request.method == "POST" and not isinstance(request.data, dict):
                raise ValidationError("Supply a JSON object.")
            if request.method == "POST":
                validate_payload_types(request.data)
            try:
                response = fn(request, *args, **kwargs)
            except DjangoValidationError:
                raise ValidationError(
                    "A supplied identifier or field value is invalid."
                )
            response["Cache-Control"] = "private, no-store"
            return response

        return endpoint

    return decorate


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
    return Property.objects.filter(
        status="verified",
        is_verified=True,
        owner__is_active=True,
        owner__is_verified=True,
    )


def eligible_owner(user):
    return public_properties().filter(owner=user, is_ownership_verified=True).exists()


def selection(request, raw, *, owned=False, lock=True):
    if (
        not isinstance(raw, dict)
        or not raw.get("offer_id")
        or type(raw.get("offer_revision")) is not int
    ):
        raise ValidationError(
            {"selection": "A property, offer and integer offer_revision are required."}
        )
    queryset = public_properties()
    if owned:
        queryset = queryset.filter(owner=request.user, is_ownership_verified=True)
    if lock:
        queryset = queryset.select_for_update(of=("self",))
    prop = get_object_or_404(queryset, id=raw.get("property_id"))
    _, snapshot = resolve_offer_snapshot(
        prop, raw["offer_id"], raw["offer_revision"], request
    )
    if not snapshot:
        raise ValidationError({"selection": "Select a published rental offer."})
    snapshot = selection_payload(snapshot)
    for key in ("rental_scope", "room_ids", "bed_id", "terms"):
        if (
            key in raw
            and (selection_payload(raw)[key] if key == "terms" else raw[key])
            != snapshot[key]
        ):
            raise RentalConflict(
                "The selected accommodation or terms changed.",
                code="accommodation_changed",
            )
    return prop, snapshot


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


def offer_money(snapshot):
    terms = snapshot.get("terms", {})
    try:
        value = Decimal(str(terms["price"])) * 100
        if not value.is_finite() or value <= 0 or value != value.to_integral_value():
            raise ValueError
        rent = int(value)
        token = terms.get("deposit", "")
        if token in {"", "none", "no_deposit"}:
            deposit = 0
        elif token in {"half_month", "one_month", "two_months"}:
            from decimal import ROUND_HALF_UP

            deposit = int(
                (
                    Decimal(rent)
                    * {
                        "half_month": Decimal("0.5"),
                        "one_month": Decimal(1),
                        "two_months": Decimal(2),
                    }[token]
                ).quantize(Decimal(1), rounding=ROUND_HALF_UP)
            )
        else:
            value = Decimal(str(token)) * 100
            if not value.is_finite() or value < 0 or value != value.to_integral_value():
                raise ValueError
            deposit = int(value)
    except (KeyError, ValueError, InvalidOperation, TypeError):
        raise RentalConflict(
            "The owner must configure explicit valid price and deposit terms.",
            code="offer_terms_incomplete",
        )
    return rent, deposit


def money(amount):
    return {"amount_minor": amount, "currency": "EGP", "exponent": 2}


def criteria(raw):
    if not isinstance(raw, dict):
        raise ValidationError({"criteria": "Supply housing criteria."})
    city = get_object_or_404(City, id=raw.get("city_id"))
    if raw.get("district_ids", []) != []:
        raise ValidationError(
            {"district_ids": "District IDs are not supported by this catalog."}
        )
    scope = raw.get("rental_scope", "")
    period = raw.get("price_period", "monthly")
    if scope not in {
        "",
        "entire_property",
        "room",
        "room_group",
        "bed",
    } or period not in {"daily", "weekly", "monthly", "yearly"}:
        raise ValidationError({"criteria": "Unsupported rental scope or price period."})
    low = money_minor(raw["budget_min"]) if raw.get("budget_min") else None
    high = money_minor(raw["budget_max"]) if raw.get("budget_max") else None
    if low is not None and high is not None and low > high:
        raise ValidationError(
            {"budget_max": "Maximum must be at least the minimum budget."}
        )
    start = civil_date(raw.get("start_on"), "start_on", future=True)
    end = civil_date(raw["end_on"], "end_on") if raw.get("end_on") else None
    if end and end <= start:
        raise ValidationError({"end_on": "End date must follow start date."})
    people = raw.get("people", 1)
    if type(people) is not int or not 1 <= people <= 20:
        raise ValidationError({"people": "Use an integer between 1 and 20."})
    furnished = raw.get("furnished")
    if furnished is not None and type(furnished) is not bool:
        raise ValidationError({"furnished": "Use a boolean or null."})
    amenities = raw.get("amenities", [])
    supported = {
        "wifi",
        "elevator",
        "garage",
        "security",
        "balcony",
        "air_conditioning",
        "near_metro",
        "natural_gas",
        "electricity_meter",
        "water_meter",
    }
    if not isinstance(amenities, list) or any(
        not isinstance(x, str) or x.removeprefix("has_") not in supported
        for x in amenities
    ):
        raise ValidationError(
            {"amenities": "Use supported catalog amenity identifiers."}
        )
    amenities = [x.removeprefix("has_") for x in amenities]
    return {
        "city_id": str(city.id),
        "city": {"id": str(city.id), "name": city.name, "slug": city.slug},
        "district_ids": [],
        "rental_scope": scope,
        "property_type": raw.get("property_type", ""),
        "budget_min": money(low) if low is not None else None,
        "budget_max": money(high) if high is not None else None,
        "price_period": period,
        "start_on": str(start),
        "end_on": str(end) if end else "",
        "people": people,
        "amenities": amenities,
        "furnished": furnished,
    }


def criteria_payload(value):
    def major(key):
        amount = (value.get(key) or {}).get("amount_minor")
        return str(Decimal(amount) / 100) if amount is not None else ""

    return {
        "city": value.get("city", {}),
        "filters": {
            "city": value.get("city_id", ""),
            "rental_scope": value.get("rental_scope", ""),
            "property_type": value.get("property_type", ""),
            "price_period": value.get("price_period", "monthly"),
            "price_min": major("budget_min"),
            "price_max": major("budget_max"),
            "amenities": value.get("amenities", []),
            "is_furnished": (
                ""
                if value.get("furnished") is None
                else str(value["furnished"]).lower()
            ),
        },
        "start_on": value.get("start_on", ""),
        "end_on": value.get("end_on", ""),
        "people": value.get("people", 1),
        "area_note": "",
    }


def purge_expired_discovery():
    from ..models import IdempotencyRecord
    from ..planning_models import CommuteSearch, TenantAssistantTurn

    now = timezone.now()
    searches = CommuteSearch.objects.filter(expires_at__lte=now)
    turns = TenantAssistantTurn.objects.filter(expires_at__lte=now)
    identifiers = list(searches.values_list("id", flat=True)) + list(
        turns.values_list("id", flat=True)
    )
    IdempotencyRecord.objects.filter(result_subject_id__in=identifiers).update(
        response_data={
            "code": "private_result_expired",
            "message": "This private result expired. Submit a fresh request.",
        },
        response_status=410,
    )
    searches.update(query={}, matches=[])
    turns.update(reply={}, session_id="")
    return len(identifiers)


def validate_payload_types(value, depth=0):
    """Validate nested structural types before membership checks and ORM lookups."""
    if depth > 12:
        raise ValidationError("The request is nested too deeply.")
    strings = {
        "action",
        "decision",
        "kind",
        "status",
        "visibility",
        "mode",
        "language",
        "rental_scope",
        "price_period",
        "property_type",
        "time_kind",
        "timezone",
        "local_time",
        "appointment_at",
        "condition",
        "token",
        "name",
        "title",
        "reason",
        "note",
        "label",
        "space",
        "start_on",
        "end_on",
        "requested_on",
        "inspected_on",
    }
    mappings = {
        "selection",
        "terms",
        "criteria",
        "filters",
        "habits",
        "preferences",
        "contributions",
        "proposal",
        "location",
        "amount",
        "total",
        "budget_min",
        "budget_max",
    }
    string_lists = {
        "participant_ids",
        "evidence_ids",
        "disclosed",
        "amenities",
        "room_ids",
        "room_names",
        "rules",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            if item is None:
                continue
            if key in strings or key.endswith("_id") or key == "id":
                if not isinstance(item, str):
                    raise ValidationError({key: "Use a string."})
            if key in mappings and not isinstance(item, dict):
                raise ValidationError({key: "Use an object."})
            if key in string_lists and (
                not isinstance(item, list) or any(not isinstance(x, str) for x in item)
            ):
                raise ValidationError({key: "Use a list of strings."})
            validate_payload_types(item, depth + 1)
    elif isinstance(value, list):
        for item in value:
            validate_payload_types(item, depth + 1)
