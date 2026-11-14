from functools import partial
from ..services.rental_lifecycle import applications_commands as commands

from core_apps.features.http import ActionPolicy, FeatureAPIView
from rest_framework.permissions import IsAuthenticated
from core_apps.features.renderers import FeatureJsonRenderer

from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from ..models import (
    ApplicationProfile,
    ApplicationProfileVersion,
    ApplicationAccessGrant,
)
from ..rental_lifecycle_serializers import (
    CommandBody,
    ProfileBody,
    ShareBody,
    ShareReviewBody,
)
from ..services.rental_lifecycle import applications as service
from ..services.rental_lifecycle.access import property_for
from .common import validated, mutate, page


class ApplicationProfileView(FeatureAPIView):
    name = "Application Profile"
    http_method_names = ["get", "patch", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "applications",
            "application_profile",
            boundary="standard",
            capability=None,
            typed=False,
        ),
        "patch": ActionPolicy(
            "applications",
            "application_profile",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        return Response(
            service.profile_payload(
                ApplicationProfile.objects.filter(applicant=request.user).first(),
                request.user,
            )
        )

    def patch(self, request):
        data = validated(ProfileBody, request.data)
        execute = partial(
            commands.application_profile_patch_execute, actor=request.user, data=data
        )
        return mutate(
            request, "application_profile.save", lambda: request.user, execute
        )


# Stable callable import for integrations; URLs use the explicit class.
application_profile = ApplicationProfileView.as_view()


class ApplicationVersionView(FeatureAPIView):
    name = "Application Version"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "applications",
            "application_version",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request):
        data = validated(CommandBody, request.data)

        authorize = partial(
            commands.application_version_post_authorize, actor=request.user
        )

        execute = partial(
            commands.application_version_post_execute, actor=request.user, data=data
        )

        return mutate(request, "application_profile.freeze", authorize, execute)


# Stable callable import for integrations; URLs use the explicit class.
application_version = ApplicationVersionView.as_view()


class ApplicationShareReviewView(FeatureAPIView):
    name = "Application Share Review"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "applications",
            "application_share_review",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request):
        data = validated(ShareReviewBody, request.data)
        version = get_object_or_404(
            ApplicationProfileVersion,
            id=data["version_id"],
            profile__applicant=request.user,
        )
        prop = property_for(request.user, data["property_id"])
        return Response(
            service.share_review(version, prop, data["categories"], data["expires_at"])
        )


# Stable callable import for integrations; URLs use the explicit class.
application_share_review = ApplicationShareReviewView.as_view()


class ApplicationSharesView(FeatureAPIView):
    name = "Application Shares"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "applications",
            "application_shares",
            boundary="standard",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "applications",
            "application_shares",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        qs = ApplicationAccessGrant.objects.filter(applicant=request.user).order_by(
            "-created_at"
        )
        return page(request, qs, lambda item: service.share_payload(item, request.user))

    def post(self, request):
        data = validated(ShareBody, request.data)
        authorize = partial(
            commands.application_shares_post_authorize, actor=request.user, data=data
        )
        execute = partial(
            commands.application_shares_post_execute, actor=request.user, data=data
        )
        return mutate(request, "application_share.create", authorize, execute)


# Stable callable import for integrations; URLs use the explicit class.
application_shares = ApplicationSharesView.as_view()


class ApplicationShareView(FeatureAPIView):
    name = "Application Share"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "applications",
            "application_share",
            boundary="standard",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "applications",
            "application_share",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, share_id):
        item = get_object_or_404(ApplicationAccessGrant, id=share_id)
        payload = service.share_payload(item, request.user)
        return Response(payload)

    def post(self, request, share_id):
        item = get_object_or_404(ApplicationAccessGrant, id=share_id)
        service.share_payload(item, request.user)
        data = validated(CommandBody, request.data)
        authorize = partial(
            commands.application_share_post_authorize,
            actor=request.user,
            share_id=share_id,
        )
        execute = partial(
            commands.application_share_post_execute, actor=request.user, data=data
        )
        return mutate(
            request, f"application_share.revoke.{share_id}", authorize, execute
        )


# Stable callable import for integrations; URLs use the explicit class.
application_share = ApplicationShareView.as_view()


class ApplicationVersionDetailView(FeatureAPIView):
    name = "Application Version Detail"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "applications",
            "application_version_detail",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, version_id):
        item = get_object_or_404(
            ApplicationProfileVersion, id=version_id, profile__applicant=request.user
        )
        return Response(service.version_payload(item))


# Stable callable import for integrations; URLs use the explicit class.
application_version_detail = ApplicationVersionDetailView.as_view()
