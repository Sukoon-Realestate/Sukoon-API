"""Rerunnable conservative import. Legacy content never earns verified averages."""

from datetime import timedelta
from django.db import transaction
from ...models import (
    ReviewCase,
    ReviewOpportunity,
    ReviewSubmission,
    ReviewSection,
    RentalReview,
)
from core_apps.properties.models import PropertyVisitReview
from .policy import POLICY
from .generation import target


@transaction.atomic
def import_one(row, source):
    if ReviewSection.objects.filter(legacy_source=source, legacy_id=row.id).exists():
        return False
    viewing = source == "property_visit_review"
    prop = row.visit.property if viewing else row.lease.property
    author = row.visit.tenant if viewing else row.author
    # A legacy visit did not preserve historical owner identity. Its property
    # record stays legacy, and no response authority is inferred for a new owner.
    if viewing:
        other = getattr(getattr(row.visit, "post_visit_decision", None), "owner", None)
        if other is None:
            other = prop.owner
        kind, subject, audience = "property_visit", prop.id, "public"
    else:
        other = (
            row.lease.owner
            if row.author_id == row.lease.tenant_id
            else row.lease.tenant
        )
        kind, subject, audience = (
            (
                "person_landlord"
                if row.author_id == row.lease.tenant_id
                else "person_tenant"
            ),
            other.id,
            "private",
        )
    if other.pk == author.pk:
        return False
    case, _ = ReviewCase.objects.get_or_create(
        experience_key=f"legacy:{source}:{row.id}",
        defaults={
            "context_type": "legacy",
            "property": prop,
            "party_a": author,
            "party_b": other,
            "visit": row.visit if viewing else None,
            "lease": None if viewing else row.lease,
            "eligible_recorded_at": row.created_at,
            "opens_at": row.created_at,
            "closes_at": row.created_at + timedelta(days=1),
            "gate_released_at": row.created_at,
            "release_mode": "after_moderation",
            "policy_snapshot": POLICY,
            "source_snapshot": {
                "legacy_context": "viewing" if viewing else "tenancy",
                "historical_reply_authority": not viewing
                or hasattr(row.visit, "post_visit_decision"),
            },
        },
    )
    opp, _ = ReviewOpportunity.objects.get_or_create(
        case=case,
        reviewer=author,
        defaults={
            "reviewer_role": "legacy",
            "allowed_targets": [target("legacy", kind, subject)],
            "state": "submitted",
            "submitted_once_at": row.created_at,
        },
    )
    sub, _ = ReviewSubmission.objects.get_or_create(
        opportunity=opp,
        defaults={
            "acting_user": author,
            "request_key": f"legacy:{row.id}",
            "payload_hash": "legacy",
            "receipt": {},
        },
    )
    section = ReviewSection.objects.create(
        submission=sub,
        target_key="legacy",
        subject_kind=kind,
        subject_id=subject,
        audience=audience,
        overall_score=row.overall_rating if viewing else row.rating,
        criteria=(
            {
                "cleanliness_at_visit": row.cleanliness_rating,
                "listing_accuracy": row.listing_accuracy_rating,
                "viewing_interaction": row.owner_interaction_rating,
            }
            if viewing
            else {}
        ),
        original_comment=row.comment,
        public_comment=row.comment,
        content_state="approved",
        verification_basis="legacy_unverified",
        legacy_source=source,
        legacy_id=row.id,
    )
    ReviewSection.objects.filter(pk=section.pk).update(created_at=row.created_at)
    return True


def migrate_legacy():
    result = {"imported": 0, "already_present_or_conflicting": 0}
    for source, query in [
        (
            "property_visit_review",
            PropertyVisitReview.objects.select_related(
                "visit__property", "visit__tenant"
            ),
        ),
        (
            "rental_review",
            RentalReview.objects.select_related(
                "lease__property", "author", "lease__owner", "lease__tenant"
            ),
        ),
    ]:
        for row in query.iterator():
            result[
                (
                    "imported"
                    if import_one(row, source)
                    else "already_present_or_conflicting"
                )
            ] += 1
    return result
