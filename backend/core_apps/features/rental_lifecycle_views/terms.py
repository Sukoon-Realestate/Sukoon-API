from functools import partial
from ..services.rental_lifecycle import terms_commands as commands

from core_apps.features.http import ActionPolicy, FeatureAPIView
from rest_framework.permissions import IsAuthenticated
from core_apps.features.renderers import FeatureJsonRenderer

from ..rental_lifecycle_serializers import AnswerBody
from ..rental_serializers import TermsProposalSerializer
from .common import validated, mutate


class ProposeAnswerView(FeatureAPIView):
    name = "Propose Answer"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "terms", "propose_answer", boundary="standard", capability=None, typed=False
        ),
    }

    def post(self, request, proposal_id):
        data = validated(AnswerBody, request.data)

        authorize = partial(
            commands.propose_answer_post_authorize,
            actor=request.user,
            proposal_id=proposal_id,
        )

        def execute(item):
            from ..services.rental_lifecycle.terms import propose_answer as command

            item = command(item, request.user, data)
            return (
                item,
                TermsProposalSerializer(item, context={"request": request}).data,
                200,
            )

        from ..rental_phase2_views_parts.terms_proposals import proposal_parties

        return mutate(
            request,
            f"terms_proposal.answer.{proposal_id}",
            authorize,
            execute,
            account_parties=lambda: proposal_parties(request, proposal_id),
        )


# Stable callable import for integrations; URLs use the explicit class.
propose_answer = ProposeAnswerView.as_view()
