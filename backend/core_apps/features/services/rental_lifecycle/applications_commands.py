"""Named applications commands; adapters supply typed data and current actor."""

from django.shortcuts import get_object_or_404
from django.utils import timezone
from core_apps.features.models import (
    ApplicationProfile,
    ApplicationProfileVersion,
    ApplicationAccessGrant,
)
from core_apps.features.services.rental_lifecycle import applications as service
from core_apps.features.services.rental_lifecycle.access import property_for
from core_apps.features.services.rental_lifecycle.common import audit, require_revision


def application_profile_patch_execute(subject, *, actor, data):
    item = service.save_profile(actor, data)
    return (item, service.profile_payload(item, actor), 200)


def application_version_post_authorize(*, actor):
    return get_object_or_404(
        ApplicationProfile.objects.select_for_update(), applicant=actor
    )


def application_version_post_execute(profile, *, actor, data):
    item = service.freeze_profile(profile, actor, data)
    return (item, service.version_payload(item), 201)


def application_shares_post_authorize(*, actor, data):
    return get_object_or_404(
        ApplicationProfileVersion, id=data["version_id"], profile__applicant=actor
    )


def application_shares_post_execute(version, *, actor, data):
    require_revision(version, data["expected_revision"])
    prop = property_for(actor, data["property_id"], lock=True)
    item = service.create_share(version, actor, prop, data)
    return (item, service.share_payload(item, actor), 201)


def application_share_post_authorize(*, actor, share_id):
    return get_object_or_404(
        ApplicationAccessGrant.objects.select_for_update(), id=share_id, applicant=actor
    )


def application_share_post_execute(grant, *, actor, data):
    require_revision(grant, data["expected_revision"])
    grant.revoked_at = timezone.now()
    grant.revision += 1
    grant.save()
    audit(grant, actor, "application.share_revoked")
    return (grant, service.share_payload(grant, actor), 200)
