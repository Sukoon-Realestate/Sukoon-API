"""Planning discovery views: commute searches."""

import math
from datetime import timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_time
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from ..planning_models import CommuteSearch
from ..providers import fake_provider_available
from ..services.planning_providers import provider_budget
from ..services.commute_jobs import destination_constraints
from ..services.planning import mutate, planning_api, text_field
from ..services.rental_phase2 import RentalConflict
from .catalog_matches import catalog_matches, commute_payload
from .mock_duration import _mock_duration


@planning_api(["POST"], "commute")
def commute_searches(request):
    def apply(_, revision):
        destinations = request.data.get("destinations")
        if not isinstance(destinations, list) or not 1 <= len(destinations) <= 2:
            raise ValidationError({"destinations": "Supply one or two destinations."})
        for item in destinations:
            if not isinstance(item, dict):
                raise ValidationError(
                    {"destinations": "Every destination must be an object."}
                )
            text_field(item, "label", required=True, limit=100)
            location = item.get("location")
            if not isinstance(location, dict):
                raise ValidationError(
                    {"location": "Latitude and longitude are required."}
                )
            for key, maximum in (("latitude", 90), ("longitude", 180)):
                value = location.get(key)
                if (
                    type(value) not in {int, float}
                    or not math.isfinite(value)
                    or abs(value) > maximum
                ):
                    raise ValidationError({"location": "Coordinates are out of range."})
            if (
                item.get("mode") not in {"driving", "walking", "cycling", "transit"}
                or type(item.get("limit_minutes")) is not int
                or not 1 <= item["limit_minutes"] <= 360
            ):
                raise ValidationError(
                    {
                        "destinations": "Supply a supported mode and a limit from 1 to 360 minutes."
                    }
                )
        local_time = request.data.get("local_time", "")
        try:
            valid_time = isinstance(local_time, str) and (
                parse_time(local_time) or parse_datetime(local_time)
            )
            ZoneInfo(request.data.get("timezone", ""))
        except (ValueError, TypeError, ZoneInfoNotFoundError):
            valid_time = None
        if (
            not valid_time
            or request.data.get("time_kind") not in {"depart_at", "arrive_by"}
            or request.data.get("hard_limits") is not True
            or type(request.data.get("balance")) is not bool
        ):
            raise ValidationError(
                "Supply a local time, IANA timezone, supported time_kind, boolean balance, and hard_limits=true."
            )
        mock = fake_provider_available() and getattr(
            settings, "PLANNING_MOCK_DISCOVERY", False
        )
        if not mock:
            constraints = destination_constraints(request.data)
            # Validate filters before queueing; the worker rechecks inventory at execution.
            next(catalog_matches(request.data.get("filters", {})), None)
            provider_budget(request.user, "commute")
            item = CommuteSearch.objects.create(
                user=request.user,
                query={
                    "destinations": constraints,
                    "balance": request.data["balance"],
                    "filters": request.data.get("filters", {}),
                },
                coverage="pending",
                provider="google_routes",
                status="queued",
                expires_at=timezone.now() + timedelta(minutes=30),
            )
            from ..tasks import process_commute_search

            transaction.on_commit(
                lambda: process_commute_search.delay(str(item.id)), robust=True
            )
            return item
        matches, unknown = [], 0
        for prop, offers in catalog_matches(request.data.get("filters", {})):
            estimates = []
            for destination in destinations:
                duration = _mock_duration(prop, destination) if mock else None
                estimates.append(
                    {
                        "destination_label": destination["label"],
                        "duration_seconds": duration,
                        "limit_seconds": destination["limit_minutes"] * 60,
                        "status": "ok" if duration is not None else "unknown",
                        "explanation": (
                            "API mock estimate; not a road or public transport route."
                            if duration is not None
                            else "No verified route is available."
                        ),
                    }
                )
            if any(x["duration_seconds"] is None for x in estimates):
                unknown += 1
                continue
            if all(x["duration_seconds"] <= x["limit_seconds"] for x in estimates):
                matches.append(
                    {
                        "property_id": str(prop.id),
                        "title": prop.title,
                        "offer_ids": [x["offer_id"] for x in offers],
                        "estimates": estimates,
                    }
                )

        def score(match):
            ratios = [
                x["duration_seconds"] / x["limit_seconds"] for x in match["estimates"]
            ]
            return (
                (max(ratios), sum(ratios))
                if request.data["balance"]
                else (sum(ratios), max(ratios))
            ) + (match["property_id"],)

        matches.sort(key=score)
        return CommuteSearch.objects.create(
            user=request.user,
            query={
                key: request.data[key]
                for key in (
                    "destinations",
                    "local_time",
                    "time_kind",
                    "timezone",
                    "balance",
                    "filters",
                )
                if key in request.data
            },
            coverage="full_catalog",
            provider="mock_haversine" if mock else "unconfigured",
            matches=matches,
            unknown_count=unknown,
            expires_at=timezone.now() + timedelta(minutes=30),
        )

    return mutate(
        request, "commute.create", lambda: None, apply, commute_payload, creating=True
    )


def _commute(user, search_id):
    item = get_object_or_404(CommuteSearch, id=search_id, user=user)
    if item.expires_at <= timezone.now():
        raise RentalConflict(
            "This private commute search expired. Submit a fresh search.",
            code="search_expired",
        )
    return item


@planning_api(["GET"], "commute")
def commute_detail(request, search_id):
    return Response(commute_payload(_commute(request.user, search_id)))
