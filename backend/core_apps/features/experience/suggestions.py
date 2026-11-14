"""Fresh suggestions and opt-in push over the existing durable event outbox."""

from core_apps.features.http import ActionPolicy, FeatureAPIView

import hashlib
from datetime import timedelta
from types import SimpleNamespace
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..pagination import FeaturePagination
from ..renderers import FeatureJsonRenderer
from .access import require, scope_for, preferences, enabled
from .action_center import rows as actions, deadline
from .models import ExperiencePreferences, ExperienceDismissal, DiscoveryInteraction


def identity(*parts):
    return hashlib.sha256(":".join(str(p) for p in parts).encode()).hexdigest()


def current(request, item):
    result = []
    disabled = set(item.ranking.get("disabled_suggestions", []))
    if "deadline" not in disabled:
        now = timezone.now()
        for row in actions(request):
            due = deadline(row["due_at"])
            if row["bucket"] == "required" and due and due <= now + timedelta(hours=24):
                phase = "overdue" if due < now else "due_soon"
                result.append(
                    {
                        **row,
                        "suggestion_kind": "deadline",
                        "phase": phase,
                        "suggestion_id": identity(row["id"], row["due_at"], phase),
                    }
                )
    if item.scope in {"individual", "student"} and "alternative" not in disabled:
        from core_apps.properties.models import SavedProperty
        from core_apps.properties.services.public_access import public_properties

        for saved in SavedProperty.objects.filter(user=request.user).select_related(
            "property"
        ):
            prop = saved.property
            available = public_properties().filter(pk=prop.pk).exists()
            if available and saved.offer_id:
                from core_apps.properties.serializers.property_parts.property_list_serializer import (
                    build_rental_summary,
                )

                summary = build_rental_summary(prop, {saved.offer_id})
                available = bool(summary and summary["eligible_count"])
            if not available:
                # Do not expose the present private description of a removed listing.
                result.append(
                    {
                        "suggestion_kind": "alternative",
                        "suggestion_id": identity("saved", saved.id),
                        "kind": "alternative",
                        "id": f"saved:{saved.id}",
                        "resource_id": str(prop.id),
                        "offer_id": saved.offer_id,
                        "title": "",
                        "bucket": "required",
                        "due_at": None,
                    }
                )
    dismissed = set(
        ExperienceDismissal.objects.filter(preferences=item).values_list(
            "identity", flat=True
        )
    )
    return [row for row in result if row["suggestion_id"] not in dismissed]


class SuggestionsView(FeatureAPIView):
    name = "Suggestions"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "suggestions",
            "suggestions",
            boundary="standard",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "suggestions",
            "suggestions",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        require("suggestions")
        item = preferences(request.user, scope_for(request))
        values = current(request, item)
        page = FeaturePagination()
        return page.get_paginated_response(page.paginate_queryset(values, request))

    def post(self, request):
        require("suggestions")
        item = preferences(request.user, scope_for(request))
        values = current(request, item)
        key = request.data.get("suggestion_id")
        if key not in {v["suggestion_id"] for v in values}:
            raise NotFound()
        ExperienceDismissal.objects.get_or_create(preferences=item, identity=key)
        return Response({"dismissed": True})


# Stable callable import for integrations; URLs use the explicit class.
suggestions = SuggestionsView.as_view()


class AlternativesView(FeatureAPIView):
    name = "Alternatives"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "suggestions",
            "alternatives",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        require("suggestions")
        scope_for(request)
        if not any(
            request.query_params.get(k)
            for k in ("city", "governorate", "district_ids", "search", "rental_scope")
        ):
            raise ValidationError(
                "Choose an area or housing filters to find alternatives."
            )
        from core_apps.properties.views.property_parts.property_list_apiview import (
            PropertyListAPIView,
        )
        from core_apps.properties.serializers import PropertyListSerializer

        view = PropertyListAPIView()
        view.request = request
        view.format_kwarg = None
        candidates = view.filter_queryset(view.get_queryset()).exclude(
            owner=request.user
        )
        from core_apps.properties.serializers.property_parts.property_list_serializer import (
            build_rental_summary,
        )

        eligible = [
            p.pk
            for p in candidates
            if not p.rental_inventory or build_rental_summary(p)["eligible_count"] > 0
        ]
        candidates = candidates.filter(pk__in=eligible)
        # Physical offers must use the same canonical eligibility filtering as search.
        if request.query_params.get("ordering") == "personalized":
            from .discovery import rank

            candidates = rank(candidates, request)
        return Response(
            {
                "results": PropertyListSerializer(
                    candidates[:3], many=True, context={"request": request}
                ).data
            }
        )


# Stable callable import for integrations; URLs use the explicit class.
alternatives = AlternativesView.as_view()


def bound_request(item):
    from ..services.company.role_context import bound_role, system_context

    parts = item.scope.split("/")
    headers = (
        {"X-Sukoon-Company-Id": parts[1], "X-Sukoon-Company-Role": parts[2]}
        if parts[0] == "company"
        else {}
    )
    request = SimpleNamespace(
        user=item.user, query_params={"workspace": parts[0]}, headers=headers
    )
    context = (
        bound_role(item.user, parts[1], parts[2])
        if parts[0] == "company"
        else system_context()
    )
    return request, context


def event_copy(event):
    item = ExperiencePreferences.objects.filter(
        pk=event.destination.get("preference_id"), user=event.recipient
    ).first()
    if not item or not enabled("suggestions"):
        raise NotFound()
    request, binding = bound_request(item)
    with binding:
        match = next(
            (
                v
                for v in current(request, item)
                if v["suggestion_id"] == event.destination.get("suggestion_id")
            ),
            None,
        )
    if match is None:
        raise NotFound()
    return {
        "title": "خطوتك القادمة في سكون / Your next step in Sukoon",
        "body": "راجع اقتراحاتك والمهام الحالية / Review your current suggestions and tasks.",
        "category": "experience",
        "push_enabled": item.suggestion_push,
    }


@shared_task
def record_suggestions():
    if not enabled("suggestions"):
        return 0
    from ..planning_models import PlanningEvent
    from rest_framework.exceptions import APIException

    count = 0
    for identifier in (
        ExperiencePreferences.objects.filter(user__is_active=True)
        .values_list("pk", flat=True)
        .iterator()
    ):
        with transaction.atomic():
            item = (
                ExperiencePreferences.objects.select_for_update()
                .select_related("user")
                .get(pk=identifier)
            )
            request, binding = bound_request(item)
            try:
                with binding:
                    values = current(request, item)
            except APIException:
                continue
            for row in values:
                # One alternative notification per day per user/workspace.
                if (
                    row["suggestion_kind"] == "alternative"
                    and PlanningEvent.objects.filter(
                        recipient=item.user,
                        destination__preference_id=item.pk,
                        destination__suggestion_kind="alternative",
                        created_at__date=timezone.localdate(),
                    ).exists()
                ):
                    continue
                parts = item.scope.split("/")
                data = {
                    "action_type": "open_experience_suggestions",
                    "event_kind": "experience_suggestion",
                    "target_id": str(item.user.id),
                    "workspace": parts[0],
                    "schema_version": "1",
                    "preference_id": item.pk,
                    "suggestion_kind": row["suggestion_kind"],
                    "suggestion_id": row["suggestion_id"],
                }
                if parts[0] == "company":
                    data.update(company_id=parts[1], company_role=parts[2])
                _, created = PlanningEvent.objects.get_or_create(
                    recipient=item.user,
                    event_key=f'experience:{item.pk}:{row["suggestion_id"]}',
                    defaults={"destination": data},
                )
                count += int(created)
    return count


@shared_task
def purge_interactions():
    return DiscoveryInteraction.objects.filter(
        day__lt=timezone.localdate() - timedelta(days=29)
    ).delete()[0]
