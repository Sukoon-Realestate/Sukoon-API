"""Planning discovery views: catalog matches."""

from decimal import Decimal, InvalidOperation
from rest_framework.exceptions import ValidationError
from ..services.planning import offer_money, public_properties
from ..services.rental_phase2 import RentalConflict
from ..services.tenancy_invitations import resolve_offer_snapshot


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
