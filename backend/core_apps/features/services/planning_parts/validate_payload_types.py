"""Planning: validate payload types."""

from decimal import Decimal
from functools import wraps
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from ...renderers import FeatureJsonRenderer
from .selection_payload import require_planning


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
        "area_note": value.get("area_note", ""),
    }


def purge_expired_discovery():
    from ...models import IdempotencyRecord
    from ...planning_models import CommuteSearch, TenantAssistantTurn

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
        "vote",
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
        "importance",
        "details",
        "search_context",
        "context",
    }
    string_lists = {
        "participant_ids",
        "evidence_ids",
        "disclosed",
        "share_fields",
        "reason_categories",
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


def planning_api(methods, capability, *, typed=False):
    def decorate(fn):
        @api_view(methods)
        @permission_classes([IsAuthenticated])
        @renderer_classes([FeatureJsonRenderer])
        @wraps(fn)
        def endpoint(request, *args, **kwargs):
            require_planning(request.user, capability)
            if request.method == "POST" and not isinstance(request.data, dict):
                raise ValidationError("Supply a JSON object.")
            if request.method == "POST" and not typed:
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
