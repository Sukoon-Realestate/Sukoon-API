from datetime import timedelta
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.response import Response
from core_apps.common.idempotency import (
    execute_idempotent,
    request_key,
    IdempotencyConflict,
)
from core_apps.common.renderers import GenericJsonRenderer
from core_apps.users.models import User
from core_apps.users.services.sessions import validate_session
from ..models import Property, HiddenListingPreference
from ..services.public_access import public_properties
from ..services.hidden_listings import active_preferences, eligible_offer_ids


class HiddenListingCommand(serializers.Serializer):
    property_id = serializers.UUIDField()
    offer_id = serializers.CharField(max_length=64, allow_blank=True, default="")
    action = serializers.ChoiceField(choices=["hide", "restore"])
    persistent = serializers.BooleanField(default=False)
    expected_revision = serializers.IntegerField(min_value=0)
    property_revision = serializers.IntegerField(min_value=1, required=False)
    offer_revision = serializers.IntegerField(min_value=1, required=False)


def projection(item):
    return {
        "property_id": str(item.property.id),
        "offer_id": item.offer_id,
        "revision": item.revision,
        "hidden": item.hidden,
        "expires_at": item.expires_at.isoformat() if item.expires_at else None,
        "active": item.hidden
        and (item.expires_at is None or item.expires_at > timezone.now()),
    }


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
def hidden_listings(request):
    if request.headers.get("X-Sukoon-Company-Id") or request.query_params.get("workspace", "individual") not in {"individual", "owner"}:
        raise PermissionDenied("Use individual or owner search preferences.")
    if request.method == "GET":
        target = request.query_params.get("property_id")
        if target:
            query = serializers.UUIDField().run_validation(target)
            prop = get_object_or_404(public_properties(), id=query)
            allowed = eligible_offer_ids(prop)
            records = HiddenListingPreference.objects.filter(
                user=request.user, property=prop
            )
            body = {
                "property_id": str(prop.id),
                "property_revision": prop.review_revision,
                "title": prop.title,
                "preferences": [
                    projection(row) for row in records.select_related("property")
                ],
                "offers": [
                    {
                        "id": str(o["id"]),
                        "revision": o["revision"],
                        "name": o.get("name", ""),
                    }
                    for o in (prop.rental_inventory or {}).get("offers", [])
                    if str(o.get("id")) in allowed
                ],
            }
        else:
            rows = list(
                active_preferences(request.user)
                .select_related("property")
                .order_by("-updated_at", "pk")[:500]
            )
            visible = {
                p.pk: p
                for p in public_properties().filter(
                    pk__in=[r.property_id for r in rows]
                )
            }
            names = {}
            for pk, prop in visible.items():
                allowed = eligible_offer_ids(prop)
                names[pk] = {
                    str(o["id"]): o.get("name", "")
                    for o in (prop.rental_inventory or {}).get("offers", [])
                    if str(o.get("id")) in allowed
                }
            body = {
                "preferences": [
                    {
                        **projection(row),
                        "title": (
                            visible[row.property_id].title
                            if row.property_id in visible
                            else ""
                        ),
                        "offer_name": names.get(row.property_id, {}).get(
                            row.offer_id, ""
                        ),
                    }
                    for row in rows
                ]
            }
        return Response(body, headers={"Cache-Control": "private, no-store"})
    body = HiddenListingCommand(data=request.data)
    body.is_valid(raise_exception=True)
    data = body.validated_data
    key = request_key(request)
    if not key:
        raise ValidationError("A stable Idempotency-Key is required.")
    with transaction.atomic():
        actor = User.objects.select_for_update().get(pk=request.user.pk)
        if not actor.is_active or actor.closed_at:
            raise PermissionDenied()
        if request.auth:
            validate_session(actor, request.auth)

        def commit():
            prop = None
            if data["action"] == "hide":
                prop = get_object_or_404(
                    public_properties(Property.objects.select_for_update()),
                    id=data["property_id"],
                )
            item = (
                HiddenListingPreference.objects.select_for_update(of=("self",))
                .select_related("property")
                .filter(
                    user=actor,
                    property__id=data["property_id"],
                    offer_id=data["offer_id"],
                )
                .first()
            )
            if data["expected_revision"] != (item.revision if item else 0):
                raise IdempotencyConflict(
                    "Hidden preference changed. Refresh it first."
                )
            if data["action"] == "hide":
                if data.get("property_revision") != prop.review_revision:
                    raise IdempotencyConflict("Listing changed. Review it again.")
                if data["offer_id"]:
                    offer = next(
                        (
                            o
                            for o in (prop.rental_inventory or {}).get("offers", [])
                            if str(o.get("id")) == data["offer_id"]
                            and not o.get("archived")
                            and o.get("availability") == "available"
                        ),
                        None,
                    )
                    if (
                        not offer
                        or data["offer_id"] not in eligible_offer_ids(prop)
                        or data.get("offer_revision") != offer.get("revision")
                    ):
                        raise IdempotencyConflict("Offer changed. Review it again.")
                if (
                    item is None
                    or not item.hidden
                    or item.expires_at is not None
                    and item.expires_at <= timezone.now()
                ) and active_preferences(actor).count() >= 500:
                    raise ValidationError("Restore an older hidden preference first.")
                if item is None:
                    item = HiddenListingPreference(
                        user=actor, property=prop, offer_id=data["offer_id"], revision=0
                    )
                item.hidden = True
                item.expires_at = (
                    None if data["persistent"] else timezone.now() + timedelta(days=30)
                )
            elif item is None:
                return (
                    {
                        "property_id": str(data["property_id"]),
                        "offer_id": data["offer_id"],
                        "revision": 0,
                        "hidden": False,
                        "active": False,
                        "expires_at": None,
                    },
                    200,
                    None,
                )
            else:
                item.hidden = False
            item.revision += 1
            item.save()
            return projection(item), 200, item.id

        result, code, _ = execute_idempotent(
            user=actor,
            operation="property.hidden-listing",
            key=key,
            payload=data,
            action=commit,
        )
        return Response(
            result, status=code, headers={"Cache-Control": "private, no-store"}
        )
