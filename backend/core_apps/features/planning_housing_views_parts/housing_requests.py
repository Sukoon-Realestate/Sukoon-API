"""Planning housing views: housing requests."""

from datetime import timedelta
from uuid import UUID
from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from ..planning_models import HousingRequest
from ..services.planning import (
    criteria,
    criteria_payload,
    eligible_owner,
    mutate,
    page,
    planning_api,
    public_properties,
    text_field,
)
from ..services.rental_phase2 import RentalConflict


def request_status(item):
    return (
        "expired"
        if item.status in {"published", "paused"} and item.expires_at <= timezone.now()
        else item.status
    )


def can_read_request(user, item):
    from ..services.student_housing.publication import participant_can_read

    if participant_can_read(user, item):
        return True
    if (item.user_id == user.pk and not item.academic_plan_id) or item.offers.filter(
        owner=user
    ).exists():
        return True
    return (
        request_status(item) == "published"
        and item.visibility == "eligible_owners"
        and eligible_owner(user)
    )


def can_offer_request(user, item):
    from ..services.student_housing.publication import request_current

    if not request_current(item):
        return False
    return (
        item.user_id != user.pk
        and request_status(item) == "published"
        and item.visibility == "eligible_owners"
        and public_properties()
        .filter(
            owner=user,
            is_ownership_verified=True,
            city__id=item.criteria.get("city_id"),
        )
        .exists()
    )


def get_request(user, identifier, *, lock=False):
    queryset = (
        HousingRequest.objects.select_for_update()
        if lock
        else HousingRequest.objects.all()
    )
    item = get_object_or_404(queryset, id=identifier)
    if not can_read_request(user, item):
        raise NotFound()
    return item


def request_actions(user, item):
    state = request_status(item)
    if item.user_id == user.pk and can_read_request(user, item):
        if item.academic_plan_id:
            return ["close"] if state in {"published", "paused"} else []
        return {
            "published": ["edit", "pause", "close", "fulfill"],
            "paused": ["edit", "publish", "close"],
            "draft": ["edit", "publish", "close"],
        }.get(state, [])
    return ["offer"] if can_offer_request(user, item) else []


def request_payload(item, user):
    return {
        "id": str(item.id),
        "user_id": str(item.user.id),
        "title": item.title,
        "note": item.note,
        "status": request_status(item),
        "visibility": item.visibility,
        "revision": item.revision,
        "criteria": criteria_payload(item.criteria),
        "expires_at": item.expires_at.isoformat(),
        "allowed_actions": request_actions(user, item),
        "blocking_reasons": [],
        "academic_context": item.academic_snapshot,
    }


def _request_values(data):
    visibility = data.get("visibility", "eligible_owners")
    if visibility != "eligible_owners":
        raise ValidationError({"visibility": "Only eligible_owners is supported."})
    return {
        "title": text_field(data, "title", required=True, limit=160),
        "note": text_field(data, "note"),
        "criteria": criteria(data.get("criteria")),
        "visibility": visibility,
    }


@planning_api(["GET", "POST"], "housing_requests")
def housing_requests(request):
    if request.method == "GET":
        from ..services.student_housing.access import plans_for

        visible = HousingRequest.objects.filter(
            Q(user=request.user, academic_plan__isnull=True)
            | Q(
                academic_plan__in=plans_for(request.user),
                academic_plan__participants__user=request.user,
            )
        ).distinct()
        return page(
            request,
            visible.order_by("-created_at", "pkid"),
            lambda x: request_payload(x, request.user),
        )
    if request.data.get("action") != "publish":
        raise ValidationError({"action": "A new housing request must be published."})

    def create(_, revision):
        live = HousingRequest.objects.filter(
            user=request.user,
            status__in=["published", "paused"],
            expires_at__gt=timezone.now(),
        ).count()
        if live >= settings.PLANNING_MAX_LIVE_REQUESTS:
            raise RentalConflict(
                "Close an existing housing request before publishing another.",
                code="request_limit",
            )
        return HousingRequest.objects.create(
            user=request.user,
            expires_at=timezone.now()
            + timedelta(days=settings.PLANNING_REQUEST_TTL_DAYS),
            **_request_values(request.data),
        )

    return mutate(
        request,
        "housing_request.create",
        lambda: None,
        create,
        lambda x: request_payload(x, request.user),
        creating=True,
    )


@planning_api(["GET"], "housing_requests")
def housing_demand(request):
    if not eligible_owner(request.user):
        raise PermissionDenied(
            "A verified owned listing is required to read housing demand."
        )
    # Discovery is available across cities. Matching inventory remains a
    # separate requirement for sending an offer, enforced by request_actions
    # and the exact-selection validation in housing_offers.
    items = (
        HousingRequest.objects.filter(
            status="published",
            visibility="eligible_owners",
            expires_at__gt=timezone.now(),
        )
        .exclude(user=request.user)
        .select_related("user")
        .order_by("-created_at", "pkid")
    )
    city = request.query_params.get("city", "").strip()
    if request.query_params.get("student") == "true":
        items = items.filter(academic_plan__isnull=False)
    if request.query_params.get("matching_inventory") == "true":
        cities = [
            str(value)
            for value in public_properties()
            .filter(owner=request.user, is_ownership_verified=True)
            .values_list("city__id", flat=True)
        ]
        items = items.filter(criteria__city_id__in=cities)
    if city:
        try:
            city = str(UUID(city))
        except ValueError:
            raise ValidationError({"city": "Use a city catalog UUID."})
        items = items.filter(criteria__city_id=city)
    return page(request, items, lambda x: request_payload(x, request.user))


@planning_api(["GET"], "housing_requests")
def housing_request_detail(request, request_id):
    return Response(
        request_payload(get_request(request.user, request_id), request.user)
    )
