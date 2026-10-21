"""Rental phase2 views: create interest invitation."""

from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import RentalInterest, TenancyInvitation, TermsProposal
from ..renderers import FeatureJsonRenderer
from ..rental_serializers import (
    RentalDecisionSerializer,
    RentalInvitationBodySerializer,
    TermsProposalSerializer,
)
from ..serializers import TenancyInvitationSerializer
from ..services.rental_phase2 import (
    RentalConflict,
    assert_owner_ready,
    remember_mutation,
)
from ..services.tenancy_invitations import (
    create_notification_for_invitation,
    resolve_offer_snapshot,
)
from .owner_payment_profile import (
    _replay_response,
    _participant_interest,
    _participant_proposal,
)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def terms_proposal_respond(request, proposal_id):
    proposal = _participant_proposal(request, proposal_id)
    serializer = RentalDecisionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    operation = f"terms_proposal.respond.{proposal_id}"
    replay = _replay_response(
        request.user, operation, data["request_key"], request.data
    )
    if replay:
        return replay
    with transaction.atomic():
        proposal = _participant_proposal(request, proposal_id, lock=True)
        if data["expected_revision"] != proposal.revision:
            raise RentalConflict("Proposal revision conflict.", code="stale_revision")
        if proposal.status in {
            TermsProposal.Status.REJECTED,
            TermsProposal.Status.ACCEPTED,
        }:
            raise RentalConflict("This proposal is already closed.")
        decision = data["decision"]
        if decision == "accept":
            from core_apps.chat.moderation.policy import require_business_participants

            require_business_participants(proposal.owner, proposal.interest.tenant)
        actor_id = str(request.user.id)
        from ..services.rental_lifecycle.consents import record_consent

        record_consent(proposal, request.user, decision)
        if decision == "accept":
            proposal.accepted_by = list(
                dict.fromkeys([*proposal.accepted_by, actor_id])
            )
            required = {str(proposal.owner.id), str(proposal.interest.tenant.id)}
            proposal.status = (
                TermsProposal.Status.ACCEPTED
                if required.issubset(set(proposal.accepted_by))
                else TermsProposal.Status.PROPOSED
            )
        elif decision == "reject":
            proposal.status = TermsProposal.Status.REJECTED
        elif decision == "request_changes":
            proposal.status = TermsProposal.Status.CHANGES_REQUESTED
            proposal.accepted_by = []
        else:
            raise ValidationError({"decision": "Unsupported proposal decision."})
        proposal.revision += 1
        proposal.save(update_fields=["accepted_by", "status", "revision", "updated_at"])
        resource = TermsProposalSerializer(proposal, context={"request": request}).data
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=data["request_key"],
            payload=request.data,
            request_subject_id=proposal.id,
            result_subject_id=proposal.id,
            result_revision=proposal.revision,
            resource=resource,
        )
    return Response(output)


def create_interest_invitation(request):
    serializer = RentalInvitationBodySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    interest = _participant_interest(request, data["interest_id"])
    if request.user != interest.property.owner:
        raise PermissionDenied("Only the property owner can create the invitation.")
    assert_owner_ready(request.user, interest.property)
    operation = "rental_invitation.create"
    replay = _replay_response(
        request.user, operation, data["request_key"], request.data
    )
    if replay:
        return replay
    with transaction.atomic():
        interest = _participant_interest(request, data["interest_id"], lock=True)
        proposal = _participant_proposal(request, data["terms_proposal_id"], lock=True)
        from core_apps.chat.moderation.policy import require_business_participants

        require_business_participants(request.user, interest.tenant)
        if proposal.interest_id != interest.pk:
            raise ValidationError(
                {"terms_proposal_id": "Proposal does not belong to interest."}
            )
        if proposal.status != TermsProposal.Status.ACCEPTED:
            raise RentalConflict("Both parties must accept the current terms first.")
        if data["interest_revision"] != interest.revision:
            raise RentalConflict("Interest revision conflict.", code="stale_revision")
        if str(data["property_id"]) != str(interest.property.id) or str(
            data["tenant_id"]
        ) != str(interest.tenant.id):
            raise ValidationError("Invitation participants do not match the interest.")
        if data["offer_id"] != interest.offer_id:
            raise RentalConflict(
                "The invitation must preserve the selected interest offer.",
                code="offer_mismatch",
            )
        _, snapshot = resolve_offer_snapshot(
            interest.property, data["offer_id"], data["offer_revision"], request
        )
        if TenancyInvitation.objects.filter(
            owner=request.user,
            property=interest.property,
            tenant=interest.tenant,
            offer_id=interest.offer_id,
            status__in=[
                TenancyInvitation.Status.PENDING,
                TenancyInvitation.Status.ACCEPTED,
            ],
            lease__isnull=True,
        ).exists():
            raise RentalConflict("A live invitation already exists for this offer.")
        invitation = TenancyInvitation.objects.create(
            property=interest.property,
            owner=request.user,
            tenant=interest.tenant,
            offer_id=interest.offer_id,
            offer_snapshot=snapshot,
            expires_at=timezone.now() + timedelta(days=7),
            initiated_by=request.user,
            interest=interest,
            terms_proposal=proposal,
            provenance_version="independent_interest_v1",
            eligibility_snapshot={
                "interest_revision": interest.revision,
                "proposal_revision": proposal.revision,
                "offer_revision": data["offer_revision"],
            },
        )
        interest.status = RentalInterest.Status.INVITED
        interest.revision += 1
        interest.save(update_fields=["status", "revision", "updated_at"])
        resource = TenancyInvitationSerializer(
            invitation, context={"request": request}
        ).data
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=data["request_key"],
            payload=request.data,
            request_subject_id=interest.id,
            result_subject_id=invitation.id,
            result_revision=invitation.revision,
            resource=resource,
            response_status=201,
        )
        create_notification_for_invitation(request, invitation)
    return Response(output, status=status.HTTP_201_CREATED)
