"""Locked tour lifecycle commands, executed through the durable operation receipt."""

from . import selectors
from django.shortcuts import get_object_or_404
from . import services, uploads
from .errors import require
from .models import TourRevision
from .policy import owner_property


def apply_revision_action(
    user, property_id, tour_id, revision_id, action, asset_kind, body, etag
):
    value = selectors.owned_revision(
        user, property_id, tour_id, revision_id, asset_kind=asset_kind
    )
    if action == "uploads":
        return uploads.create_upload(value, body, etag)
    if action == "process":
        require(not body, "invalid_request", "Processing accepts an empty body.")
        return services.queue_processing(value, etag)
    return services.submit_review(value, body, etag)


def abort_upload(user, upload_id, body, etag):
    upload = selectors.owned_upload(user, upload_id, True)
    require(not body, "invalid_request", "Abort accepts an empty body.")
    require(
        upload.state != "complete",
        "upload_completed",
        "A completed asset cannot be aborted.",
        409,
    )
    upload.state = "aborted"
    upload.save(update_fields=["state"])
    return (uploads.upload_payload(upload), 200)


def review_revision(user, property_id, tour_id, revision_id, asset_kind, body, etag):
    value = get_object_or_404(
        TourRevision.objects.select_for_update(of=("self",)).select_related(
            "tour__property"
        ),
        id=revision_id,
        tour__id=tour_id,
        **{"tour__" + asset_kind + "__id": property_id}
    )
    return services.review(value, user, body)


def create(user, property_id, asset_kind, body):
    prop = owner_property(user, property_id, asset_kind)
    # The account is locked by the operation boundary. Lock and recheck the target
    # before cloning/creation so retirement cannot race authoring.
    prop = type(prop).objects.select_for_update().get(pk=prop.pk)
    owner_property(user, property_id, asset_kind)
    return services.create_tour(prop, body)


def disable(user, property_id, tour_id, asset_kind, *, delete=False):
    tour = selectors.owned_tour(user, property_id, tour_id, True, asset_kind=asset_kind)
    tour.disabled = True
    if delete:
        tour.deleted = True
    tour.save(update_fields=["disabled", "deleted", "updated_at"])
    return services.tour_payload(tour), 200
