from datetime import timedelta
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound
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
from ..services.rental_lifecycle.common import audit, require_revision
from .common import endpoint, validated, mutate, page


@endpoint(["GET", "PATCH"])
def application_profile(request):
    if request.method == "GET":
        return Response(
            service.profile_payload(
                ApplicationProfile.objects.filter(applicant=request.user).first(),
                request.user,
            )
        )
    data = validated(ProfileBody, request.data)

    def execute(subject):
        item = service.save_profile(request.user, data)
        return item, service.profile_payload(item, request.user), 200

    return mutate(request, "application_profile.save", lambda: request.user, execute)


@endpoint(["POST"])
def application_version(request):
    data = validated(CommandBody, request.data)

    def authorize():
        return get_object_or_404(
            ApplicationProfile.objects.select_for_update(), applicant=request.user
        )

    def execute(profile):
        item = service.freeze_profile(profile, request.user, data)
        return item, service.version_payload(item), 201

    return mutate(request, "application_profile.freeze", authorize, execute)


@endpoint(["POST"])
def application_share_review(request):
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


@endpoint(["GET", "POST"])
def application_shares(request):
    if request.method == "GET":
        qs = ApplicationAccessGrant.objects.filter(applicant=request.user).order_by(
            "-created_at"
        )
        return page(request, qs, lambda item: service.share_payload(item, request.user))
    data = validated(ShareBody, request.data)

    def authorize():
        return get_object_or_404(
            ApplicationProfileVersion,
            id=data["version_id"],
            profile__applicant=request.user,
        )

    def execute(version):
        require_revision(version, data["expected_revision"])
        prop = property_for(request.user, data["property_id"], lock=True)
        item = service.create_share(version, request.user, prop, data)
        return item, service.share_payload(item, request.user), 201

    return mutate(request, "application_share.create", authorize, execute)


@endpoint(["GET", "POST"])
def application_share(request, share_id):
    item = get_object_or_404(ApplicationAccessGrant, id=share_id)
    payload = service.share_payload(item, request.user)
    if request.method == "GET":
        return Response(payload)
    data = validated(CommandBody, request.data)

    def authorize():
        return get_object_or_404(
            ApplicationAccessGrant.objects.select_for_update(),
            id=share_id,
            applicant=request.user,
        )

    def execute(grant):
        require_revision(grant, data["expected_revision"])
        grant.revoked_at = timezone.now()
        grant.revision += 1
        grant.save()
        audit(grant, request.user, "application.share_revoked")
        return grant, service.share_payload(grant, request.user), 200

    return mutate(request, f"application_share.revoke.{share_id}", authorize, execute)


@endpoint(["GET"])
def application_version_detail(request, version_id):
    item = get_object_or_404(
        ApplicationProfileVersion, id=version_id, profile__applicant=request.user
    )
    return Response(service.version_payload(item))
