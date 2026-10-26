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
    serializer = RentalDecisionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    from ..services.rental_lifecycle.common import command
    from ..services.negotiation_terms import respond
    from .terms_proposals import proposal_parties

    def authorize():
        return _participant_proposal(request, proposal_id, lock=True, provider_required=False)

    def execute(proposal):
        proposal = respond(proposal, request.user, data)
        return proposal, TermsProposalSerializer(proposal, context={"request": request}).data, 200

    output, status = command(user=request.user, operation=f"terms_proposal.respond.{proposal_id}",
                             data=request.data, authorize=authorize, execute=execute,
                             account_parties=lambda: proposal_parties(request, proposal_id))
    return Response(output, status=status)


def create_interest_invitation(request):
    serializer = RentalInvitationBodySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    interest = _participant_interest(request, data["interest_id"])
    if request.user != interest.property.owner:
        raise PermissionDenied("Only the property owner can create the invitation.")
    assert_owner_ready(request.user, interest.property)
    from ..services.rental_lifecycle.common import command
    from .terms_proposals import interest_parties

    def authorize():
        return _participant_interest(request, data["interest_id"], lock=True)

    def execute(interest):
        proposal = _participant_proposal(request, data["terms_proposal_id"], lock=True)
        from core_apps.chat.moderation.policy import require_business_participants
        from core_apps.users.services.new_business import require_new_business

        if interest.property.owner_id != request.user.pk:
            raise PermissionDenied("Only the current owner may invite the applicant.")
        require_new_business(request.user.pk, interest.tenant_id)
        require_business_participants(request.user, interest.tenant)
        if proposal.interest_id != interest.pk:
            raise ValidationError({"terms_proposal_id": "Proposal does not belong to interest."})
        if proposal.status != TermsProposal.Status.ACCEPTED:
            raise RentalConflict("Both parties must accept the current terms first.")
        if data["interest_revision"] != interest.revision:
            raise RentalConflict("Interest revision conflict.", code="stale_revision")
        if str(data["property_id"]) != str(interest.property.id) or str(data["tenant_id"]) != str(interest.tenant.id):
            raise ValidationError("Invitation participants do not match the interest.")
        if data["offer_id"] != interest.offer_id:
            raise RentalConflict("Keep the selected interest offer.", code="offer_mismatch")
        if proposal.author_id:
            from ..services.negotiation_terms import require_followup, current_selection
            require_followup(proposal, continue_hold=True)
            current_selection(proposal)
            if data["offer_revision"] != proposal.offer_snapshot["offer_revision"]:
                raise RentalConflict("Review the accepted offer version.", code="stale_revision")
            snapshot = proposal.offer_snapshot
        else:
            _, snapshot = resolve_offer_snapshot(
                interest.property, data["offer_id"], data["offer_revision"], request,
            )
        from ..services.rental_application_records import create_invitation
        invitation = create_invitation(interest=interest, proposal=proposal, owner=request.user, snapshot=snapshot)
        resource = TenancyInvitationSerializer(invitation, context={"request": request}).data
        create_notification_for_invitation(request, invitation)
        return invitation, resource, 201

    output, response_status = command(
        user=request.user, operation="rental_invitation.create", data=request.data,
        authorize=authorize, execute=execute,
        account_parties=lambda: interest_parties(request, data["interest_id"]),
    )
    return Response(output, status=response_status)
