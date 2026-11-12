"""Owner-only weekly availability. Slots never confirm a viewing request."""

from datetime import datetime, timedelta
import re

from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core_apps.common.idempotency import IdempotencyConflict, fingerprint
from core_apps.common.renderers import GenericJsonRenderer
from core_apps.users.models import User
from core_apps.users.services.sessions import validate_session
from ..models import OwnerAvailabilitySlot, Property, PropertyVisit
from ..services.availability_closures import slot_in_closure, closure_intervals


def _input(data):
    try:
        week = datetime.strptime(data.get("week_start", ""), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise ValidationError("Select a valid week.")
    today = timezone.localdate()
    if (
        week.weekday() != 0
        or week < today - timedelta(days=today.weekday())
        or week > today + timedelta(days=180)
    ):
        raise ValidationError("Choose a Monday within the next 180 days.")
    pattern = data.get("slots")
    if not isinstance(pattern, list) or not 1 <= len(pattern) <= 56:
        raise ValidationError("Supply between 1 and 56 weekly slots.")
    normalized = set()
    for item in pattern:
        if (
            not isinstance(item, dict)
            or type(item.get("weekday")) is not int
            or not 1 <= item["weekday"] <= 7
            or not isinstance(item.get("time"), str)
            or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", item["time"])
        ):
            raise ValidationError("Each slot needs a weekday and a 24-hour time.")
        normalized.add((item["weekday"], item["time"]))
    return week, sorted(normalized)


def _preview(prop, week, pattern):
    existing = {
        (slot.date, slot.time.strftime("%H:%M")): slot.is_enabled
        for slot in OwnerAvailabilitySlot.objects.filter(
            property=prop, date__gte=week, date__lt=week + timedelta(days=7)
        )
    }
    visits = set(
        PropertyVisit.objects.filter(
            property__owner_id=prop.owner_id,
            status=PropertyVisit.Status.CONFIRMED,
            visit_date__gte=week,
            visit_date__lt=week + timedelta(days=7),
            visit_time__isnull=False,
        ).values_list("visit_date", "visit_time")
    )
    busy = {(day, time.strftime("%H:%M")) for day, time in visits}
    from ..services.viewing_times import instant

    intervals = closure_intervals(
        prop,
        instant(week, datetime.min.time()),
        instant(week + timedelta(days=7), datetime.min.time()),
    )
    now = timezone.localtime()
    slots = []
    for weekday, time in pattern:
        day = week + timedelta(days=weekday - 1)
        status = "new"
        if day < now.date() or day == now.date() and time <= now.strftime("%H:%M"):
            status = "past"
        elif (day, time) in busy:
            status = "busy"
        elif slot_in_closure(
            prop, day, datetime.strptime(time, "%H:%M").time(), intervals=intervals
        ):
            status = "closed"
        elif (day, time) in existing:
            status = "existing" if existing[day, time] else "disabled"
        slots.append({"date": day.isoformat(), "time": time, "status": status})
    return {
        "protocol": 1,
        "week_start": week.isoformat(),
        "slots": slots,
        "revision": fingerprint({"property": str(prop.id), "slots": slots}),
    }


@api_view(["POST", "PUT"])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
def owner_availability(request, property_id):
    # POST is a read-only preview; PUT is an explicit, additive, idempotent set.
    week, pattern = _input(request.data)
    with transaction.atomic():
        current = User.objects.select_for_update().get(pk=request.user.pk)
        if request.auth:
            validate_session(current, request.auth)
        prop = Property.objects.select_for_update().filter(id=property_id).first()
        if prop is None:
            raise NotFound()
        if not current.is_active or prop.owner_id != current.pk or prop.retired_at:
            raise PermissionDenied()
        preview = _preview(prop, week, pattern)
        if request.method == "PUT":
            if request.data.get("revision") != preview["revision"]:
                raise IdempotencyConflict(
                    "Availability changed. Preview the week again."
                )
            for item in preview["slots"]:
                if item["status"] == "new":
                    OwnerAvailabilitySlot.objects.get_or_create(
                        property=prop,
                        owner=current,
                        date=item["date"],
                        time=item["time"],
                        defaults={"is_enabled": True},
                    )
            preview = _preview(prop, week, pattern)
        return Response(preview)
