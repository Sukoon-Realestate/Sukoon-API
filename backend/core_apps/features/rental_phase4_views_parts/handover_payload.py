"""Supported handover imports; current authority lives in the domain service."""

from ..services.handover_reads import (
    _money as _money,
    handover_payload as handover_payload,
    _validate_evidence as _validate_evidence,
    current_actor as current_actor,
    lease_for as lease_for,
    handover_for as handover_for,
)
from ..services.evidence_projection import evidence_payload as evidence_payload

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
MAX_EVIDENCE_BYTES = 5 * 1024 * 1024


def _current_actor(request, lock=False):
    request.user = current_actor(
        request.user,
        request.auth,
        lock=lock,
        write=request.method not in {"GET", "HEAD", "OPTIONS"},
    )


def _lease(request, lease_id, lock=False):
    request.user, lease = lease_for(
        request.user,
        request.auth,
        lease_id,
        lock=lock,
        write=request.method not in {"GET", "HEAD", "OPTIONS"},
    )
    return lease


def _handover(request, handover_id, lock=False):
    request.user, item = handover_for(
        request.user,
        request.auth,
        handover_id,
        lock=lock,
        write=request.method not in {"GET", "HEAD", "OPTIONS"},
    )
    return item


__all__ = [
    "_money",
    "_validate_evidence",
    "current_actor",
    "evidence_payload",
    "handover_for",
    "handover_payload",
    "lease_for",
]
