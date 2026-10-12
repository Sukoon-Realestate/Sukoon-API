import math
import re
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_time
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core_apps.properties.models import City
from .planning_models import CommuteSearch, TenantAssistantTurn
from .providers import fake_provider_available
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
    for field in ("is_furnished", "smoking_allowed"):
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


@planning_api(["GET"], "commute")
def commute_results(request, search_id):
    item = _commute(request.user, search_id)
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
        filters = {}
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
        matches = list(catalog_matches(filters))[:3]
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
                    "offer_id": offers[0]["offer_id"],
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
        if matches:
            prop, offers = matches[0]
            rent, deposit = offer_money(offers[0])
            costs = [
                {
                    "label": prop.title,
                    "kind": "recurring",
                    "period": offers[0]["terms"]["price_period"],
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
            "provider": "catalog_rules",
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

    return mutate(
        request,
        "assistant.turn",
        lambda: None,
        apply,
        lambda x: {"id": str(x.id), "revision": x.revision, **x.reply},
        creating=True,
    )
