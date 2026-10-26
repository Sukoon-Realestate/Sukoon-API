"""Validate new choices against current catalogs, retaining historical references."""

from django.db import connection
from rest_framework.exceptions import ValidationError


def require_current_selections(items, *, field="city"):
    """Lock all children, then ancestors, in a stable order across multi-selects."""
    nodes = {}

    def collect(item):
        if item is None or (type(item), item.pk) in nodes:
            return
        current = type(item).objects.filter(pk=item.pk).first()
        if current is None:
            raise ValidationError(
                {field: "This catalog choice no longer exists. Refresh the choices."}
            )
        nodes[type(item), item.pk] = current
        for parent in ("university", "city", "governorate"):
            related = getattr(current, parent, None)
            if related is not None:
                collect(related)

    for item in items:
        collect(item)
    order = {
        "propertytype": -1,
        "campus": 0,
        "district": 1,
        "university": 2,
        "city": 3,
        "governorate": 4,
    }
    for model, pk in sorted(
        nodes, key=lambda key: (order[key[0]._meta.model_name], key[1])
    ):
        query = model.objects
        if connection.in_atomic_block:
            query = query.select_for_update()
        current = query.filter(pk=pk).first()
        if current is None or not getattr(
            current, "is_active", getattr(current, "active", True)
        ):
            raise ValidationError(
                {
                    field: "This catalog choice is no longer available. Refresh the choices."
                }
            )


def require_current_selection(item, *, previous=None, field="city"):
    if item is not None and (previous is None or item.pk != previous.pk):
        require_current_selections([item], field=field)
    return item


def validate_property_locations(values, previous=None):
    require_current_selection(
        values.get("property_type"),
        previous=getattr(previous, "property_type", None),
        field="property_type",
    )
    items = [
        value
        for name in ("district_catalog", "city", "governorate")
        if (value := values.get(name)) is not None
        and getattr(previous, f"{name}_id", None) != value.pk
    ]
    require_current_selections(items, field="city")
