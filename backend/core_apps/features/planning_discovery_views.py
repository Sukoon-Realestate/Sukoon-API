import math
import re
from itertools import islice
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.db import transaction
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_time
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core_apps.properties.models import City
from .planning_models import CommuteSearch, TenantAssistantTurn
from .providers import fake_provider_available
from .services.planning_providers import (
    mock_discovery,
    extract_criteria,
    provider_budget,
)
from .services.commute_jobs import destination_constraints
from .services.commands import command_identity
from .services.rental_phase2 import replay_operation, fingerprint
from .services.planning import (
    money,
    mutate,
    offer_money,
    page,
    planning_api,
    public_properties,
    text_field,
)
from .services.rental_phase2 import RentalConflict
from .services.tenancy_invitations import resolve_offer_snapshot


def catalog_matches(filters):
    """Filter actual offer records before routing or pagination."""
    if not isinstance(filters, dict):
        raise ValidationError({"filters": "Supply a filter object."})
    text_filters = {
        "city",
        "governorate",
        "district",
        "rental_scope",
        "property_type",
        "price_period",
        "price_min",
        "price_max",
        "suitable_for",
        "bedrooms",
        "bathrooms",
        "search",
        "ordering",
    }
    if any(
        key in filters and not isinstance(filters[key], (str, int, float))
        for key in text_filters
    ):
        raise ValidationError(
            {"filters": "Filter identifiers and values must be scalar values."}
        )
    if (
        set(filters)
        - text_filters
        - {
            "page",
            "page_size",
            "amenities",
            "is_furnished",
            "is_verified",
            "smoking_allowed",
        }
    ):
        raise ValidationError({"filters": "Unsupported search filters."})
    properties = (
        public_properties()
        .select_related("city", "property_type")
        .order_by("-created_at", "pkid")
    )
    for field in ("city", "governorate"):
        if filters.get(field):
            properties = properties.filter(**{f"{field}__id": filters[field]})
    for field in ("property_type", "district", "suitable_for"):
        if filters.get(field):
            properties = properties.filter(
                **{
                    (
                        "property_type__slug" if field == "property_type" else field
                    ): filters[field]
                }
            )
    for field in ("is_furnished", "smoking_allowed", "is_verified"):
        if filters.get(field) not in (None, ""):
            value = filters[field]
            if value not in (True, False, "true", "false"):
                raise ValidationError({field: "Use true or false."})
            properties = properties.filter(**{field: value in (True, "true")})
    for field in ("bedrooms", "bathrooms"):
        if filters.get(field) not in (None, ""):
            try:
                number = int(filters[field])
            except (TypeError, ValueError):
                raise ValidationError({field: "Use a positive integer."})
            if number < 1:
                raise ValidationError({field: "Use a positive integer."})
            properties = properties.filter(**{field: number})
    if filters.get("search"):
        properties = properties.filter(title__icontains=str(filters["search"])[:160])
    amenities = filters.get("amenities", [])
    allowed_amenities = {
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
        not isinstance(x, str) or x.removeprefix("has_") not in allowed_amenities
        for x in amenities
    ):
        raise ValidationError({"amenities": "Unsupported amenity filter."})
    amenities = [x.removeprefix("has_") for x in amenities]
    for amenity in amenities:
        properties = properties.filter(
            **{amenity if amenity == "near_metro" else f"has_{amenity}": True}
        )
    limits = {}
    for name in ("price_min", "price_max"):
        if filters.get(name) not in (None, ""):
            try:
                value = Decimal(str(filters[name])) * 100
                if not value.is_finite() or value < 0:
                    raise ValueError
                limits[name] = value
            except (ValueError, TypeError, InvalidOperation):
                raise ValidationError({name: "Use a nonnegative decimal amount."})
    if limits and filters.get("price_period") not in {
        "daily",
        "weekly",
        "monthly",
        "yearly",
    }:
        raise ValidationError(
            {"price_period": "Price limits require an explicit price period."}
        )
    for prop in properties:
        offers = []
        for raw in (prop.rental_inventory or {}).get("offers", []):
            if raw.get("archived") or raw.get("availability") != "available":
                continue
            if (
                filters.get("rental_scope")
                and raw.get("rental_scope") != filters["rental_scope"]
            ):
                continue
            if (
                filters.get("price_period")
                and raw.get("terms", {}).get("price_period") != filters["price_period"]
            ):
                continue
            try:
                _, snapshot = resolve_offer_snapshot(prop, raw["id"], raw["revision"])
                rent, _ = offer_money(snapshot)
            except (ValidationError, RentalConflict):
                continue
            if rent < limits.get("price_min", 0) or rent > limits.get(
                "price_max", Decimal("Infinity")
            ):
                continue
            offers.append(snapshot)
        if offers:
            yield prop, offers


def commute_payload(item):
    return {
        "id": str(item.id),
        "revision": item.revision,
        "coverage": item.coverage,
        "provider": item.provider,
        "resolved_at": item.created_at.isoformat(),
        "expires_at": item.expires_at.isoformat(),
        "unknown_count": item.unknown_count,
        "status": item.status,
        "processed_count": item.processed_count,
        "total_count": item.total_count,
        "failure_code": item.failure_code,
    }


def _mock_duration(prop, destination):
    if prop.latitude is None or prop.longitude is None:
        return None
    latitude, longitude = (
        destination["location"]["latitude"],
        destination["location"]["longitude"],
    )
    lat1, lat2 = math.radians(float(prop.latitude)), math.radians(latitude)
    angle = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(math.radians(longitude - float(prop.longitude)) / 2) ** 2
    )
    kilometers = 6371 * 2 * math.asin(math.sqrt(min(1, max(0, angle))))
    speed = {"walking": 5, "cycling": 15, "driving": 30, "transit": 20}[
        destination["mode"]
    ]
    return math.ceil(kilometers / speed * 3600)


@planning_api(["POST"], "commute")
def commute_searches(request):
    def apply(_, revision):
        destinations = request.data.get("destinations")
        if not isinstance(destinations, list) or not 1 <= len(destinations) <= 2:
            raise ValidationError({"destinations": "Supply one or two destinations."})
        for item in destinations:
            if not isinstance(item, dict):
                raise ValidationError(
                    {"destinations": "Every destination must be an object."}
                )
            text_field(item, "label", required=True, limit=100)
            location = item.get("location")
            if not isinstance(location, dict):
                raise ValidationError(
                    {"location": "Latitude and longitude are required."}
                )
            for key, maximum in (("latitude", 90), ("longitude", 180)):
                value = location.get(key)
                if (
                    type(value) not in {int, float}
                    or not math.isfinite(value)
                    or abs(value) > maximum
                ):
                    raise ValidationError({"location": "Coordinates are out of range."})
            if (
                item.get("mode") not in {"driving", "walking", "cycling", "transit"}
                or type(item.get("limit_minutes")) is not int
                or not 1 <= item["limit_minutes"] <= 360
            ):
                raise ValidationError(
                    {
                        "destinations": "Supply a supported mode and a limit from 1 to 360 minutes."
                    }
                )
        local_time = request.data.get("local_time", "")
        try:
            valid_time = isinstance(local_time, str) and (
                parse_time(local_time) or parse_datetime(local_time)
            )
            ZoneInfo(request.data.get("timezone", ""))
        except (ValueError, TypeError, ZoneInfoNotFoundError):
            valid_time = None
        if (
            not valid_time
            or request.data.get("time_kind") not in {"depart_at", "arrive_by"}
            or request.data.get("hard_limits") is not True
            or type(request.data.get("balance")) is not bool
        ):
            raise ValidationError(
                "Supply a local time, IANA timezone, supported time_kind, boolean balance, and hard_limits=true."
            )
        mock = fake_provider_available() and getattr(
            settings, "PLANNING_MOCK_DISCOVERY", False
        )
        if not mock:
            constraints = destination_constraints(request.data)
            # Validate filters before queueing; the worker rechecks inventory at execution.
            next(catalog_matches(request.data.get("filters", {})), None)
            provider_budget(request.user, "commute")
            item = CommuteSearch.objects.create(
                user=request.user,
                query={
                    "destinations": constraints,
                    "balance": request.data["balance"],
                    "filters": request.data.get("filters", {}),
                },
                coverage="pending",
                provider="google_routes",
                status="queued",
                expires_at=timezone.now() + timedelta(minutes=30),
            )
            from .tasks import process_commute_search

            transaction.on_commit(
                lambda: process_commute_search.delay(str(item.id)), robust=True
            )
            return item
        matches, unknown = [], 0
        for prop, offers in catalog_matches(request.data.get("filters", {})):
            estimates = []
            for destination in destinations:
                duration = _mock_duration(prop, destination) if mock else None
                estimates.append(
                    {
                        "destination_label": destination["label"],
                        "duration_seconds": duration,
                        "limit_seconds": destination["limit_minutes"] * 60,
                        "status": "ok" if duration is not None else "unknown",
                        "explanation": (
                            "API mock estimate; not a road or public transport route."
                            if duration is not None
                            else "No verified route is available."
                        ),
                    }
                )
            if any(x["duration_seconds"] is None for x in estimates):
                unknown += 1
                continue
            if all(x["duration_seconds"] <= x["limit_seconds"] for x in estimates):
                matches.append(
                    {
                        "property_id": str(prop.id),
                        "title": prop.title,
                        "offer_ids": [x["offer_id"] for x in offers],
                        "estimates": estimates,
                    }
                )

        def score(match):
            ratios = [
                x["duration_seconds"] / x["limit_seconds"] for x in match["estimates"]
            ]
            return (
                (max(ratios), sum(ratios))
                if request.data["balance"]
                else (sum(ratios), max(ratios))
            ) + (match["property_id"],)

        matches.sort(key=score)
        return CommuteSearch.objects.create(
            user=request.user,
            query={
                key: request.data[key]
                for key in (
                    "destinations",
                    "local_time",
                    "time_kind",
                    "timezone",
                    "balance",
                    "filters",
                )
                if key in request.data
            },
            coverage="full_catalog",
            provider="mock_haversine" if mock else "unconfigured",
            matches=matches,
            unknown_count=unknown,
            expires_at=timezone.now() + timedelta(minutes=30),
        )

    return mutate(
        request, "commute.create", lambda: None, apply, commute_payload, creating=True
    )


def _commute(user, search_id):
    item = get_object_or_404(CommuteSearch, id=search_id, user=user)
    if item.expires_at <= timezone.now():
        raise RentalConflict(
            "This private commute search expired. Submit a fresh search.",
            code="search_expired",
        )
    return item


@planning_api(["GET"], "commute")
def commute_detail(request, search_id):
    return Response(commute_payload(_commute(request.user, search_id)))


@planning_api(["POST"], "commute")
def commute_cancel(request, search_id):
    def apply(item, revision):
        if item.status not in {"queued", "running"}:
            raise RentalConflict("This search is already complete.")
        item.status = "cancelled"
        item.matches, item.query = [], {}
        item.revision += 1
        item.save()
        return item

    return mutate(
        request,
        f"commute.cancel.{search_id}",
        lambda: get_object_or_404(
            CommuteSearch.objects.select_for_update(), id=search_id, user=request.user
        ),
        apply,
        commute_payload,
    )


@planning_api(["GET"], "commute")
def commute_results(request, search_id):
    item = _commute(request.user, search_id)
    if item.status != "succeeded":
        raise RentalConflict(
            "The route search is not complete.",
            code=item.failure_code or "search_pending",
        )
    # Recheck visibility at read time, including after moderation/withdrawal.
    current = {
        str(prop.id): {x["offer_id"] for x in offers}
        for prop, offers in catalog_matches(item.query.get("filters", {}))
    }
    matches = [
        {
            **x,
            "offer_ids": [
                offer
                for offer in x["offer_ids"]
                if offer in current.get(x["property_id"], set())
            ],
        }
        for x in item.matches
    ]
    return page(request, [x for x in matches if x["offer_ids"]], lambda x: x)


@planning_api(["POST"], "tenant_assistant")
def tenant_assistant_turns(request):
    key, _ = command_identity(request.data)
    replay = replay_operation(request.user, "assistant.turn", key, request.data)
    if replay:
        return Response(replay[0], status=replay[1])
    text = text_field(request.data, "text", required=True, limit=4000)
    language = request.data.get("language")
    if language not in {"ar", "en"} or request.data.get("retain_history") is not False:
        raise ValidationError("Use language ar/en and retain_history=false.")
    session_id = text_field(request.data, "session_id", required=True, limit=100)
    context = request.data.get("context", {})
    if not isinstance(context, dict) or set(context) - {
        "filters",
        "property_id",
        "offer_id",
        "property_ids",
    }:
        raise ValidationError(
            {"context": "Use reviewed filters and an optional exact property/offer."}
        )
    comparison_ids = context.get("property_ids", [])
    if (
        not isinstance(comparison_ids, list)
        or len(comparison_ids) > 3
        or any(not isinstance(x, str) for x in comparison_ids)
        or len(set(comparison_ids)) != len(comparison_ids)
    ):
        raise ValidationError({"context": "Compare at most three distinct properties."})
    if comparison_ids and (context.get("property_id") or context.get("offer_id")):
        raise ValidationError(
            {"context": "Choose either a comparison or an exact property and offer."}
        )
    if context.get("offer_id") and not context.get("property_id"):
        raise ValidationError({"context": "An offer requires its property."})
    # Resolve before a billable provider call. Client IDs are never authority.
    selected_ids = comparison_ids or (
        [context["property_id"]] if context.get("property_id") else []
    )
    selected_properties = [
        get_object_or_404(public_properties(), id=x) for x in selected_ids
    ]
    if request.data.get("previous_turn_id"):
        previous = get_object_or_404(
            TenantAssistantTurn,
            id=request.data["previous_turn_id"],
            user=request.user,
            session_id=session_id,
            expires_at__gt=timezone.now(),
        )
        context = {"filters": previous.reply.get("filters", {}), **context}
    extracted = None
    lock_key = None
    if not mock_discovery():
        lock_key = "planning-assistant:" + fingerprint(
            {"user": str(request.user.id), "key": key}
        )
        if not cache.add(lock_key, True, timeout=90):
            raise RentalConflict(
                "This assistant request is already processing.",
                code="operation_in_progress",
            )
        try:
            provider_budget(request.user, "assistant")
            catalog = {
                "cities": [
                    {"id": str(x.id), "name": x.name}
                    for x in City.objects.order_by("pkid")
                ],
                "amenities": [
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
                ],
            }
            extracted = extract_criteria(
                text, language, catalog, {"filters": context.get("filters", {})}
            )
            # Reject unsupported typed operators and invalid prices before using model output.
            next(catalog_matches(extracted["filters"]), None)
        except Exception:
            cache.delete(lock_key)
            raise

    def apply(_, revision):
        text = text_field(request.data, "text", required=True, limit=4000)
        session_id = text_field(request.data, "session_id", required=True, limit=100)
        language = request.data.get("language")
        if (
            language not in {"ar", "en"}
            or request.data.get("retain_history") is not False
        ):
            raise ValidationError("Use language ar/en and retain_history=false.")
        previous = None
        if request.data.get("previous_turn_id"):
            previous = get_object_or_404(
                TenantAssistantTurn,
                id=request.data["previous_turn_id"],
                user=request.user,
                session_id=session_id,
                expires_at__gt=timezone.now(),
            )
        filters = dict(context.get("filters", {}))
        city = next(
            (
                x
                for x in City.objects.order_by("pkid")
                if x.name.casefold() in text.casefold()
            ),
            None,
        )
        if city:
            filters["city"] = str(city.id)
        for token, scope in (
            ("bed", "bed"),
            ("سرير", "bed"),
            ("room", "room"),
            ("غرفة", "room"),
        ):
            if token in text.casefold():
                filters["rental_scope"] = scope
                break
        budget = re.search(
            r"(?:under|maximum|budget|أقل من|بحد أقصى|ميزانية)\s*(\d+(?:\.\d{1,2})?)",
            text,
            re.I,
        )
        unresolved = []
        period_words = {
            "daily": ("daily", "per day", "يومي", "يومياً"),
            "weekly": ("weekly", "per week", "أسبوعي"),
            "monthly": ("monthly", "per month", "شهري", "شهرياً"),
            "yearly": ("yearly", "annually", "سنوي"),
        }
        period = next(
            (
                key
                for key, words in period_words.items()
                if any(word in text.casefold() for word in words)
            ),
            None,
        )
        if period:
            filters["price_period"] = period
        if budget and period:
            filters["price_max"] = budget.group(1)
        elif budget:
            unresolved.append(
                "حدد فترة السعر لتطبيق الميزانية."
                if language == "ar"
                else "Specify the price period before applying this budget."
            )
        if extracted is not None:
            filters = extracted["filters"]
            unresolved = extracted["unresolved_requirements"]
        matches = list(islice(catalog_matches(filters), 3))
        if selected_properties:
            selected_matches = []
            for selected_prop in selected_properties:
                prop = get_object_or_404(public_properties(), pk=selected_prop.pk)
                offers = []
                for raw in (prop.rental_inventory or {}).get("offers", []):
                    if raw.get("archived") or raw.get("availability") != "available":
                        continue
                    if context.get("offer_id") and raw.get("id") != context["offer_id"]:
                        continue
                    try:
                        _, snapshot = resolve_offer_snapshot(
                            prop, raw["id"], raw["revision"]
                        )
                    except (ValidationError, RentalConflict):
                        continue
                    offers.append(snapshot)
                if context.get("offer_id") and not offers:
                    raise RentalConflict(
                        "The selected offer changed or is unavailable.",
                        code="offer_unavailable",
                    )
                selected_matches.append((prop, offers))
            matches = (
                selected_matches
                if comparison_ids
                else (
                    selected_matches
                    + [(p, o) for p, o in matches if p.pk != selected_properties[0].pk][
                        :2
                    ]
                )
            )
        ids = [str(prop.id) for prop, _ in matches]
        arabic = language == "ar"
        actions = [
            {"kind": "search", "title": "مراجعة البحث" if arabic else "Review search"}
        ]
        for prop, offers in matches:
            actions.append(
                {
                    "kind": "property",
                    "title": prop.title,
                    "property_id": str(prop.id),
                    "offer_id": (
                        context.get("offer_id", "")
                        if context.get("property_id") == str(prop.id)
                        and any(
                            x["offer_id"] == context.get("offer_id") for x in offers
                        )
                        else ""
                    ),
                }
            )
        if len(ids) >= 2:
            actions.append(
                {
                    "kind": "compare",
                    "title": "مقارنة العقارات" if arabic else "Compare properties",
                    "property_ids": ids,
                }
            )
        costs = []
        selected = next(
            (
                (prop, offer)
                for prop, offers in matches
                for offer in offers
                if str(prop.id) == context.get("property_id")
                and offer["offer_id"] == context.get("offer_id")
            ),
            None,
        )
        if selected:
            prop, selected_offer = selected
            if extracted and extracted["questions"]:
                actions.append(
                    {
                        "kind": "messageDraft",
                        "title": (
                            "Review questions for the owner"
                            if language == "en"
                            else "مراجعة الأسئلة للمالك"
                        ),
                        "property_id": str(prop.id),
                        "offer_id": selected_offer["offer_id"],
                    }
                )
            rent, deposit = offer_money(selected_offer)
            costs = [
                {
                    "label": prop.title,
                    "kind": "recurring",
                    "period": selected_offer["terms"]["price_period"],
                    "money": money(rent),
                },
                {
                    "label": "التأمين" if arabic else "Deposit",
                    "kind": "deposit",
                    "period": "",
                    "money": money(deposit),
                },
            ]
        reply = {
            "text": (
                "اقتراحات من بيانات العقارات المتاحة. راجع الفلاتر والشروط قبل المتابعة."
                if arabic
                else "Suggestions from available property records. Review filters and terms before continuing."
            ),
            "filters": filters,
            "unresolved_requirements": unresolved
            + [
                (
                    "المتطلبات غير الظاهرة في الفلاتر لم يتم التحقق منها."
                    if arabic
                    else "Requirements not represented in the filters have not been verified."
                )
            ],
            "grounded_property_ids": ids,
            "actions": actions,
            "costs": costs,
            "provider": "gemini" if extracted is not None else "catalog_rules",
            "questions": extracted["questions"] if extracted else [],
            "grounded_offers": [
                {
                    "property_id": str(prop.id),
                    "offer_id": offer["offer_id"],
                    "offer_revision": offer["offer_revision"],
                    "terms": offer["terms"],
                }
                for prop, offers in matches
                for offer in offers
            ],
            "retain_history": False,
        }
        # Keep no raw prompt; a short-lived reply supports same-key recovery.
        return TenantAssistantTurn.objects.create(
            user=request.user,
            session_id=session_id,
            previous_turn=previous,
            reply=reply,
            expires_at=timezone.now() + timedelta(hours=24),
        )

    try:
        return mutate(
            request,
            "assistant.turn",
            lambda: None,
            apply,
            lambda x: {"id": str(x.id), "revision": x.revision, **x.reply},
            creating=True,
        )
    finally:
        if lock_key:
            cache.delete(lock_key)
