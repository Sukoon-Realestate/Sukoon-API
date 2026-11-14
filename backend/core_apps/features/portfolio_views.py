from functools import partial
from .services.company import portfolio_commands as entry_commands

"""Thin owner portfolio commands. Public bytes never include authority evidence."""

from core_apps.features.http import ActionPolicy, FeatureAPIView
from rest_framework.permissions import IsAuthenticated
from core_apps.features.renderers import FeatureJsonRenderer


from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from .company_views import mutate, page
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
from .services.rental_lifecycle.common import require_actor, staff_role
from core_apps.properties.models import ResidentialMedia, PortfolioChangeSet
from core_apps.virtual_tours import storage


class ChangeHistoryView(FeatureAPIView):
    name = "Change History"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "portfolio_views",
            "change_history",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, kind, asset_id):
        parent = portfolio.parent_for(request.user, kind, asset_id)
        return page(
            request,
            PortfolioChangeSet.objects.filter(
                owner=request.user, **{kind: parent}
            ).order_by("-created_at", "-id"),
            changes.change_payload,
        )


# Stable callable import for integrations; URLs use the explicit class.
change_history = ChangeHistoryView.as_view()


class PreviewView(FeatureAPIView):
    name = "Preview"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "portfolio_views",
            "preview",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, kind, asset_id, operation):
        body = validated(
            BulkPreviewBody if operation == "bulk-edit" else TopologyPreviewBody,
            request.data,
        )
        handler = (
            changes.preview_bulk
            if operation == "bulk-edit"
            else topology.preview_topology
        )
        return mutate(
            request,
            "portfolio." + operation + ".preview",
            lambda: portfolio.parent_for(request.user, kind, asset_id),
            lambda _: handler(request.user, kind, asset_id, body),
            changes.change_payload,
            creating=True,
        )


# Stable callable import for integrations; URLs use the explicit class.
preview = PreviewView.as_view()


class ChangeView(FeatureAPIView):
    name = "Change"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "portfolio_views",
            "change",
            boundary="company",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "portfolio_views",
            "change",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, change_id):
        return Response(
            changes.change_payload(changes.change_for(request.user, change_id))
        )

    def post(self, request, change_id):
        body = validated(CommandBody, request.data)
        apply = partial(
            entry_commands.change_post_apply,
            actor=request.user,
            body=body,
            change_id=change_id,
        )
        return mutate(
            request,
            "portfolio.change.apply",
            lambda: changes.change_for(request.user, change_id),
            apply,
            changes.change_payload,
        )


# Stable callable import for integrations; URLs use the explicit class.
change = ChangeView.as_view()


class MediaCollectionView(FeatureAPIView):
    name = "Media Collection"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "portfolio_views",
            "media_collection",
            boundary="company",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "portfolio_views",
            "media_collection",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, kind, asset_id):
        parent = portfolio.parent_for(request.user, kind, asset_id)
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

    def post(self, request, kind, asset_id):
        portfolio.parent_for(request.user, kind, asset_id)
        body = validated(MediaIntentBody, request.data)
        return mutate(
            request,
            "portfolio.media.intent",
            lambda: portfolio.parent_for(request.user, kind, asset_id),
            lambda _: media.create_intent(request.user, kind, asset_id, body),
            media.payload,
            creating=True,
        )


# Stable callable import for integrations; URLs use the explicit class.
media_collection = MediaCollectionView.as_view()


class MediaDetailView(FeatureAPIView):
    name = "Media Detail"
    http_method_names = ["get", "put", "delete", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "portfolio_views",
            "media_detail",
            boundary="company",
            capability=None,
            typed=False,
        ),
        "put": ActionPolicy(
            "portfolio_views",
            "media_detail",
            boundary="company",
            capability=None,
            typed=False,
        ),
        "delete": ActionPolicy(
            "portfolio_views",
            "media_detail",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, media_id):
        return Response(media.payload(media.media_for(request.user, media_id)))

    def put(self, request, media_id):
        require_actor(request.user)
        return Response(
            media.payload(
                media.upload(request.user, media_id, request.FILES.get("file"))
            )
        )

    def delete(self, request, media_id):
        require_actor(request.user)
        body = validated(CommandBody, request.data)
        return mutate(
            request,
            "portfolio.media.remove",
            lambda: media.media_for(request.user, media_id),
            lambda _: media.remove(request.user, media_id, body),
            media.payload,
        )


# Stable callable import for integrations; URLs use the explicit class.
media_detail = MediaDetailView.as_view()


class MediaBytesView(FeatureAPIView):
    name = "Media Bytes"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "portfolio_views",
            "media_bytes",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, media_id):
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


# Stable callable import for integrations; URLs use the explicit class.
media_bytes = MediaBytesView.as_view()


class MediaReviewView(FeatureAPIView):
    name = "Media Review"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "portfolio_views",
            "media_review",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, media_id):
        body = validated(MediaReviewBody, request.data)

        authorize = partial(
            entry_commands.media_review_post_authorize,
            actor=request.user,
            media_id=media_id,
        )

        return mutate(
            request,
            "portfolio.media.review",
            authorize,
            lambda _: media.review(request.user, media_id, body),
            media.payload,
        )


# Stable callable import for integrations; URLs use the explicit class.
media_review = MediaReviewView.as_view()
