"""Thin owner portfolio commands. Public bytes never include authority evidence."""

from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from .company_views import company_api, mutate, page
from .company_serializers import CommandBody
from .portfolio_serializers import (
    BulkPreviewBody,
    TopologyPreviewBody,
    MediaIntentBody,
    MediaReviewBody,
)
from .rental_lifecycle_views.common import validated
from .services.company import (
    portfolio,
    portfolio_changes as changes,
    portfolio_topology as topology,
    portfolio_media as media,
)
from .services.rental_lifecycle.common import require_actor, require_staff, staff_role
from core_apps.properties.models import ResidentialMedia, PortfolioChangeSet
from core_apps.virtual_tours import storage


@company_api(["GET"])
def change_history(request, kind, asset_id):
    parent = portfolio.parent_for(request.user, kind, asset_id)
    return page(
        request,
        PortfolioChangeSet.objects.filter(
            owner=request.user, **{kind: parent}
        ).order_by("-created_at", "-id"),
        changes.change_payload,
    )


@company_api(["POST"])
def preview(request, kind, asset_id, operation):
    body = validated(
        BulkPreviewBody if operation == "bulk-edit" else TopologyPreviewBody,
        request.data,
    )
    handler = (
        changes.preview_bulk if operation == "bulk-edit" else topology.preview_topology
    )
    return mutate(
        request,
        "portfolio." + operation + ".preview",
        lambda: portfolio.parent_for(request.user, kind, asset_id),
        lambda _: handler(request.user, kind, asset_id, body),
        changes.change_payload,
        creating=True,
    )


@company_api(["GET", "POST"])
def change(request, change_id):
    if request.method == "GET":
        return Response(
            changes.change_payload(changes.change_for(request.user, change_id))
        )
    body = validated(CommandBody, request.data)

    def apply(item):
        handler = (
            changes.apply_bulk
            if item.operation == "bulk_edit"
            else topology.apply_topology
        )
        return handler(request.user, change_id, body)

    return mutate(
        request,
        "portfolio.change.apply",
        lambda: changes.change_for(request.user, change_id),
        apply,
        changes.change_payload,
    )


@company_api(["GET", "POST"])
def media_collection(request, kind, asset_id):
    parent = portfolio.parent_for(request.user, kind, asset_id)
    if request.method == "GET":
        return Response(
            {
                "items": [
                    media.payload(item)
                    for item in parent.media.exclude(state="removed").order_by(
                        "created_at"
                    )
                ]
            }
        )
    body = validated(MediaIntentBody, request.data)
    return mutate(
        request,
        "portfolio.media.intent",
        lambda: portfolio.parent_for(request.user, kind, asset_id),
        lambda _: media.create_intent(request.user, kind, asset_id, body),
        media.payload,
        creating=True,
    )


@company_api(["GET", "PUT", "DELETE"])
def media_detail(request, media_id):
    if request.method == "GET":
        return Response(media.payload(media.media_for(request.user, media_id)))
    require_actor(request.user)
    if request.method == "PUT":
        return Response(
            media.payload(
                media.upload(request.user, media_id, request.FILES.get("file"))
            )
        )
    body = validated(CommandBody, request.data)
    return mutate(
        request,
        "portfolio.media.remove",
        lambda: media.media_for(request.user, media_id),
        lambda _: media.remove(request.user, media_id, body),
        media.payload,
    )


@company_api(["GET"])
def media_bytes(request, media_id):
    item = get_object_or_404(
        ResidentialMedia.objects.select_related("building", "complex"),
        id=media_id,
        state="ready",
    )
    parent = item.building or item.complex
    owner = item.owner_id == request.user.pk
    reviewer = staff_role(request.user, {"property_reviewer"})
    public = (
        item.purpose == "photo"
        and item.review_status == "approved"
        and parent.authority_status == "verified"
        and not parent.archived
    )
    if not (owner or reviewer or public):
        raise PermissionDenied("This media is private.")
    response = FileResponse(
        storage.read_path(item.blob).open("rb"), content_type="image/png"
    )
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response


@company_api(["POST"])
def media_review(request, media_id):
    body = validated(MediaReviewBody, request.data)

    def authorize():
        require_staff(request.user, {"property_reviewer"})
        return get_object_or_404(ResidentialMedia, id=media_id)

    return mutate(
        request,
        "portfolio.media.review",
        authorize,
        lambda _: media.review(request.user, media_id, body),
        media.payload,
    )
