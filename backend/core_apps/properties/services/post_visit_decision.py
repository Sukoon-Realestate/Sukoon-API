"""Tenant-attested post-visit decisions and read-only rental continuation."""

from copy import deepcopy
from datetime import datetime
from zoneinfo import ZoneInfo

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import APIException

from core_apps.common.idempotency import fingerprint
from core_apps.features.models import (
    IdempotencyRecord,
    Lease,
    OwnerPaymentProfile,
    TenancyInvitation,
)
from core_apps.features.services.tenancy_invitations import (
    LIVE_LEASE_STATUSES,
    current_invitation_problem,
)
from core_apps.properties.models import Property, PropertyVisit, PropertyVisitDecision

OPERATION = "visit.post_visit_decision"
CAIRO = ZoneInfo("Africa/Cairo")


class DecisionConflict(APIException):
    status_code = 409

    def __init__(self, message, code):
        super().__init__({"message": message, "code": code})


def invalid(message, code):
    error = APIException({"message": message, "code": code})
    error.status_code = 400
    raise error


class PostVisitDecisionBody(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["proceed", "decline"])
    reason = serializers.CharField(
        required=False, allow_blank=True, trim_whitespace=True
    )
    attended = serializers.BooleanField()
    expected_revision = serializers.IntegerField(min_value=1)
    request_key = serializers.UUIDField()

    def validate(self, attrs):
        # Python len(str) and Dart runes.length both count Unicode code points.
        # Boundary whitespace is trimmed; interior newlines and text survive.
        if self.initial_data.get("attended") is not True:
            invalid("Attendance acknowledgment is required.", "attendance_required")
        reason = attrs.get("reason", "")
        if attrs["decision"] == "proceed" and "reason" in attrs:
            invalid(
                "A positive decision must not contain a reason.", "reason_not_allowed"
            )
        if attrs["decision"] == "decline" and not reason:
            invalid(
                "Please tell us why you do not want to continue.", "reason_required"
            )
        if len(reason) > 1000:
            invalid("Your reason must be 1,000 characters or fewer.", "reason_too_long")
        return attrs


def scheduled_at(visit):
    return datetime.combine(visit.visit_date, visit.visit_time, CAIRO)


def decision_for(visit):
    try:
        return visit.post_visit_decision
    except PropertyVisitDecision.DoesNotExist:
        return None


def linked_invitation(visit):
    """Do not invent a visit link for ambiguous historical invitations."""
    linked = (
        visit.rental_invitations.select_related("lease", "property", "owner", "tenant")
        .order_by("-created_at", "-pkid")
        .first()
    )
    if linked:
        return linked, False
    candidates = (
        TenancyInvitation.objects.filter(
            provenance_version="historical_v0",
            source_visit__isnull=True,
            property=visit.property,
            tenant=visit.tenant,
            owner=visit.property.owner,
        )
        .filter(status__in=["pending", "accepted"])
        .select_related("lease", "property", "owner", "tenant")
    )
    if visit.offer_id:
        candidates = candidates.filter(offer_id=visit.offer_id)
    candidates = [
        item for item in candidates if item.lease_id or item.expires_at > timezone.now()
    ]
    if not candidates:
        return None, False
    visits = PropertyVisit.objects.filter(property=visit.property, tenant=visit.tenant)
    if visit.offer_id:
        visits = visits.filter(offer_id=visit.offer_id)
    if len(candidates) == 1 and visits.count() == 1:
        return candidates[0], False
    return None, True


def historical_agreement(visit):
    # Legacy read-only agreements predate the invitation workflow. A unique
    # matching context is a continuation hint, never a fabricated source FK.
    candidates = Lease.objects.filter(
        legacy_read_only=True,
        tenancy_invitation__isnull=True,
        owner=visit.property.owner,
        tenant=visit.tenant,
        property=visit.property,
        status__in=LIVE_LEASE_STATUSES,
    )
    visits = PropertyVisit.objects.filter(property=visit.property, tenant=visit.tenant)
    if visit.offer_id:
        candidates = candidates.filter(offer_id=visit.offer_id)
        visits = visits.filter(offer_id=visit.offer_id)
    items = list(candidates[:2])
    if len(items) == 1 and visits.count() == 1:
        return items[0], False
    return None, bool(items)


def eligibility(visit, actor, *, decision=None, invitation=None, ambiguous=False):
    reason = None
    if actor.pk != visit.tenant_id:
        reason = "not_visit_tenant"
    elif decision:
        reason = "decision_already_recorded"
    elif invitation or ambiguous:
        reason = "continuation_exists"
    elif visit.status != PropertyVisit.Status.CONFIRMED:
        reason = "visit_not_confirmed"
    elif scheduled_at(visit) > timezone.now():
        reason = "visit_not_started"
    return {
        "can_submit": reason is None,
        "eligible_at": scheduled_at(visit).isoformat(),
        "blocked_reason": reason,
    }


def contracting_problem(visit, decision):
    prop = visit.property
    if decision and decision.owner_id != prop.owner_id:
        return "ownership_changed"
    if prop.status != Property.Status.VERIFIED or not prop.is_verified:
        return "property_unavailable"
    if not prop.owner.is_active or not prop.owner.is_verified:
        return "owner_access_changed"
    if not visit.tenant.is_active or not visit.tenant.is_verified:
        return "tenant_access_changed"
    if visit.offer_id:
        offers = (prop.rental_inventory or {}).get("offers", [])
        offer = next(
            (item for item in offers if str(item.get("id")) == visit.offer_id), None
        )
        if (
            not offer
            or offer.get("archived")
            or offer.get("availability") != "available"
        ):
            return "offer_unavailable"
        if visit.offer_snapshot and accommodation_identity(
            offer
        ) != accommodation_identity(visit.offer_snapshot):
            return "accommodation_changed"
        if Lease.objects.filter(
            property=prop, offer_id=visit.offer_id, status__in=LIVE_LEASE_STATUSES
        ).exists():
            return "allocation_conflict"
    return None


def accommodation_identity(snapshot):
    return (
        snapshot.get("rental_scope"),
        tuple(sorted(str(value) for value in snapshot.get("room_ids", []))),
        str(snapshot.get("bed_id") or ""),
    )


def validate_visited_accommodation(visit, snapshot):
    if (
        visit.offer_id
        and visit.offer_snapshot
        and accommodation_identity(snapshot or {})
        != accommodation_identity(visit.offer_snapshot)
    ):
        raise DecisionConflict(
            "The visited accommodation has changed.", "accommodation_changed"
        )


def continuation(
    visit, actor, decision, invitation, ambiguous, actions, legacy_lease=None
):
    owner = actor.pk == visit.property.owner_id
    base = {
        "status": "visit_not_eligible",
        "next_actor": None,
        "next_action": None,
        "blocked_reason": actions["blocked_reason"],
        "source_visit_id": str(visit.id),
        "source_decision_id": str(decision.id) if decision else None,
        "invitation_id": None,
        "agreement_id": None,
        "invoice_id": None,
        "compatibility_version": "visit_decision_v1",
    }
    if legacy_lease:
        base.update(
            status=f"agreement_{legacy_lease.status}",
            agreement_id=str(legacy_lease.id),
            next_action="open_agreement",
            next_actor="both",
            blocked_reason=None,
            compatibility_version="historical_v0",
        )
        return base
    if invitation:
        base.update(
            invitation_id=str(invitation.id),
            compatibility_version=invitation.provenance_version,
            blocked_reason=None,
        )
        if invitation.lease_id:
            lease = invitation.lease
            base.update(
                status=f"agreement_{lease.status}",
                agreement_id=str(lease.id),
                next_action="open_agreement",
                next_actor="both",
            )
            if lease.status in {Lease.Status.SIGNED, Lease.Status.ACTIVE}:
                invoice = (
                    lease.invoices.filter(status__in=["due", "overdue"])
                    .order_by("due_date", "created_at")
                    .first()
                )
                if invoice:
                    base.update(invoice_id=str(invoice.id), next_actor="tenant")
                    if not owner:
                        base["next_action"] = "open_invoice"
            return base
        status = invitation.status
        if status in {"pending", "accepted"}:
            if invitation.expires_at <= timezone.now():
                status = "expired"
            elif current_invitation_problem(invitation):
                status = "revoked"
        base.update(status=f"invitation_{status}", next_action="open_invitation")
        if status == "pending":
            base["next_actor"] = "tenant"
        elif status == "accepted":
            base["next_actor"] = "owner"
            profile = OwnerPaymentProfile.objects.filter(
                owner=visit.property.owner
            ).first()
            if owner and (
                not profile
                or profile.status != "ready"
                or not profile.payout_ready
                or "rental-policy-v1" not in profile.accepted_policy_versions
            ):
                base["next_action"] = "setup_owner_payments"
        return base
    if ambiguous:
        base.update(
            status="contracting_blocked",
            blocked_reason="continuation_exists",
            compatibility_version="historical_v0",
        )
    elif decision and decision.value == "decline":
        base.update(status="declined", blocked_reason=None)
    elif decision:
        problem = contracting_problem(visit, decision)
        if problem:
            base.update(status="contracting_blocked", blocked_reason=problem)
        else:
            base.update(
                status="awaiting_owner_invitation",
                blocked_reason=None,
                next_actor="owner",
                next_action="create_rental_invitation" if owner else None,
            )
    elif actions["can_submit"] or (
        actor.pk != visit.tenant_id
        and visit.status == "confirmed"
        and scheduled_at(visit) <= timezone.now()
    ):
        base.update(
            status="awaiting_tenant_decision",
            blocked_reason=None,
            next_actor="tenant",
            next_action="submit_post_visit_decision" if not owner else None,
        )
    return base


def reason_visible(actor, visit):
    # Owning the property never grants access to the tenant's private text.
    if actor.pk == visit.property.owner_id:
        return False
    if actor.pk == visit.tenant_id:
        return True
    profile = getattr(actor, "staff_profile", None)
    return bool(
        actor.is_active
        and profile
        and profile.is_active
        and profile.role_name in {"support", "system_owner"}
    )


def visit_context(visit, actor):
    decision = decision_for(visit)
    invitation, ambiguous = linked_invitation(visit)
    if invitation and actor.pk not in {invitation.owner_id, invitation.tenant_id}:
        # A later property owner does not acquire another owner's contract or
        # invitation permissions merely by viewing the property's old visit.
        invitation = None
    legacy_lease, legacy_ambiguous = (
        historical_agreement(visit) if not invitation else (None, False)
    )
    ambiguous = ambiguous or legacy_ambiguous
    actions = eligibility(
        visit,
        actor,
        decision=decision,
        invitation=invitation or legacy_lease,
        ambiguous=ambiguous,
    )
    serialized = None
    if decision:
        serialized = {
            "id": str(decision.id),
            "visit_id": str(visit.id),
            "value": decision.value,
            "attended": decision.attended,
            "attendance_source": decision.attendance_source,
            "attested_at": decision.attested_at.isoformat(),
            "created_at": decision.created_at.isoformat(),
            "visit_revision": decision.visit_revision,
        }
        if reason_visible(actor, visit) and decision.value == "decline":
            serialized["reason"] = decision.reason
    return {
        "revision": visit.revision,
        "offer_id": visit.offer_id,
        "offer_snapshot": visit.offer_snapshot,
        "post_visit_decision": serialized,
        "post_visit_actions": actions,
        "rental_continuation": continuation(
            visit, actor, decision, invitation, ambiguous, actions, legacy_lease
        ),
    }


def record_event(visit, decision):
    from core_apps.features.planning_models import PlanningEvent
    from core_apps.notifications.services.notification_service import (
        NotificationService,
    )

    data = {
        "action_type": "view_visit",
        "workspace": "owner",
        "target_id": str(visit.id),
        "visit_id": str(visit.id),
        "property_id": str(visit.property.id),
        "source_decision_id": str(decision.id),
        "event_kind": "visit_post_decision",
        "schema_version": "1",
    }
    event = PlanningEvent.objects.create(
        recipient=visit.property.owner,
        event_key=f"visit.post_visit_decision:{decision.id}",
        destination=data,
    )
    data["event_id"] = str(event.id)
    event.notification = NotificationService.create_notification(
        user=visit.property.owner,
        title="قرار المستأجر بعد المعاينة / Tenant visit decision",
        body=(
            "يرغب المستأجر في المتابعة / The tenant would like to proceed."
            if decision.value == "proceed"
            else "اختار المستأجر عدم المتابعة / The tenant chose not to continue."
        ),
        category="visit_post_decision",
        data=data,
        send_push=False,
    )
    event.save(update_fields=["notification", "updated_at"])
    # The existing periodic process_planning_jobs task drains/retries this outbox.
    # No provider request is made in the decision transaction.


@transaction.atomic
def submit_decision(actor, visit_id, data):
    visit = get_object_or_404(
        PropertyVisit.objects.select_for_update(of=("self",)).select_related(
            "property", "property__owner", "tenant"
        ),
        id=visit_id,
        tenant=actor,
    )
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
    existing = decision_for(visit)
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
        invitation, ambiguous = linked_invitation(visit)
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
            scheduled_at=scheduled_at(visit),
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
    visits = PropertyVisit.objects.select_related("post_visit_decision")
    if lock:
        visits = visits.select_for_update(of=("self",))
    visit = get_object_or_404(
        visits, id=data["source_visit_id"], property=property_obj, tenant=tenant
    )
    decision = decision_for(visit)
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
    if visit.rental_invitations.filter(lease__status__in=LIVE_LEASE_STATUSES).exists():
        raise DecisionConflict(
            "This visit already has an agreement.", "continuation_exists"
        )
    return visit, decision


def validate_invitation_provenance(invitation):
    """Defend draft creation too; historical and independent origins stay valid."""
    if invitation.provenance_version == "historical_v0":
        return
    if (
        invitation.provenance_version == "independent_interest_v1"
        and invitation.interest_id
    ):
        return
    if not invitation.source_visit_id or not invitation.source_decision_id:
        raise DecisionConflict(
            "The invitation has no valid source decision.", "source_mismatch"
        )
    decision = invitation.source_decision
    visit = invitation.source_visit
    if (
        decision.visit_id != visit.pk
        or decision.value != "proceed"
        or decision.tenant_id != invitation.tenant_id
        or decision.owner_id != invitation.owner_id
        or visit.property_id != invitation.property_id
        or (visit.offer_id and invitation.offer_id != visit.offer_id)
    ):
        raise DecisionConflict(
            "The invitation source no longer matches.", "source_mismatch"
        )
