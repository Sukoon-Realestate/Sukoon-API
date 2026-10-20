"""Optional stay search over canonical offers. Reads only: no holds or writes."""

from decimal import Decimal
from django.db.models import Case, When, Value, DecimalField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from ...student_models import Campus
from .decisions import minor
from .inventory import assert_available
from ..rental_phase2 import RentalConflict
from ..tenancy_invitations import resolve_offer_snapshot


class SearchContext(serializers.Serializer):
    campus_id = serializers.UUIDField(required=False)
    price_period = serializers.ChoiceField(choices=["monthly"], default="monthly")
    available_from = serializers.DateField(required=False)
    available_until = serializers.DateField(required=False)
    student_people = serializers.IntegerField(default=1, min_value=1, max_value=100)
    budget_basis = serializers.ChoiceField(
        choices=["per_person", "whole_group"], default="per_person"
    )

    def validate(self, data):
        start, end = data.get("available_from"), data.get("available_until")
        if end and (not start or end <= start):
            raise ValidationError({"available_until": "Choose an end after the start."})
        return data


class RentalSearchContext(serializers.Serializer):
    rental_search_version = serializers.ChoiceField(choices=["1"])
    price_period = serializers.ChoiceField(
        choices=["daily", "weekly", "monthly", "yearly"], required=False
    )
    available_from = serializers.DateField(required=False)
    available_until = serializers.DateField(required=False)
    occupants = serializers.IntegerField(default=1, min_value=1, max_value=20)

    def validate(self, data):
        start, end = data.get("available_from"), data.get("available_until")
        if bool(start) != bool(end) or (start and end <= start):
            raise ValidationError(
                {"available_until": "Choose both dates, with an end after the start."}
            )
        return data


def matching_offers(prop, context, query):
    """Price bounds apply to the selected offer, never the property's legacy price."""
    matches = {}
    for offer in (prop.rental_inventory or {}).get("offers", []):
        if offer.get("archived") or offer.get("availability") != "available":
            continue
        if (
            query.get("rental_scope")
            and offer.get("rental_scope") != query["rental_scope"]
        ):
            continue
        terms = offer.get("terms", {})
        period = query.get("price_period") or (
            "monthly" if "student_people" in context else ""
        )
        if period and terms.get("price_period") != period:
            continue
        rent = minor(terms.get("price"))
        if rent is None:
            continue
        whole = offer.get("rental_scope") in {"entire_property", "room_group"}
        people = context.get("student_people", context.get("occupants", 1))
        # Independent rooms/beds remain individual offers, not a promise for a group.
        comparison = Decimal(rent)
        if whole and context.get("budget_basis") == "per_person":
            comparison /= people
        elif not whole and context.get("budget_basis") == "whole_group":
            comparison *= people
        if query.get("price_min") and comparison < Decimal(query["price_min"]) * 100:
            continue
        if query.get("price_max") and comparison > Decimal(query["price_max"]) * 100:
            continue
        try:
            _, snapshot = resolve_offer_snapshot(prop, offer["id"], offer["revision"])
            if (
                (whole or "occupants" in context)
                and snapshot.get("capacity") is not None
                and snapshot["capacity"] < people
            ):
                continue
            # A date-less search must still respect habitability and retired inventory.
            from .habitability import assert_habitable

            assert_habitable(prop, snapshot)
            if prop.retired_at:
                continue
            if context.get("available_from") and context.get("available_until"):
                from ..rental_phase2 import add_months

                minimum = max(1, int(terms.get("rental_period") or 1))
                if terms.get("price_period") == "monthly" and context[
                    "available_until"
                ] < add_months(context["available_from"], minimum):
                    continue
                assert_available(
                    prop,
                    snapshot,
                    context["available_from"],
                    context["available_until"],
                )
        except (RentalConflict, ValidationError):
            continue
        matches[str(offer["id"])] = comparison
    return matches


def filter_properties(queryset, query, request=None):
    ordinary = "rental_search_version" in query
    if ordinary and query.get("student_search") == "true":
        raise ValidationError({"rental_search_version": "Choose one search context."})
    body = (RentalSearchContext if ordinary else SearchContext)(data=query)
    body.is_valid(raise_exception=True)
    context = body.validated_data
    if context.get("campus_id"):
        campus = Campus.objects.filter(
            id=context["campus_id"], active=True, university__active=True
        ).first()
        if not campus:
            raise ValidationError({"campus_id": "Choose a current campus or clear it."})
        # City match only. This is never a commute-time or radius guarantee.
        queryset = queryset.filter(city_id=campus.city_id)
    candidates = queryset.exclude(rental_inventory__isnull=True)
    # Bound the optional physical-inventory scan; never silently truncate results.
    if candidates.count() > 500:
        raise ValidationError(
            {
                "rental_search": "Narrow the city, area or accommodation type before checking stay dates."
            }
        )
    matches = {}
    for prop in candidates.iterator(chunk_size=100):
        offers = matching_offers(prop, context, query)
        if offers:
            matches[prop.pk] = offers
    if request is not None:
        request.student_offer_matches = matches
        request.rental_search_version = 1 if ordinary else None
    return queryset.filter(pk__in=matches).annotate(
        student_comparison_price=Case(
            *[
                When(pk=pk, then=Value(min(prices.values())))
                for pk, prices in matches.items()
            ],
            default=Value(None),
            output_field=DecimalField(max_digits=24, decimal_places=8),
        )
    )
