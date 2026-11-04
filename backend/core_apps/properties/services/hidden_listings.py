"""Account-scoped search preferences; never restrict direct resource access."""

from django.db.models import Q, Case, When, Value, F, DecimalField
from django.utils import timezone
from ..models import HiddenListingPreference


def active_preferences(user):
    return HiddenListingPreference.objects.filter(user=user, hidden=True).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
    )


def eligible_offer_ids(prop):
    from core_apps.features.services.rental_lifecycle.habitability import (
        restricted_keys,
        offer_restricted,
    )

    restricted = restricted_keys(prop)
    return {
        str(o.get("id"))
        for o in (prop.rental_inventory or {}).get("offers", [])
        if not o.get("archived")
        and o.get("availability") == "available"
        and not offer_restricted(prop, o, restricted)
    }


def apply_hidden_listings(queryset, request):
    if (not request.user.is_authenticated
        or request.query_params.get("workspace", "individual") not in {"individual", "owner"}
        or request.query_params.get("student_search") == "true"
        or request.headers.get("X-Sukoon-Company-Id")):
        return queryset
    rows = list(active_preferences(request.user).values_list("property_id", "offer_id"))
    whole = {pk for pk, offer in rows if not offer}
    queryset = queryset.exclude(pk__in=whole)
    offers = {}
    for pk, offer in rows:
        if offer and pk not in whole:
            offers.setdefault(pk, set()).add(offer)
    if not offers:
        return queryset
    from ..serializers.property_parts.property_list_serializer import (
        build_rental_summary,
    )

    matching = dict(getattr(request, "student_offer_matches", {}))
    excluded, prices = [], []
    for prop in queryset.filter(pk__in=offers).iterator(chunk_size=100):
        ids = eligible_offer_ids(prop)
        previous = matching.get(prop.pk)
        if previous is not None:
            ids &= set(previous)
        ids -= offers[prop.pk]
        summary = build_rental_summary(prop, ids)
        if not summary or not summary["eligible_count"]:
            excluded.append(prop.pk)
            continue
        matching[prop.pk] = {key: previous[key] if previous else 0 for key in ids}
        if previous:
            prices.append(When(pk=prop.pk, then=Value(min(matching[prop.pk].values()))))
    request.listing_offer_matches = matching
    queryset = queryset.exclude(pk__in=excluded)
    if prices and "student_comparison_price" in queryset.query.annotations:
        queryset = queryset.annotate(
            student_comparison_price=Case(
                *prices,
                default=F("student_comparison_price"),
                output_field=DecimalField(max_digits=24, decimal_places=8)
            )
        )
    return queryset
