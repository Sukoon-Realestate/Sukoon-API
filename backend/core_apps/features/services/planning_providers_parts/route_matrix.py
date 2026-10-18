"""Planning providers: route matrix."""

import json
import math
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from rest_framework.exceptions import APIException, Throttled


class DiscoveryUnavailable(APIException):
    status_code = 503
    default_code = "provider_unavailable"
    default_detail = "The discovery provider is temporarily unavailable."


def provider_budget(user, service):
    """Bound provider costs per authenticated actor; replay is checked first."""
    key = f"planning-budget:{service}:{user.pk}:{int(timezone.now().timestamp()) // 60}"
    if cache.add(key, 1, timeout=120):
        count = 1
    else:
        try:
            count = cache.incr(key)
        except ValueError:
            raise Throttled(wait=60) from None
    if count > max(1, settings.PLANNING_PROVIDER_REQUESTS_PER_MINUTE):
        raise Throttled(wait=60)


def post_json(url, body, headers):
    request = Request(
        url,
        data=json.dumps(body).encode(),
        method="POST",
        headers={"Content-Type": "application/json", **headers},
    )
    try:
        with urlopen(
            request, timeout=settings.PLANNING_PROVIDER_TIMEOUT_SECONDS
        ) as response:
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError("oversized response")
        return json.loads(raw)
    except HTTPError as exc:
        # Provider bodies and request URLs may contain sensitive input. Do not log them.
        code = "provider_quota" if exc.code == 429 else "provider_unavailable"
        raise DiscoveryUnavailable(code=code) from None
    except (URLError, TimeoutError, OSError, ValueError):
        raise DiscoveryUnavailable() from None


def mock_discovery():
    from ...providers import fake_provider_available

    return fake_provider_available() and settings.PLANNING_MOCK_DISCOVERY


def ready_services(enabled):
    from core_apps.common.recovery import scope_available
    from config.advanced_housing import (
        PROVIDER_SERVICES,
        mock_mode_available,
        manual_review_available,
    )

    result = [
        service
        for service in enabled
        if service not in PROVIDER_SERVICES
        or mock_mode_available()
        or (service == "asset_assisted_analysis" and manual_review_available())
    ]
    if not scope_available("company_authority"):
        result = [
            service
            for service in result
            if service not in {"company_housing", "residential_portfolios"}
        ]
    from ...providers import fake_provider_available

    if not fake_provider_available() and "student_verification" in result:
        result.remove("student_verification")
    if not mock_discovery():
        if not settings.PLANNING_ROUTES_API_KEY and "commute" in result:
            result.remove("commute")
        if (
            not (settings.PLANNING_GEMINI_API_KEY and settings.PLANNING_GEMINI_MODEL)
            and "tenant_assistant" in result
        ):
            result.remove("tenant_assistant")
    return result


def configuration():
    from config.advanced_housing import provider_configuration

    return {
        "schema_version": 2,
        "advanced_housing": provider_configuration(),
        "joint_leases": False,
        "student_housing": {
            "schema_version": 1,
            "billing_period": "monthly",
            "currency": "EGP",
            "conditional_group_booking": False,
            "family_payment_delegation": False,
            "ambassadors": False,
            "partner_services": False,
            "admission_refund_guarantee": False,
        },
        # Protocol support only; housing_groups and current membership grant access.
        "group_chat": True,
        "commute": {
            "modes": list(settings.PLANNING_ROUTE_MODES),
            "arrive_by_modes": (
                ["transit"] if "transit" in settings.PLANNING_ROUTE_MODES else []
            ),
            "max_destinations": 2,
            "provider": "mock_haversine" if mock_discovery() else "google_routes",
            "max_origins": settings.PLANNING_ROUTE_MAX_ORIGINS,
        },
        "assistant": {
            "provider": "catalog_rules" if mock_discovery() else "gemini",
            "retain_history": False,
        },
        "housing_request_ttl_days": settings.PLANNING_REQUEST_TTL_DAYS,
    }


def route_matrix(origins, destination):
    """One destination per call preserves independent timing/mode constraints."""
    mode = destination["mode"]
    modes = {
        "driving": "DRIVE",
        "walking": "WALK",
        "cycling": "BICYCLE",
        "transit": "TRANSIT",
    }
    if mode not in settings.PLANNING_ROUTE_MODES or (
        destination["time_kind"] == "arrive_by" and mode != "transit"
    ):
        raise DiscoveryUnavailable(code="unsupported_route_mode")
    body = {
        "origins": [
            {"waypoint": {"location": {"latLng": origin}}} for origin in origins
        ],
        "destinations": [
            {"waypoint": {"location": {"latLng": destination["location"]}}}
        ],
        "travelMode": modes[mode],
        (
            "arrivalTime"
            if destination["time_kind"] == "arrive_by"
            else "departureTime"
        ): destination["at"],
        "languageCode": destination.get("language", "ar"),
        "regionCode": "eg",
    }
    if mode == "driving":
        body["routingPreference"] = "TRAFFIC_AWARE"
    raw = post_json(
        "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix",
        body,
        {
            "X-Goog-Api-Key": settings.PLANNING_ROUTES_API_KEY,
            "X-Goog-FieldMask": "originIndex,destinationIndex,status,condition,duration,distanceMeters,fallbackInfo",
        },
    )
    if not isinstance(raw, list):
        raise DiscoveryUnavailable(code="invalid_provider_response")
    results = [{"duration_seconds": None, "status": "unknown"} for _ in origins]
    seen = set()
    for element in raw:
        if not isinstance(element, dict):
            raise DiscoveryUnavailable(code="invalid_provider_response")
        index = element.get("originIndex", 0)
        if (
            type(index) is not int
            or not 0 <= index < len(origins)
            or index in seen
            or element.get("destinationIndex", 0) != 0
        ):
            raise DiscoveryUnavailable(code="invalid_provider_response")
        seen.add(index)
        if not isinstance(element.get("status", {}), dict):
            raise DiscoveryUnavailable(code="invalid_provider_response")
        if (
            element.get("status", {}).get("code", 0) != 0
            or element.get("condition") != "ROUTE_EXISTS"
        ):
            results[index]["status"] = "no_route"
            continue
        try:
            duration = element["duration"]
            seconds = (
                float(duration[:-1])
                if isinstance(duration, str) and duration.endswith("s")
                else float("nan")
            )
            if not math.isfinite(seconds) or seconds < 0:
                raise ValueError
        except (KeyError, ValueError, TypeError):
            raise DiscoveryUnavailable(code="invalid_provider_response") from None
        results[index] = {
            "duration_seconds": math.ceil(seconds),
            "distance_meters": (
                element.get("distanceMeters")
                if type(element.get("distanceMeters")) is int
                and element["distanceMeters"] >= 0
                else None
            ),
            "status": "ok",
            "timing_fallback": bool(element.get("fallbackInfo")),
        }
    return results
