"""Post visit decision: submit decision."""

from copy import deepcopy
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from core_apps.common.idempotency import fingerprint
from core_apps.features.models import IdempotencyRecord
from core_apps.features.services.tenancy_invitations import LIVE_LEASE_STATUSES
from core_apps.properties.models import PropertyVisit, PropertyVisitDecision
from .linked_invitation import (
    OPERATION,
    DecisionConflict,
    invalid,
    decision_for,
    linked_invitation,
    historical_agreement,
    eligibility,
)
from .visit_context import record_event


@transaction.atomic
def submit_decision(actor, visit_id, data):
    visit = get_object_or_404(
        PropertyVisit.objects.select_for_update(of=("self",)).select_related(
            "property", "property__owner", "tenant"
        ),
        id=visit_id,
    )
    from ..viewing_access import participant

    if not participant(visit, actor):
        from rest_framework.exceptions import NotFound

        raise NotFound()
    # Include the visit in the actor/operation-scoped fingerprint. Never persist
    # the reason again in the general-purpose idempotency response store.
    digest = fingerprint({"visit_id": str(visit.id), **data})
    record = IdempotencyRecord.objects.filter(
        user=actor, operation=OPERATION, request_key=str(data["request_key"])
    ).first()
    if record:
        if record.fingerprint != digest:
            raise DecisionConflict(
                "This request key was used for different data.", "idempotency_conflict"
            )
        return visit, False
    original = PropertyVisitDecision.objects.filter(
        tenant=actor, request_key=data["request_key"]
    ).first()
    if original:
        # The immutable decision outlives ordinary idempotency-record retention.
        # Its original operation can still be recovered, but never reused for a
        # different visit or intention after those auxiliary records are purged.
        if (
            original.visit_id != visit.pk
            or original.value != data["decision"]
            or original.reason != data.get("reason", "")
            or original.visit_revision != data["expected_revision"]
        ):
            raise DecisionConflict(
                "This request key was used for different data.", "idempotency_conflict"
            )
        return visit, False
    existing = decision_for(visit, actor)
    if existing:
        if existing.value != data["decision"] or existing.reason != data.get(
            "reason", ""
        ):
            raise DecisionConflict(
                "A different decision is already recorded.", "decision_conflict"
            )
        decision, created = existing, False
    else:
        if visit.revision != data["expected_revision"]:
            raise DecisionConflict("The visit details have changed.", "stale_revision")
        invitation, ambiguous = linked_invitation(visit, actor)
        legacy_lease, legacy_ambiguous = (
            historical_agreement(visit) if not invitation else (None, False)
        )
        action = eligibility(
            visit,
            actor,
            invitation=invitation or legacy_lease,
            ambiguous=ambiguous or legacy_ambiguous,
        )
        if not action["can_submit"]:
            raise DecisionConflict(
                "A decision is not available for this visit.", action["blocked_reason"]
            )
        decision = PropertyVisitDecision.objects.create(
            visit=visit,
            tenant=actor,
            owner=visit.property.owner,
            value=data["decision"],
            reason=data.get("reason", ""),
            attended=True,
            attested_at=timezone.now(),
            visit_revision=visit.revision,
            request_key=data["request_key"],
            property_id_snapshot=visit.property.id,
            offer_id=visit.offer_id,
            offer_snapshot=deepcopy(visit.offer_snapshot),
            scheduled_at=None,
        )
        # Revision changes on decision commit too, without rewriting the appointment.
        visit.revision += 1
        visit.save(update_fields=["revision", "updated_at"])
        record_event(visit, decision)
        created = True
    IdempotencyRecord.objects.create(
        user=actor,
        operation=OPERATION,
        request_key=str(data["request_key"]),
        fingerprint=digest,
        response_data={},
        response_status=200,
        request_subject_id=visit.id,
        result_subject_id=decision.id,
        result_revision=visit.revision,
    )
    # Avoid a cached absent reverse OneToOne after the creation.
    visit.refresh_from_db()
    return visit, created


def validate_invitation_source(property_obj, tenant, data, *, lock=False):
    if not data.get("source_visit_id"):
        invalid(
            "A source visit is required for direct invitations.",
            "source_visit_required",
        )
    if not data.get("source_decision_id"):
        invalid(
            "The tenant's positive decision is required.", "source_decision_required"
        )
    visits = PropertyVisit.objects.all()
    if lock:
        visits = visits.select_for_update(of=("self",))
    visit = get_object_or_404(visits, id=data["source_visit_id"], property=property_obj)
    from ..viewing_access import participant

    if visit.company_id:
        raise DecisionConflict(
            "A company visit cannot create a personal tenancy invitation.",
            "corporate_contract_policy_required",
        )
    if not participant(visit, tenant):
        raise DecisionConflict(
            "The attendee no longer has authority for this viewing.", "source_mismatch"
        )
    decision = decision_for(visit, tenant)
    if (
        not decision
        or str(decision.id) != str(data["source_decision_id"])
        or decision.owner_id != property_obj.owner_id
    ):
        raise DecisionConflict(
            "The decision does not match this visit.", "source_mismatch"
        )
    if decision.value != "proceed":
        raise DecisionConflict(
            "The tenant declined to continue from this visit.", "decision_conflict"
        )
    if visit.offer_id and visit.offer_id != data.get("offer_id", ""):
        raise DecisionConflict(
            "The invitation must preserve the visited offer.", "offer_mismatch"
        )
    if visit.rental_invitations.filter(
        tenant=tenant, lease__status__in=LIVE_LEASE_STATUSES
    ).exists():
        raise DecisionConflict(
            "This visit already has an agreement.", "continuation_exists"
        )
    return visit, decision
