"""Read-only, single-filter alternatives evaluated before pagination."""

from copy import copy
from django.db import DatabaseError

from django.utils import timezone


# Visibility, authority, offer scope and location are never relaxed implicitly.
RELAXABLE_FILTERS = (
    "price_max",
    "price_min",
    "bedrooms",
    "bedrooms_min",
    "bathrooms",
    "is_furnished",
    "has_wifi",
    "has_elevator",
    "has_garage",
    "has_balcony",
    "has_air_conditioning",
    "near_metro",
)


def search_suggestions(view):
    request = view.request
    suggestions = []
    if request.query_params.get("new_updated_only") == "true":
        return {"read_at": timezone.now().isoformat(), "suggestions": []}
    for field in RELAXABLE_FILTERS:
        if not request.query_params.get(field):
            continue
        params = request.query_params.copy()
        params.pop(field, None)
        params.pop("page", None)
        for key in ("saved_search_id", "saved_search_workspace", "saved_search_read_id", "new_updated_only"):
            params.pop(key, None)
        candidate_request = copy(request)
        candidate_request._request = copy(request._request)
        candidate_request._request.GET = params
        candidate_view = copy(view)
        candidate_view.request = candidate_request
        # Reuse all public-access, account and canonical filter checks. Counts
        # are never obtained from a page or a client-side approximation.
        try:
            count = candidate_view.filter_queryset(
                candidate_view.get_queryset()
            ).count()
        except DatabaseError:
            return {
                "read_at": timezone.now().isoformat(),
                "suggestions": [],
                "unavailable": True,
            }
        if count:
            suggestions.append({"remove_filter": field, "result_count": count})
        if len(suggestions) == 3:
            break
    return {"read_at": timezone.now().isoformat(), "suggestions": suggestions}
