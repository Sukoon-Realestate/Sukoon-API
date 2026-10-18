"""One district contract for requests, matching, and read projections."""

from uuid import UUID
from rest_framework.exceptions import ValidationError
from core_apps.properties.models import District


def validate_districts(city, raw):
    if (
        not isinstance(raw, list)
        or len(raw) > 100
        or any(not isinstance(x, str) for x in raw)
    ):
        raise ValidationError({"district_ids": "Use a bounded list of district UUIDs."})
    try:
        identities = list(dict.fromkeys(str(UUID(x)) for x in raw))
    except (ValueError, TypeError):
        raise ValidationError({"district_ids": "Use district catalog UUIDs."})
    rows = {
        str(x.id): x
        for x in District.objects.filter(id__in=identities, city=city, is_active=True)
    }
    if len(rows) != len(identities):
        raise ValidationError(
            {
                "district_ids": "Refresh and choose active districts belonging to the selected city."
            }
        )
    return identities, [
        {
            "id": value,
            "city_id": str(city.id),
            "name": rows[value].name,
            "is_active": True,
        }
        for value in identities
    ]


def district_projection(criteria):
    identities = criteria.get("district_ids", [])
    # Preserve historical IDs and names, including deleted or inactive choices.
    current = {
        str(x.id): x
        for x in District.objects.filter(id__in=identities).select_related("city")
    }
    historical = {x["id"]: x for x in criteria.get("districts", [])}
    return [
        {
            "id": value,
            "city_id": criteria.get("city_id", ""),
            "name": (
                current[value].name
                if value in current
                else historical.get(value, {}).get("name", "")
            ),
            "is_active": value in current
            and current[value].is_active
            and str(current[value].city.id) == criteria.get("city_id"),
        }
        for value in identities
    ]


def district_matches(prop, criteria):
    identities = criteria.get("district_ids", [])
    # Empty explicitly means any district in this city, including unmapped legacy properties.
    return not identities or (
        prop.district_catalog_id is not None
        and str(prop.district_catalog.id) in identities
    )


def filter_districts(queryset, criteria):
    identities = criteria.get("district_ids", [])
    return (
        queryset.filter(district_catalog__id__in=identities) if identities else queryset
    )
