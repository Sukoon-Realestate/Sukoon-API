"""Planning: criteria."""

from decimal import Decimal, InvalidOperation
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound, ValidationError
from core_apps.properties.models import City, Property, PropertyType
from ..commands import money_minor
from ..rental_phase2 import RentalConflict
from ..tenancy_invitations import resolve_offer_snapshot
from .selection_payload import (
    text_field,
    civil_date,
    public_properties,
    selection_payload,
)


def selection(request, raw, *, owned=False, lock=True):
    if (
        not isinstance(raw, dict)
        or not raw.get("offer_id")
        or type(raw.get("offer_revision")) is not int
    ):
        raise ValidationError(
            {"selection": "A property, offer and integer offer_revision are required."}
        )
    queryset = (
        Property.objects.filter(owner=request.user) if owned else public_properties()
    )
    if lock:
        queryset = queryset.select_for_update(of=("self",))
    prop = queryset.filter(id=raw.get("property_id")).first()
    if prop is None:
        raise NotFound(
            "The selected property is unavailable. Refresh and choose another property."
        )
    if (
        owned
        and not public_properties()
        .filter(pk=prop.pk, is_ownership_verified=True)
        .exists()
    ):
        raise ValidationError(
            {
                "selection": "This property must be published and its ownership verified before it can be offered."
            }
        )
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


def offer_money(snapshot):
    terms = snapshot.get("terms", {})
    try:
        value = Decimal(str(terms["price"])) * 100
        if not value.is_finite() or value <= 0 or value != value.to_integral_value():
            raise ValueError
        rent = int(value)
        token = terms.get("deposit", "")
        if token in {"", None}:
            deposit = None
        elif token in {"none", "no_deposit"}:
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


def criteria(raw, *, allow_existing_start=False, previous=None):
    if not isinstance(raw, dict):
        raise ValidationError({"criteria": "Supply housing criteria."})
    city = get_object_or_404(City, id=raw.get("city_id"))
    from .districts import validate_districts

    previous = previous or {}
    from core_apps.properties.catalog_access import require_current_selection

    property_type = raw.get("property_type", "")
    if not isinstance(property_type, str) or len(property_type) > 50:
        raise ValidationError({"property_type": "Choose a catalog property type."})
    if property_type:
        kind = PropertyType.objects.filter(slug=property_type).first()
        if kind is None:
            raise ValidationError({"property_type": "Choose a catalog property type."})
        require_current_selection(
            kind,
            previous=kind if previous.get("property_type") == property_type else None,
            field="property_type",
        )
    same_city = str(city.id) == previous.get("city_id")
    district_ids, districts = validate_districts(
        city,
        raw.get("district_ids", []),
        retained=previous.get("district_ids", []) if same_city else [],
    )
    require_current_selection(city, previous=city if same_city else None)
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
    start = civil_date(raw.get("start_on"), "start_on", future=not allow_existing_start)
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
        "district_ids": district_ids,
        "districts": districts,
        "district_scope": "selected" if district_ids else "all_city",
        "rental_scope": scope,
        "property_type": property_type,
        "budget_min": money(low) if low is not None else None,
        "budget_max": money(high) if high is not None else None,
        "price_period": period,
        "start_on": str(start),
        "end_on": str(end) if end else "",
        "people": people,
        "amenities": amenities,
        "furnished": furnished,
        "area_note": text_field(raw, "area_note", limit=300),
    }
