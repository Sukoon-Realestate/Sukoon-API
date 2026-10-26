import hashlib
import secrets
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from .errors import TourError, require
from .models import TourViewerSession
from .policy import enabled, public_property, scope_policy, uuid_value


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def available_variant(variant, preview=False, user=None):
    revision = variant.revision
    tour, prop = revision.tour, revision.tour.target
    if revision.capture_job_id:
        from .capture_delivery import source

        source(revision)
    require(
        enabled(tour.kind, preview) and not tour.deleted,
        "tour_disabled",
        "This tour is unavailable.",
        409,
    )
    require(
        revision.processing_state == "ready"
        and revision.source_hash == variant.source_hash,
        "not_ready",
        "This tour is not ready.",
        409,
    )
    if preview:
        from django.contrib.auth import get_user_model
        from rest_framework.exceptions import PermissionDenied
        from .review_access import reviewer

        user = (
            get_user_model().objects.filter(pk=user.pk, is_active=True).first()
            if user and user.is_authenticated
            else None
        )
        authorized = bool(
            user
            and getattr(prop, "owner_id", getattr(prop, "manager_id", None)) == user.pk
        )
        if user and not authorized:
            try:
                reviewer(user)
                authorized = True
            except (PermissionDenied, TourError):
                pass
        require(
            authorized,
            "preview_forbidden",
            "Preview access is restricted.",
            403,
        )
    else:
        require(
            public_property(prop)
            and not tour.disabled
            and tour.active_revision_id == revision.pk
            and revision.review_state == "approved",
            "tour_unavailable",
            "This tour is no longer published.",
            409,
        )
    require(
        variant.scope_fingerprint
        == scope_policy(prop, variant.context, variant.manifest["spaces"]),
        "scope_changed",
        "The viewing scope changed. Refresh the property.",
        409,
    )
    require(
        variant.manifest.get("schema_version") in (1, 2),
        "unsupported_manifest",
        "Update the viewer to open this tour.",
        409,
    )


def available(prop, context="overview"):
    result = []
    if not public_property(prop):
        return result
    for tour in prop.virtual_tours.filter(deleted=False, disabled=False).select_related(
        "active_revision"
    ):
        if (
            not enabled(tour.kind)
            or not tour.active_revision
            or tour.active_revision.processing_state != "ready"
            or tour.active_revision.review_state != "approved"
        ):
            continue
        variant = (
            tour.active_revision.variants.filter(context=context)
            .select_related("revision__tour__property")
            .first()
        )
        if variant:
            try:
                available_variant(variant)
            except TourError:
                continue
            result.append(
                {
                    "tour_id": str(tour.id),
                    "revision_id": str(tour.active_revision.id),
                    "kind": tour.kind,
                    "title": variant.manifest["title"],
                    "captured_at": variant.manifest["captured_at"],
                    "content_origin": variant.manifest["content_origin"],
                    "has_available_variant": True,
                    "requires_offer_context": False,
                }
            )
        elif (
            context == "overview"
            and (prop.rental_inventory or {}).get("mode") == "partial"
        ):
            # Hint only: no package, source URL, offer-specific metadata or access.
            result.append(
                {
                    "tour_id": str(tour.id),
                    "revision_id": str(tour.active_revision.id),
                    "kind": tour.kind,
                    "has_available_variant": False,
                    "requires_offer_context": True,
                }
            )
    return result


def create_session(tour, user, body):
    require(
        set(body).issubset(
            {
                "offer_id",
                "preview",
                "revision_id",
                "context",
                "supported_manifest_versions",
            }
        ),
        "invalid_session",
        "Unsupported viewer session field.",
    )
    preview = body.get("preview") is True
    require(
        "preview" not in body or isinstance(body["preview"], bool),
        "invalid_session",
        "Preview must be a boolean.",
    )
    context = (
        body.get("context", body.get("offer_id") or "overview")
        if preview
        else body.get("offer_id") or "overview"
    )
    require(
        isinstance(context, str) and 1 <= len(context) <= 100,
        "invalid_session",
        "Provide a valid viewing context.",
    )
    if preview:
        require(
            uuid_value(body.get("revision_id")),
            "invalid_revision",
            "Preview requires a valid revision UUID.",
        )
    revision = (
        tour.revisions.filter(id=body.get("revision_id")).first()
        if preview
        else tour.active_revision
    )
    require(revision, "tour_unavailable", "No viewable revision exists.", 404)
    variant = (
        revision.variants.filter(context=context)
        .select_related("revision__tour__property")
        .first()
    )
    require(
        variant,
        "variant_unavailable",
        "Select an offer with an approved viewing package.",
        404,
    )
    available_variant(variant, preview, user)
    versions = body.get("supported_manifest_versions", [1])
    require(
        isinstance(versions, list)
        and 1 <= len(versions) <= 4
        and all(type(v) is int and v in (1, 2) for v in versions)
        and variant.manifest["schema_version"] in versions,
        "unsupported_manifest",
        "Update the app to open this capture tour.",
        409,
    )
    token = secrets.token_urlsafe(32)
    now = timezone.now()
    session = TourViewerSession.objects.create(
        variant=variant,
        user=user if user.is_authenticated else None,
        preview=preview,
        bootstrap_hash=token_hash(token),
        bootstrap_expires_at=now + timedelta(seconds=60),
        expires_at=now + timedelta(minutes=15),
    )
    return {
        "session_id": str(session.id),
        "bootstrap_token": token,
        "bootstrap_expires_at": session.bootstrap_expires_at.isoformat(),
        "viewer_url": settings.VIRTUAL_TOUR_VIEWER_URL,
        "protocol_version": 1,
        "manifest_version": variant.manifest["schema_version"],
    }


def active_session(session):
    require(
        not session.revoked_at and session.expires_at > timezone.now(),
        "session_expired",
        "Open the tour again to continue.",
        401,
    )
    # Refresh all related objects on every access (including signed byte grants).
    available_variant(session.variant, session.preview, session.user)


def authenticate_session(session, credential):
    require(
        bool(credential)
        and bool(session.credential_hash)
        and secrets.compare_digest(token_hash(credential), session.credential_hash),
        "viewer_unauthorized",
        "Invalid viewer credential.",
        401,
    )
    active_session(session)


def exchange(session):
    now = timezone.now()
    require(
        session.exchanged_at is None and session.bootstrap_expires_at > now,
        "bootstrap_expired",
        "The bootstrap token has expired or was used.",
        401,
    )
    active_session(session)
    credential = secrets.token_urlsafe(32)
    session.exchanged_at, session.credential_hash = now, token_hash(credential)
    session.expires_at = now + timedelta(minutes=15)
    session.save(update_fields=["exchanged_at", "credential_hash", "expires_at"])
    return {
        "session_id": str(session.id),
        "credential": credential,
        "expires_at": session.expires_at.isoformat(),
    }
