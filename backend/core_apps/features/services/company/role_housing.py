"""Physical housing information for the exact assigned resident, without commerce."""

from django.utils.translation import get_language
from core_apps.common.translation import translate_message


def housing_title(rows):
    """Headings use only already authorized physical accommodation labels."""
    return " / ".join(
        dict.fromkeys(row["title"] for row in rows if row.get("title"))
    ) or translate_message("Your housing")


def resident_state(assignments, company_possession):
    """Company possession never proves that this employee has arrived."""
    states = {row["state"] for row in assignments}
    if "occupied" in states:
        return "occupied"
    if "arrival_pending" in states:
        return (
            "housing_preparing"
            if company_possession == "not_started"
            else "arrival_pending"
        )
    if "returned" in states:
        return "returned"
    if states == {"cancelled"}:
        return "cancelled"
    return "housing_preparing"


def assigned_housing(item, user):
    result = []
    arabic = (get_language() or "").startswith("ar")
    rows = (
        item.preparation.booking.assignments.filter(employee=user)
        .select_related("property__city", "property__governorate")
        .prefetch_related("property__images")
    )
    for row in rows:
        prop = row.property

        def location_label(value):
            return getattr(value, "name_ar" if arabic else "name_en", "") or value.name

        images = [prop.main_image] + [image.image for image in prop.images.all()]
        result.append(
            {
                "assignment_id": str(row.id),
                "property_id": str(prop.id),
                "title": prop.title,
                "unit_code": prop.unit_code,
                "floor": prop.floor,
                "address": "، ".join(
                    v
                    for v in [
                        location_label(prop.governorate),
                        location_label(prop.city),
                        prop.district,
                        prop.street,
                    ]
                    if v
                ),
                "photo_urls": list(
                    dict.fromkeys(image.url for image in images if image)
                ),
                "smoking_allowed": prop.smoking_allowed,
                "starts_on": str(row.starts_on),
                "ends_on_exclusive": str(row.ends_on_exclusive),
            }
        )
    return result
