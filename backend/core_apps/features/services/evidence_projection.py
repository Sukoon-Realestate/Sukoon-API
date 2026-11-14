"""Metadata for authorized rental evidence; byte access is checked separately."""

from ..models import RentalEvidence


def evidence_payload(item):
    return {
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "name": item.original_name,
        "mime_type": item.content_type,
        "size_bytes": item.size_bytes,
        "media_metadata": item.media_metadata or {},
        "status": (
            "ready"
            if item.malware_status == RentalEvidence.MalwareStatus.SAFE
            else item.malware_status
        ),
        "sha256": item.sha256,
        "revision": item.revision,
    }
