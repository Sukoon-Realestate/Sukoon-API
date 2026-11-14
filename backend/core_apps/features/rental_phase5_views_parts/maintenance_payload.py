"""Supported maintenance helper imports for existing callers."""

from ..services.maintenance_reads import (
    MAINTENANCE_ACTIONS as MAINTENANCE_ACTIONS,
    MAINTENANCE_EVENT_LABELS as MAINTENANCE_EVENT_LABELS,
    _money as _money,
    _assert_private_access as _assert_private_access,
    _safe_evidence as _safe_evidence,
    maintenance_payload as maintenance_payload,
    lease_for as lease_for,
    maintenance_for as maintenance_for,
)


def _lease(request, lease_id, lock=False, servicing=False):
    return lease_for(
        request.user,
        lease_id,
        lock=lock,
        servicing=servicing,
        write=request.method not in {"GET", "HEAD", "OPTIONS"},
    )


def _maintenance(request, request_id, lock=False):
    return maintenance_for(request.user, request_id, lock=lock)


__all__ = [
    "MAINTENANCE_ACTIONS",
    "MAINTENANCE_EVENT_LABELS",
    "_assert_private_access",
    "_money",
    "_safe_evidence",
    "lease_for",
    "maintenance_for",
    "maintenance_payload",
]
