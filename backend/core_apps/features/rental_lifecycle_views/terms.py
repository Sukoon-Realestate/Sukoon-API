import copy
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from core_apps.properties.models import Property
from ..models import TermsProposal, ReservationHold, TenancyInvitation
from ..rental_lifecycle_serializers import AnswerBody
from ..rental_serializers import TermsProposalSerializer
from ..services.rental_lifecycle.common import require_revision, audit
from ..services.rental_lifecycle.consents import record_consent
from ..services.rental_lifecycle.notifications import record_rental_event
from ..services.rental_phase2 import RentalConflict
from .common import endpoint, validated, mutate


@endpoint(["POST"])
def propose_answer(request, proposal_id):
    data = validated(AnswerBody, request.data)

    def authorize():
        item = get_object_or_404(TermsProposal, id=proposal_id, owner=request.user)
        Property.objects.select_for_update().get(pk=item.interest.property_id)
        return TermsProposal.objects.select_for_update().get(pk=item.pk)

    def execute(item):
        from ..services.rental_lifecycle.terms import propose_answer as command

        item = command(item, request.user, data)
        return (
            item,
            TermsProposalSerializer(item, context={"request": request}).data,
            200,
        )

    from ..rental_phase2_views_parts.terms_proposals import proposal_parties
    return mutate(request, f"terms_proposal.answer.{proposal_id}", authorize, execute,
                  account_parties=lambda: proposal_parties(request, proposal_id))
