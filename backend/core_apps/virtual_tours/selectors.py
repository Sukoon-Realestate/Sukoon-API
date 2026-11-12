"""Scoped tour and capture reads. Locking variants are used only inside commands."""

from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import (
    PropertyVirtualTour,
    TourRevision,
    TourUploadSession,
    TourViewerSession,
)
from .capture_models import PropertyCaptureSession, CaptureAsset
from .policy import owner_property
from . import sessions


def owned_tour(user, property_id, tour_id, lock=False, asset_kind="property"):
    prop = owner_property(user, property_id, asset_kind)
    qs = PropertyVirtualTour.objects.select_related("property", "active_revision")
    if lock:
        type(prop).objects.select_for_update().get(pk=prop.pk)
        owner_property(user, property_id, asset_kind)
        qs = qs.select_for_update(of=("self",))
    return get_object_or_404(qs, id=tour_id, **{asset_kind: prop})


def owned_revision(user, property_id, tour_id, revision_id, asset_kind="property"):
    tour = owned_tour(user, property_id, tour_id, True, asset_kind=asset_kind)
    return get_object_or_404(
        TourRevision.objects.select_for_update(of=("self",)).select_related(
            "tour__property"
        ),
        id=revision_id,
        tour=tour,
    )


def owned_upload(user, upload_id, lock=False):
    qs = TourUploadSession.objects.select_related("revision__tour__property", "asset")
    if lock:
        qs = qs.select_for_update(of=("self",))
    return get_object_or_404(
        qs.filter(
            Q(revision__tour__property__owner=user)
            | Q(revision__tour__building__manager=user)
            | Q(revision__tour__complex__manager=user)
        ),
        id=upload_id,
    )


def session_query(lock=False):
    qs = TourViewerSession.objects.select_related(
        "variant__revision__tour__property", "user"
    )
    return qs.select_for_update(of=("self",)) if lock else qs


def viewer_session(session_id, credential, lock=False):
    session = get_object_or_404(session_query(lock), id=session_id)
    sessions.authenticate_session(session, credential)
    return session


def owned(user, session_id, lock=False):
    if lock:
        from core_apps.properties.models import Property

        identity = get_object_or_404(PropertyCaptureSession, id=session_id, owner=user)
        get_object_or_404(
            Property.objects.select_for_update(),
            pk=identity.property_id,
            owner=user,
            retired_at=None,
        )
    qs = PropertyCaptureSession.objects.select_related("property")
    if lock:
        qs = qs.select_for_update(of=("self",))
    return get_object_or_404(
        qs,
        id=session_id,
        owner=user,
        property__owner=user,
        property__retired_at=None,
        deleted_at=None,
    )


def asset_for(user, session_id, asset_id, lock=False):
    session = owned(user, session_id, lock)
    qs = CaptureAsset.objects.select_for_update() if lock else CaptureAsset.objects
    return get_object_or_404(qs, session=session, id=asset_id)


def owner_tours(user, property_id, asset_kind="property"):
    from django.db.models import F, Prefetch
    from .models import TourReviewEvent
    from .services import tour_payload

    prop = owner_property(user, property_id, asset_kind)
    revisions = (
        TourRevision.objects.select_related("capture_job")
        .order_by("-created_at")
        .prefetch_related(
            "assets",
            "variants",
            Prefetch(
                "reviews",
                queryset=TourReviewEvent.objects.filter(
                    decision="rejected", source_hash=F("revision__source_hash")
                ).order_by("-created_at", "-pk")[:1],
                to_attr="prepared_reviews",
            ),
        )[:1]
    )
    tours = prop.virtual_tours.select_related(
        "property", "building", "complex", "active_revision"
    ).prefetch_related(
        Prefetch("revisions", queryset=revisions, to_attr="prepared_revisions")
    )
    return {"tours": [tour_payload(tour) for tour in tours]}
