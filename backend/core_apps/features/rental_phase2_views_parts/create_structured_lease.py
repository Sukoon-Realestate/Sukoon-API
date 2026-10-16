"""Rental phase2 views: create structured lease."""

from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from ..models import Lease, TenancyInvitation
from ..rental_serializers import (
    LeasePhase2Serializer,
    RentalAgreementDraftBodySerializer,
)
from ..services.rental_phase2 import (
    RentalConflict,
    assert_owner_ready,
    remember_mutation,
    reserve_inventory_days,
)
from ..services.tenancy_invitations import resolve_offer_snapshot
from .owner_payment_profile import (
    _replay_response,
    _json_safe,
    _validate_terms_offer,
    _event,
)


def create_structured_lease(request):
    serializer = RentalAgreementDraftBodySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    invitation = get_object_or_404(
        TenancyInvitation.objects.select_related("property", "owner", "tenant"),
        id=data["invitation_id"],
        owner=request.user,
    )
    operation = "rental_agreement.create"
    replay = _replay_response(
        request.user, operation, data["request_key"], request.data
    )
    if replay:
        return replay
    with transaction.atomic():
        from core_apps.properties.models import Property

        Property.objects.select_for_update().get(pk=invitation.property_id)
        invitation = (
            TenancyInvitation.objects.select_for_update(of=("self",))
            .select_related("property", "owner", "tenant", "terms_proposal")
            .get(pk=invitation.pk)
        )
        assert_owner_ready(request.user, invitation.property)
        if invitation.status != TenancyInvitation.Status.ACCEPTED:
            raise RentalConflict(
                "The invitation is not accepted.", code="offer_unavailable"
            )
        if invitation.lease_id or invitation.consumed_at:
            raise RentalConflict(
                "The invitation was already consumed.", code="invitation_consumed"
            )
        if invitation.expires_at <= timezone.now():
            raise RentalConflict("The invitation expired.", code="invitation_expired")
        if data["invitation_revision"] != invitation.revision:
            raise RentalConflict("Invitation revision conflict.", code="stale_revision")
        if str(data["property_id"]) != str(invitation.property.id) or str(
            data["tenant_id"]
        ) != str(invitation.tenant.id):
            raise ValidationError("Agreement participants do not match the invitation.")
        from core_apps.properties.services.post_visit_decision import (
            DecisionConflict,
            validate_invitation_provenance,
        )

        validate_invitation_provenance(invitation)
        from ..services.tenancy_invitations import validate_accounts

        validate_accounts(request.user, invitation.tenant, request)
        if invitation.property.status != invitation.property.Status.VERIFIED:
            raise DecisionConflict(
                "The property is not available for leasing.", "property_unavailable"
            )
        if data["offer_id"] != invitation.offer_id:
            raise DecisionConflict(
                "The agreement must preserve the accepted invitation's offer.",
                "offer_mismatch",
            )
        if data["offer_revision"] != (invitation.offer_snapshot or {}).get(
            "offer_revision"
        ):
            raise DecisionConflict(
                "The accepted offer has changed; a fresh invitation is required.",
                "stale_revision",
            )
        _, snapshot = resolve_offer_snapshot(
            invitation.property, data["offer_id"], data["offer_revision"], request
        )
        if snapshot != invitation.offer_snapshot:
            raise DecisionConflict(
                "The accepted accommodation has changed.", "accommodation_changed"
            )
        _validate_terms_offer(data["terms"], snapshot)
        if (
            invitation.terms_proposal
            and _json_safe(data["terms"]) != invitation.terms_proposal.terms
        ):
            raise RentalConflict("The reviewed terms changed.", code="document_changed")
        lease = Lease.objects.create(
            property=invitation.property,
            owner=request.user,
            tenant=invitation.tenant,
            template_id=data["terms"]["template_id"],
            template_version=data["terms"]["template_version"],
            start_date=data["terms"]["starts_on"],
            end_date=data["terms"]["ends_on_exclusive"],
            rent_amount_minor=data["terms"]["monthly_rent"]["amount_minor"],
            rent_currency="EGP",
            rent_exponent=2,
            offer_id=data["offer_id"],
            offer_snapshot=snapshot,
            terms=_json_safe(data["terms"]),
            policy_version="rental-policy-v1",
            legacy_read_only=False,
            hold_expires_at=timezone.now()
            + timedelta(minutes=settings.RENTAL_HOLD_TTL_MINUTES),
        )
        from ..services.rental_lifecycle.reservations import transfer_hold

        if not transfer_hold(lease, invitation.terms_proposal):
            reserve_inventory_days(
                lease, lease.start_date, lease.end_date, lease.hold_expires_at
            )
        from ..models import GroupBookingParticipant

        GroupBookingParticipant.objects.filter(invitation=invitation).update(
            lease=lease
        )
        invitation.lease = lease
        invitation.consumed_at = timezone.now()
        invitation.save(update_fields=["lease", "consumed_at", "updated_at"])
        _event(lease, request.user, "draft_created", "Agreement draft created")
        resource = LeasePhase2Serializer(lease, context={"request": request}).data
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=data["request_key"],
            payload=request.data,
            request_subject_id=invitation.id,
            result_subject_id=lease.id,
            result_revision=lease.revision,
            resource=resource,
            response_status=201,
        )
    return Response(output, status=status.HTTP_201_CREATED)
