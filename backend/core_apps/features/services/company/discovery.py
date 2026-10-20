"""Read-only suitability against the same exact scope used by selection."""

from math import asin, cos, radians, sin, sqrt
from uuid import UUID

from django.utils import timezone
from rest_framework.exceptions import ValidationError

from core_apps.properties.services.property import PropertyService
from . import offers
from .request_period import monthly_periods
from ..rental_phase2 import RentalConflict


def requirement_catalog(language=None):
    catalog = PropertyService.get_filter_options(language)["amenities"]
    return [
        {
            "value": "furnished",
            "query_parameter": "is_furnished",
            "label": "Furnished" if str(language).startswith("en") else "مفروش",
        },
        *catalog,
    ]


def distance_km(a, b, c, d):
    a, b, c, d = map(radians, map(float, (a, b, c, d)))
    h = sin((c - a) / 2) ** 2 + cos(a) * cos(c) * sin((d - b) / 2) ** 2
    return round(6371.0088 * 2 * asin(min(1, sqrt(h))), 2)


def suitability(offer, requirement, *, catalog=None):
    result = offers.offer_payload(
        offer, starts_on=requirement.starts_on, ends_on=requirement.ends_on_exclusive
    )
    months = monthly_periods(requirement.starts_on, requirement.ends_on_exclusive)
    rent = offer.monthly_rent_minor * months
    reasons = []
    if not result.get("eligible"):
        reasons.append(
            result.get("blocking_reason", "inventory_or_authority_unavailable")
        )
    capacity = result.get("capacity")
    if capacity is None:
        reasons.append("capacity_unknown")
    elif capacity < requirement.headcount:
        reasons.append("insufficient_capacity")
    if rent > requirement.commitment_ceiling_minor:
        reasons.append("rent_over_ceiling")
    if offer.deposit_minor > requirement.deposit_limit_minor:
        reasons.append("deposit_over_ceiling")
    facts, locations = [], []
    try:
        props = offers.resolve_scope(offer)
    except RentalConflict:
        props = []
    catalog = catalog if catalog is not None else requirement_catalog("en")
    for row in catalog:
        # These existing listing booleans mean owner-declared availability,
        # not inspection, inclusion in rent, or guaranteed service quality.
        value = (
            all(getattr(p, row["query_parameter"]) for p in props) if props else None
        )
        facts.append({"key": row["value"], "available_in_every_unit": value})
        if row["value"] in requirement.requirements and value is not True:
            reasons.append("requirement_unconfirmed:" + row["value"])
    for prop in props:
        location = {
            "property_id": str(prop.id),
            "city": prop.city.name,
            "district": prop.district,
            "latitude": str(prop.latitude) if prop.latitude is not None else None,
            "longitude": str(prop.longitude) if prop.longitude is not None else None,
        }
        distance = None
        if all(
            v is not None
            for v in (
                requirement.worksite_latitude,
                requirement.worksite_longitude,
                prop.latitude,
                prop.longitude,
            )
        ):
            distance = distance_km(
                requirement.worksite_latitude,
                requirement.worksite_longitude,
                prop.latitude,
                prop.longitude,
            )
        location["straight_line_km"] = distance
        locations.append(location)
    result.update(
        request_id=str(requirement.id),
        request_revision=requirement.revision,
        full_term_rent_minor=rent,
        rental_months=months,
        comparison_headcount=requirement.headcount,
        suitability_reasons=list(dict.fromkeys(reasons)),
        meets_requirements=not reasons,
        requirement_facts=facts,
        locations=locations,
        checked_at=timezone.now().isoformat(),
        quote_expires_at=None,  # A listing check does not create a package quote.
        other_costs_status="not_established",
        distance_basis="straight_line_not_travel_time",
    )
    return result


def query_options(params):
    def flag(key):
        raw = params.get(key, "false")
        if raw not in {"true", "false"}:
            raise ValidationError({key: "Use true or false."})
        return raw == "true"

    location = params.get("location", "").strip()
    if len(location) > 100:
        raise ValidationError({"location": "Use at most 100 characters."})
    identities = (
        params.get("offer_ids", "").split(",") if params.get("offer_ids") else []
    )
    try:
        if len(identities) > 3:
            raise ValueError()
        identities = [UUID(v) for v in identities]
    except (ValueError, TypeError):
        raise ValidationError({"offer_ids": "Compare at most three exact offer IDs."})
    return (
        flag("suitable_only"),
        flag("available_only"),
        location.casefold(),
        identities,
    )


def results(queryset, requirement, params):
    suitable, available, location, identities = query_options(params)
    if identities:
        queryset = queryset.filter(id__in=identities)
    # Monetary coarse filtering avoids inventory queries for impossible prices.
    if suitable:
        months = monthly_periods(requirement.starts_on, requirement.ends_on_exclusive)
        queryset = queryset.filter(
            monthly_rent_minor__lte=requirement.commitment_ceiling_minor // months,
            deposit_minor__lte=requirement.deposit_limit_minor,
        )
    # Exact-scope/date suitability cannot be inferred from a directory or a
    # building's aggregate capacity. Filter before pagination, never hide just
    # the unsuitable rows on the current page.
    rows = []
    catalog = requirement_catalog("en")
    for offer in queryset.order_by("-created_at", "id").iterator(chunk_size=100):
        row = suitability(offer, requirement, catalog=catalog)
        if suitable and not row["meets_requirements"]:
            continue
        if available and row.get("available_for_dates") is not True:
            continue
        if location and not any(
            location in (v["city"] + " " + v["district"]).casefold()
            for v in row["locations"]
        ):
            continue
        rows.append(row)
    return rows
