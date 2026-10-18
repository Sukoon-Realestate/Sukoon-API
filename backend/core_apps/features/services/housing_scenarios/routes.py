"""Frozen, directional route estimates using the existing road provider adapter."""

import math
from dataclasses import dataclass, asdict
from datetime import timedelta
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from ..policy_registry import approved_policy
from ..rental_phase2 import fingerprint, RentalConflict
from ..planning_providers_parts.route_matrix import (
    route_matrix,
    provider_budget,
    DiscoveryUnavailable,
)


@dataclass(frozen=True)
class RouteEstimate:
    origin: dict
    destination: dict
    mode: str
    departure_at: str
    timezone: str
    query_digest: str
    source: str = "google_routes"
    source_version: str = "v2"
    origin_accuracy: str = "owner_reported"
    destination_accuracy: str = "coordinator_reported"
    duration_seconds: int | None = None
    distance_meters: int | None = None
    fetched_at: str | None = None
    expires_at: str | None = None
    unknown_reason: str | None = None

    def payload(self):
        result = asdict(self)
        return {
            **result,
            "minutes": (
                math.ceil(self.duration_seconds / 60)
                if self.duration_seconds is not None
                else None
            ),
            "status": (
                "route_estimate" if self.duration_seconds is not None else "unknown"
            ),
            "provider": self.source,
            "simulated": False,
        }


def point(latitude, longitude):
    try:
        values = {"latitude": float(latitude), "longitude": float(longitude)}
    except (ValueError, TypeError):
        return None
    if (
        not all(math.isfinite(value) for value in values.values())
        or abs(values["latitude"]) > 90
        or abs(values["longitude"]) > 180
    ):
        return None
    return values


def estimate(user, prop, assumptions, *, frozen=None):
    origin = point(prop.latitude, prop.longitude)
    destination = point(assumptions.get("latitude"), assumptions.get("longitude"))
    departure = assumptions.get("departure_at", "")
    query = {
        "origin": origin,
        "destination": destination,
        "mode": assumptions["mode"],
        "departure_at": departure,
        "timezone": "Africa/Cairo",
        "source": "google_routes",
        "version": "v2",
    }
    digest = fingerprint(query)

    def unknown(reason):
        return RouteEstimate(
            origin or {},
            destination or {},
            assumptions["mode"],
            departure,
            "Africa/Cairo",
            digest,
            unknown_reason=reason,
        ).payload()

    if not origin or not destination:
        return unknown("coordinates_unavailable")
    at = parse_datetime(departure) if isinstance(departure, str) else None
    if not at or timezone.is_naive(at) or at <= timezone.now():
        return unknown("departure_time_required")
    try:
        policy = approved_policy("D22", "routes.estimate")
    except RentalConflict:
        return unknown("route_provider_policy_required")
    ttl = policy.rules.get("route_validity_seconds")
    if (
        type(ttl) is not int
        or ttl <= 0
        or not policy.rules.get("storage_policy_reference")
    ):
        return unknown("route_retention_policy_required")
    if frozen is not None:
        expiry = parse_datetime(frozen.get("expires_at") or "")
        if (
            frozen.get("query_digest") != digest
            or not expiry
            or expiry <= timezone.now()
            or frozen.get("policy_version") != policy.version
        ):
            raise RentalConflict(
                "Route estimates changed or expired. Create and review a fresh scenario.",
                code="route_refresh_required",
            )
        return frozen
    if not settings.PLANNING_ROUTES_API_KEY:
        return unknown("route_provider_unconfigured")
    cache_key = "corporate-route:" + fingerprint(
        {"query": query, "policy": policy.version}
    )
    cached = cache.get(cache_key)
    if cached and parse_datetime(cached["expires_at"]) > timezone.now():
        return cached
    provider_budget(user, "corporate_routes")
    try:
        row = route_matrix(
            [origin],
            {
                "mode": assumptions["mode"],
                "time_kind": "depart_at",
                "at": departure,
                "location": destination,
            },
        )[0]
    except DiscoveryUnavailable:
        return unknown("route_provider_unavailable")
    if (
        row.get("status") != "ok"
        or row.get("timing_fallback")
        or type(row.get("distance_meters")) is not int
    ):
        return unknown("route_or_timing_not_confirmed")
    now = timezone.now()
    result = RouteEstimate(
        origin,
        destination,
        assumptions["mode"],
        departure,
        "Africa/Cairo",
        digest,
        duration_seconds=row["duration_seconds"],
        distance_meters=row["distance_meters"],
        fetched_at=now.isoformat(),
        expires_at=(now + timedelta(seconds=ttl)).isoformat(),
    ).payload()
    result["policy_version"] = policy.version
    cache.set(cache_key, result, timeout=ttl)
    return result
