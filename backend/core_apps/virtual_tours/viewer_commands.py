"""Credential lifecycle and bounded streaming writes, independent of HTTP."""

from datetime import timedelta
from django.core import signing
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from . import selectors, sessions, uploads
from .models import TourUploadSession
from .errors import require


def receive_tour_part(upload_id, part, stream_factory, grant):
    try:
        grant = signing.loads(grant, salt="tour-upload-part", max_age=300)
    except signing.BadSignature:
        require(False, "upload_grant_expired", "Obtain a fresh part upload grant.", 401)
    require(
        grant == {"upload": str(upload_id), "part": part},
        "upload_grant_invalid",
        "Invalid upload grant.",
        403,
    )
    with transaction.atomic():
        upload = get_object_or_404(
            TourUploadSession.objects.select_for_update(of=("self",)).select_related(
                "revision__tour__property"
            ),
            id=upload_id,
        )
        stream = stream_factory()
        chunks = iter(lambda: stream.read(1024 * 1024), b"")
        return uploads.receive_part(upload, part, chunks)


def exchange_bootstrap(body, grant):
    require(
        set(body) == {"bootstrap_token"},
        "invalid_request",
        "Provide bootstrap_token only.",
    )
    token = body.get("bootstrap_token", "")
    require(
        isinstance(token, str) and 20 <= len(token) <= 100,
        "invalid_bootstrap",
        "Invalid bootstrap token.",
        401,
    )
    with transaction.atomic():
        session = get_object_or_404(
            selectors.session_query(True), bootstrap_hash=sessions.token_hash(token)
        )
        return sessions.exchange(session)


def change_session(session_id, credential, body, *, revoke=False):
    require(not body, "invalid_request", "Session lifecycle accepts an empty body.")
    with transaction.atomic():
        session = selectors.viewer_session(session_id, credential, True)
        if revoke:
            session.revoked_at = timezone.now()
        else:
            session.expires_at = timezone.now() + timedelta(minutes=15)
        session.save(update_fields=["expires_at", "revoked_at"])
        return {
            "expires_at": session.expires_at.isoformat(),
            "revoked": bool(session.revoked_at),
        }
