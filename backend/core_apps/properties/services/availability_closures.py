"""Dated closures override the weekly pattern without changing appointments."""

from datetime import datetime, timezone as utc
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from ..models import AvailabilityClosure, PropertyVisit


def parse_range(data):
    try:
        zone = ZoneInfo(data.get("timezone", "Africa/Cairo"))
        values = [datetime.fromisoformat(data[key]) for key in ("starts_at", "ends_at")]
        for value in values:
            if value.tzinfo is None:
                raise ValueError()
            # A supplied local offset must agree with the named zone, including DST.
            local = value.astimezone(zone)
            if (
                local.replace(tzinfo=None) != value.replace(tzinfo=None)
                or local.utcoffset() != value.utcoffset()
            ):
                raise ValueError()
        start, end = values
        if start >= end or (end - start).days > 180 or end <= timezone.now():
            raise ValueError()
        return start, end, zone
    except (KeyError, ValueError, TypeError, ZoneInfoNotFoundError):
        raise ValidationError(
            "Supply a valid dated range and timezone, including its current UTC offset."
        )


def closure_intervals(prop, start=None, end=None):
    """Load a window once for slot projection; mutation callers load after locking."""
    rows = AvailabilityClosure.objects.filter(property=prop, active=True)
    if start is not None:
        rows = rows.filter(ends_at__gt=start)
    if end is not None:
        rows = rows.filter(starts_at__lt=end)
    return list(rows.order_by("starts_at").values_list("starts_at", "ends_at"))


def slot_in_closure(prop, day, time, *, intervals=None):
    zone = ZoneInfo("Africa/Cairo")
    local = datetime.combine(day, time).replace(tzinfo=zone)
    # Reject nonexistent or ambiguous wall times instead of guessing an instant.
    roundtrip = local.astimezone(utc.utc).astimezone(zone)
    if (
        roundtrip.replace(tzinfo=None) != local.replace(tzinfo=None)
        or local.utcoffset() != local.replace(fold=1).utcoffset()
    ):
        return True
    if intervals is None:
        return AvailabilityClosure.objects.filter(
            property=prop, active=True, starts_at__lte=local, ends_at__gt=local
        ).exists()
    at = local.astimezone(utc.utc)
    return any(start <= at < end for start, end in intervals)


def affected_visits(prop, start, end):
    result = []
    for visit in PropertyVisit.objects.filter(
        property=prop,
        status__in=["pending", "confirmed"],
        visit_date__isnull=False,
        visit_time__isnull=False,
    ):
        local = datetime.combine(visit.visit_date, visit.visit_time).replace(
            tzinfo=ZoneInfo("Africa/Cairo")
        )
        if start <= local < end:
            result.append(
                {
                    "id": str(visit.id),
                    "revision": visit.revision,
                    "date": visit.visit_date.isoformat(),
                    "time": visit.visit_time.strftime("%H:%M"),
                }
            )
    return sorted(result, key=lambda v: v["id"])
