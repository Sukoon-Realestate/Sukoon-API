"""Reviewed assistant grounding."""

import re
from itertools import islice
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from core_apps.properties.models import City
from ..services.planning import public_properties
from ..services.rental_phase2 import RentalConflict
from ..services.tenancy_invitations import resolve_offer_snapshot
from .catalog_matches import catalog_matches


def assistant_filters(text, language, context, extracted):
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
    return filters, unresolved


def assistant_matches(filters, selected_properties, context, comparison_ids):
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
                + [(p, o) for p, o in matches if p.pk != selected_properties[0].pk][:2]
            )
        )
    return matches
