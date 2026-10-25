"""Post visit decision: linked invitation."""

from datetime import datetime
from zoneinfo import ZoneInfo
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import APIException
from core_apps.features.models import Lease, TenancyInvitation
from core_apps.features.services.tenancy_invitations import LIVE_LEASE_STATUSES
from core_apps.properties.models import PropertyVisit, PropertyVisitDecision


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


def decision_for(visit, actor=None):
    return visit.participant_decisions.filter(tenant=actor or visit.tenant).first()


def linked_invitation(visit, actor=None):
    tenant = actor or visit.tenant
    """Do not invent a visit link for ambiguous historical invitations."""
    linked = (
        visit.rental_invitations.filter(tenant=tenant)
        .select_related("lease", "property", "owner", "tenant")
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
            tenant=tenant,
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
    from ..viewing_access import participant

    if not participant(visit, actor):
        reason = "not_visit_tenant"
    elif decision:
        reason = "decision_already_recorded"
    elif invitation or ambiguous:
        reason = "continuation_exists"
    elif visit.status != PropertyVisit.Status.CONFIRMED:
        reason = "visit_not_confirmed"
    return {
        "can_submit": reason is None,
        "eligible_at": "",
        "blocked_reason": reason,
    }


def accommodation_identity(snapshot):
    return (
        snapshot.get("rental_scope"),
        tuple(sorted(str(value) for value in snapshot.get("room_ids", []))),
        str(snapshot.get("bed_id") or ""),
    )
