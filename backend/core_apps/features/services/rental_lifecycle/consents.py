"""Append-only decisions bind the version and exact material reviewed."""

from ...models import RentalConsentRecord
from ..rental_phase2 import fingerprint


def record_consent(item, actor, decision, snapshot=None):
    reviewed = (
        snapshot
        if snapshot is not None
        else {"selection": item.offer_snapshot, "terms": item.terms}
    )
    return RentalConsentRecord.objects.get_or_create(
        actor=actor,
        subject_kind=item._meta.model_name,
        subject_id=item.id,
        subject_revision=item.revision,
        decision=decision,
        defaults={
            "terms_digest": fingerprint(reviewed),
            "policy_version": getattr(item, "policy_version", "")
            or item.terms.get("policy_version", ""),
            "snapshot": reviewed,
        },
    )[0]
