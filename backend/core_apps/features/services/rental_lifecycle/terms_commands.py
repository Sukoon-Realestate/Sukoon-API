"""Named terms commands; adapters supply typed data and current actor."""

from django.shortcuts import get_object_or_404
from core_apps.properties.models import Property
from core_apps.features.models import TermsProposal


def propose_answer_post_authorize(*, actor, proposal_id):
    item = get_object_or_404(TermsProposal, id=proposal_id, owner=actor)
    Property.objects.select_for_update().get(pk=item.interest.property_id)
    return TermsProposal.objects.select_for_update().get(pk=item.pk)
