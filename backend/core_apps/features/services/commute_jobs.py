"""Durable route searches. No HTTP call runs inside a database transaction."""

from datetime import datetime, timezone as utc_timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from ..planning_models import CommuteSearch
from .planning_providers import DiscoveryUnavailable, route_matrix


def destination_constraints(data):
    result = []
    for value in data["destinations"]:
        local = value.get("local_time") or data.get("local_time", "")
        zone_name = value.get("timezone", data.get("timezone", "Africa/Cairo"))
        kind = value.get("time_kind", data.get("time_kind", "depart_at"))
        try:
            zone = ZoneInfo(zone_name)
            naive = datetime.fromisoformat(local)
            if naive.tzinfo is not None or "T" not in local:
                raise ValueError
            aware = naive.replace(tzinfo=zone)
            # A missing or repeated civil hour needs an explicit corrected choice.
            if (
                aware.astimezone(utc_timezone.utc).astimezone(zone).replace(tzinfo=None)
                != naive
            ):
                raise ValueError
            if aware.utcoffset() != naive.replace(tzinfo=zone, fold=1).utcoffset():
                raise ValueError
        except (ValueError, TypeError, ZoneInfoNotFoundError):
            raise ValidationError(
                {"local_time": "Choose an unambiguous existing local date and time."}
            ) from None
        if aware <= timezone.now():
            raise ValidationError({"local_time": "Choose a future journey time."})
        if value["mode"] not in settings.PLANNING_ROUTE_MODES or kind not in {
            "depart_at",
            "arrive_by",
        }:
            raise ValidationError(
                {"mode": "Choose a supported journey mode and timing."}
            )
        if kind == "arrive_by" and value["mode"] != "transit":
            raise ValidationError(
                {"time_kind": "Arrival-time routing is supported only for transit."}
            )
        result.append(
            {
                **value,
                "time_kind": kind,
                "timezone": zone_name,
                "local_time": local,
                "at": aware.astimezone(utc_timezone.utc).isoformat(),
            }
        )
    return result


def run_commute(search_id):
    from ..planning_discovery_views import catalog_matches
    from .planning import enabled_services
    from .planning_providers import ready_services

    with transaction.atomic():
        item = CommuteSearch.objects.select_for_update().get(id=search_id)
        if item.status != "queued" or item.expires_at <= timezone.now():
            return
        item.status, item.started_at = "running", timezone.now()
        item.save(update_fields=["status", "started_at", "updated_at"])
        query = item.query
    matches, unknown, processed = [], 0, 0
    try:
        if (
            "commute" not in ready_services(enabled_services())
            or not item.user.is_active
            or not item.user.is_verified
        ):
            raise DiscoveryUnavailable(code="capability_unavailable")
        candidates = []
        for prop, offers in catalog_matches(query.get("filters", {})):
            candidates.append((prop, offers))
            if len(candidates) > settings.PLANNING_ROUTE_MAX_ORIGINS:
                raise DiscoveryUnavailable(code="search_scope_too_large")
        CommuteSearch.objects.filter(pk=item.pk, status="running").update(
            total_count=len(candidates)
        )
        for offset in range(0, len(candidates), 100):
            if not CommuteSearch.objects.filter(
                pk=item.pk, status="running", expires_at__gt=timezone.now()
            ).exists():
                return
            batch = candidates[offset : offset + 100]
            located = [
                (p, offers)
                for p, offers in batch
                if p.latitude is not None and p.longitude is not None
            ]
            unknown += len(batch) - len(located)
            estimates = [[] for _ in located]
            for destination in query["destinations"]:
                if not located:
                    continue
                if not CommuteSearch.objects.filter(
                    pk=item.pk, status="running", expires_at__gt=timezone.now()
                ).exists():
                    return
                response = route_matrix(
                    [
                        {"latitude": float(p.latitude), "longitude": float(p.longitude)}
                        for p, _ in located
                    ],
                    destination,
                )
                for i, route in enumerate(response):
                    estimates[i].append(
                        {
                            **route,
                            "destination_label": destination["label"],
                            "limit_seconds": destination["limit_minutes"] * 60,
                            "mode": destination["mode"],
                            "requested_at": destination["at"],
                            "time_kind": destination["time_kind"],
                            "origin_precision": "listing_coordinate",
                            "estimated_at": timezone.now().isoformat(),
                            "explanation": "Google Routes",
                        }
                    )
            for (prop, offers), journeys in zip(located, estimates):
                if any(
                    x["duration_seconds"] is None or x.get("timing_fallback")
                    for x in journeys
                ):
                    unknown += 1
                elif all(x["duration_seconds"] <= x["limit_seconds"] for x in journeys):
                    matches.append(
                        {
                            "property_id": str(prop.id),
                            "title": prop.title,
                            "offer_ids": [x["offer_id"] for x in offers],
                            "estimates": journeys,
                        }
                    )
            processed += len(batch)
            CommuteSearch.objects.filter(pk=item.pk, status="running").update(
                processed_count=processed, updated_at=timezone.now()
            )

        def score(match):
            ratios = [
                x["duration_seconds"] / x["limit_seconds"] for x in match["estimates"]
            ]
            return (
                (max(ratios), sum(ratios))
                if query.get("balance")
                else (sum(ratios), max(ratios))
            ) + (match["property_id"],)

        matches.sort(key=score)
        CommuteSearch.objects.filter(
            pk=item.pk, status="running", expires_at__gt=timezone.now()
        ).update(
            matches=matches,
            unknown_count=unknown,
            coverage="partial" if unknown else "full_catalog",
            status="succeeded",
            revision=item.revision + 1,
            updated_at=timezone.now(),
        )
    except DiscoveryUnavailable as exc:
        CommuteSearch.objects.filter(pk=item.pk, status="running").update(
            status="failed",
            failure_code=str(exc.get_codes()),
            coverage="unavailable",
            matches=[],
            unknown_count=unknown,
            revision=item.revision + 1,
            updated_at=timezone.now(),
        )
    except Exception:
        # Persist a truthful terminal failure; do not strand a running search or log destinations.
        CommuteSearch.objects.filter(pk=item.pk, status="running").update(
            status="failed",
            failure_code="search_failed",
            coverage="unavailable",
            matches=[],
            revision=item.revision + 1,
            updated_at=timezone.now(),
        )
        raise
