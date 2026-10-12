from datetime import timedelta
from django.conf import settings

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response

from .planning_models import HousingOffer, HousingRequest
from .services.planning import (
    check_revision,
    criteria,
    criteria_payload,
    eligible_owner,
    money,
    mutate,
    offer_money,
    page,
    planning_api,
    public_properties,
    selection,
    text_field,
)
from .services.rental_phase2 import RentalConflict


def request_status(item):
    return (
        "expired"
        if item.status in {"published", "paused"} and item.expires_at <= timezone.now()
        else item.status
    )


def can_read_request(user, item):
    if item.user_id == user.pk or item.offers.filter(owner=user).exists():
        return True
    return (
        request_status(item) == "published"
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
    if item.user_id == user.pk:
        return {
            "published": ["edit", "pause", "close", "fulfill"],
            "paused": ["edit", "publish", "close"],
            "draft": ["edit", "publish", "close"],
        }.get(state, [])
    return ["offer"] if state == "published" and can_read_request(user, item) else []


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
        return page(
            request,
            HousingRequest.objects.filter(user=request.user).order_by(
                "-created_at", "pkid"
            ),
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
    cities = {
        str(x)
        for x in public_properties()
        .filter(owner=request.user, is_ownership_verified=True)
        .values_list("city__id", flat=True)
    }
    items = [
        x
        for x in HousingRequest.objects.filter(
            status="published", expires_at__gt=timezone.now()
        )
        .exclude(user=request.user)
        .order_by("-created_at", "pkid")
        if x.criteria.get("city_id") in cities
    ]
    return page(request, items, lambda x: request_payload(x, request.user))


@planning_api(["GET"], "housing_requests")
def housing_request_detail(request, request_id):
    return Response(
        request_payload(get_request(request.user, request_id), request.user)
    )


@planning_api(["POST"], "housing_requests")
def housing_request_action(request, request_id, action):
    def apply(item, revision):
        if item.user_id != request.user.pk or action not in request_actions(
            request.user, item
        ):
            raise PermissionDenied("This request action is not available to you.")
        if request.data.get("action") != action:
            raise ValidationError({"action": "Body and route action must match."})
        if action == "edit":
            for key, value in _request_values(request.data).items():
                setattr(item, key, value)
        else:
            item.status = {
                "pause": "paused",
                "publish": "published",
                "close": "closed",
                "fulfill": "fulfilled",
            }[action]
        item.revision += 1
        item.save()
        return item

    return mutate(
        request,
        f"housing_request.{action}.{request_id}",
        lambda: get_request(request.user, request_id, lock=True),
        apply,
        lambda x: request_payload(x, request.user),
    )


def offer_status(item):
    if item.status not in {"declined", "withdrawn"} and (
        request_status(item.request) != "published"
        or item.request_revision != item.request.revision
    ):
        return "expired"
    if item.status in {"sent", "viewed", "shortlisted", "selected_to_proceed"}:
        from .services.tenancy_invitations import resolve_offer_snapshot

        try:
            if not public_properties().filter(pk=item.property_id).exists():
                return "unavailable"
            resolve_offer_snapshot(
                item.property,
                item.selection["offer_id"],
                item.selection["offer_revision"],
            )
        except (ValidationError, RentalConflict, KeyError):
            return "unavailable"
    return item.status


def offer_actions(user, item):
    if user.pk == item.owner_id:
        return (
            ["withdraw"]
            if item.status in {"sent", "viewed", "shortlisted", "selected_to_proceed"}
            else []
        )
    if user.pk == item.request.user_id and offer_status(item) in {
        "sent",
        "viewed",
        "shortlisted",
    }:
        return (["shortlist"] if item.status != "shortlisted" else []) + [
            "select_to_proceed",
            "decline",
        ]
    if user.pk == item.request.user_id and offer_status(item) == "selected_to_proceed":
        return ["decline"]
    return []


def offer_payload(item, user):
    return {
        "id": str(item.id),
        "request_id": str(item.request.id),
        "owner_user_id": str(item.owner.id),
        "status": offer_status(item),
        "note": item.note,
        "revision": item.revision,
        "request_revision": item.request_revision,
        "selection": item.selection,
        "rent": money(item.rent_minor),
        "deposit": money(item.deposit_minor),
        "price_period": item.price_period,
        "allowed_actions": offer_actions(user, item),
        "blocking_reasons": [],
    }


def get_offer(user, identifier, *, lock=False):
    queryset = HousingOffer.objects.select_related("request", "owner")
    if lock:
        queryset = queryset.select_for_update(of=("self",))
    item = get_object_or_404(
        queryset.filter(Q(owner=user) | Q(request__user=user)), id=identifier
    )
    return item


@planning_api(["GET", "POST"], "housing_offers")
def housing_offers(request, request_id):
    parent = get_request(request.user, request_id)
    if request.method == "GET":
        items = (
            parent.offers.all()
            if parent.user_id == request.user.pk
            else parent.offers.filter(owner=request.user)
        )
        return page(
            request,
            items.select_related("request", "owner").order_by("-created_at", "pkid"),
            lambda x: offer_payload(x, request.user),
        )

    def apply(item, revision):
        if item.user_id == request.user.pk or "offer" not in request_actions(
            request.user, item
        ):
            raise PermissionDenied(
                "Only an eligible owner can respond to a published request."
            )
        if str(request.data.get("request_id")) != str(item.id):
            raise ValidationError({"request_id": "Must match the route."})
        check_revision(item.revision, request.data.get("request_revision"))
        prop, snapshot = selection(request, request.data.get("selection"), owned=True)
        if (
            item.offers.filter(
                owner=request.user,
                property=prop,
                request_revision=item.revision,
                selection__offer_id=snapshot["offer_id"],
            )
            .exclude(status__in=["withdrawn", "declined"])
            .exists()
        ):
            raise RentalConflict(
                "An offer for this exact accommodation already exists.",
                code="duplicate_offer",
            )
        if (
            item.offers.filter(
                owner=request.user, created_at__gte=timezone.now() - timedelta(days=1)
            ).count()
            >= settings.PLANNING_OWNER_OFFERS_PER_REQUEST_PER_DAY
        ):
            raise RentalConflict(
                "The offer limit for this request was reached.", code="offer_limit"
            )
        if str(prop.city.id) != item.criteria["city_id"] or (
            item.criteria["rental_scope"]
            and item.criteria["rental_scope"] != snapshot["rental_scope"]
        ):
            raise ValidationError(
                {
                    "selection": "The offer must match the requested city and accommodation scope."
                }
            )
        capacity = 1 if snapshot["rental_scope"] == "bed" else snapshot.get("capacity")
        if capacity is None or item.criteria["people"] > capacity:
            raise ValidationError(
                {"selection": "The accommodation cannot hold the requested party."}
            )
        rent, deposit = offer_money(snapshot)
        requirements = item.criteria
        if rent < (requirements.get("budget_min") or {}).get(
            "amount_minor", 0
        ) or rent > (requirements.get("budget_max") or {}).get(
            "amount_minor", 10**12
        ):
            raise ValidationError(
                {"selection": "The rent is outside the requested budget."}
            )
        if (
            requirements.get("property_type")
            and prop.property_type.slug != requirements["property_type"]
        ):
            raise ValidationError(
                {"selection": "The property type does not match the request."}
            )
        if (
            requirements.get("furnished") is not None
            and prop.is_furnished != requirements["furnished"]
        ):
            raise ValidationError(
                {"selection": "The furnishing requirement is not met."}
            )
        if any(
            not getattr(prop, name if name == "near_metro" else f"has_{name}", False)
            for name in requirements.get("amenities", [])
        ):
            raise ValidationError(
                {"selection": "The requested amenities are not available."}
            )
        if snapshot["terms"].get("price_period") != item.criteria["price_period"]:
            raise ValidationError(
                {"selection": "The offer must use the requested price period."}
            )
        return HousingOffer.objects.create(
            request=item,
            owner=request.user,
            property=prop,
            request_revision=item.revision,
            selection=snapshot,
            note=text_field(request.data, "note"),
            rent_minor=rent,
            deposit_minor=deposit,
            price_period=snapshot["terms"]["price_period"],
        )

    return mutate(
        request,
        f"housing_offer.create.{request_id}",
        lambda: get_request(request.user, request_id, lock=True),
        apply,
        lambda x: offer_payload(x, request.user),
        creating=True,
    )


@planning_api(["POST"], "housing_offers")
def housing_offer_action(request, offer_id, action):
    def apply(item, revision):
        if action not in offer_actions(request.user, item):
            raise PermissionDenied("This offer action is not available to you.")
        if request.data.get("decision") != action:
            raise ValidationError({"decision": "Body and route decision must match."})
        if action in {"shortlist", "select_to_proceed"}:
            selection(request, item.selection)
        if (
            action == "select_to_proceed"
            and item.request.offers.filter(status="selected_to_proceed")
            .exclude(pk=item.pk)
            .exists()
        ):
            raise RentalConflict(
                "Review the previously selected offer before selecting another."
            )
        item.status = {
            "shortlist": "shortlisted",
            "decline": "declined",
            "withdraw": "withdrawn",
            "select_to_proceed": "selected_to_proceed",
        }[action]
        item.revision += 1
        item.save()
        return item

    def load():
        found = get_offer(request.user, offer_id)
        HousingRequest.objects.select_for_update().get(pk=found.request_id)
        return get_offer(request.user, offer_id, lock=True)

    return mutate(
        request,
        f"housing_offer.{action}.{offer_id}",
        load,
        apply,
        lambda x: offer_payload(x, request.user),
    )


@planning_api(["GET"], "housing_offers")
def owner_housing_offers(request):
    return page(
        request,
        HousingOffer.objects.filter(owner=request.user)
        .select_related("request", "owner", "property")
        .order_by("-created_at", "pkid"),
        lambda x: offer_payload(x, request.user),
    )
