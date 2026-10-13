"""Reviewed assistant context."""

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from ..planning_models import TenantAssistantTurn
from ..services.planning import public_properties


def assistant_context(request, session_id):
    context = request.data.get("context", {})
    if not isinstance(context, dict) or set(context) - {
        "filters",
        "property_id",
        "offer_id",
        "property_ids",
    }:
        raise ValidationError(
            {"context": "Use reviewed filters and an optional exact property/offer."}
        )
    comparison_ids = context.get("property_ids", [])
    if (
        not isinstance(comparison_ids, list)
        or len(comparison_ids) > 3
        or any(not isinstance(x, str) for x in comparison_ids)
        or len(set(comparison_ids)) != len(comparison_ids)
    ):
        raise ValidationError({"context": "Compare at most three distinct properties."})
    if comparison_ids and (context.get("property_id") or context.get("offer_id")):
        raise ValidationError(
            {"context": "Choose either a comparison or an exact property and offer."}
        )
    if context.get("offer_id") and not context.get("property_id"):
        raise ValidationError({"context": "An offer requires its property."})
    # Resolve before a billable provider call. Client IDs are never authority.
    selected_ids = comparison_ids or (
        [context["property_id"]] if context.get("property_id") else []
    )
    selected_properties = [
        get_object_or_404(public_properties(), id=x) for x in selected_ids
    ]
    if request.data.get("previous_turn_id"):
        previous = get_object_or_404(
            TenantAssistantTurn,
            id=request.data["previous_turn_id"],
            user=request.user,
            session_id=session_id,
            expires_at__gt=timezone.now(),
        )
        context = {"filters": previous.reply.get("filters", {}), **context}
    return context, comparison_ids, selected_properties
