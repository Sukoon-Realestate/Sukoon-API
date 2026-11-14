from functools import partial
from ..services.rental_lifecycle import habitability_commands as commands

from core_apps.features.http import ActionPolicy, FeatureAPIView
from rest_framework.permissions import IsAuthenticated
from core_apps.features.renderers import FeatureJsonRenderer

from rest_framework import serializers as s
from ..rental_lifecycle_serializers import CommandBody
from .common import mutate, validated


class AssessmentBody(CommandBody):
    action = s.ChoiceField(choices=["restrict", "reopen"])
    physical_keys = s.ListField(
        child=s.CharField(max_length=100), max_length=100, allow_empty=False
    )
    evidence_ids = s.ListField(child=s.UUIDField(), max_length=20, allow_empty=False)
    assessed_severity = s.ChoiceField(
        choices=["minor", "major", "urgent"], required=True
    )
    review_at = s.DateTimeField(required=False)
    reason = s.CharField(max_length=4000)


class AssessmentView(FeatureAPIView):
    name = "Assessment"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "habitability",
            "assessment",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, case_id):
        data = validated(AssessmentBody, request.data)

        authorize = partial(
            commands.assessment_post_authorize, actor=request.user, case_id=case_id
        )

        execute = partial(
            commands.assessment_post_execute, actor=request.user, data=data
        )

        return mutate(request, "habitability.assess", authorize, execute)


# Stable callable import for integrations; URLs use the explicit class.
assessment = AssessmentView.as_view()
