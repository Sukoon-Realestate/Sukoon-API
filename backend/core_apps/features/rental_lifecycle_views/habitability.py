from django.shortcuts import get_object_or_404
from rest_framework import serializers as s
from ..services.rental_lifecycle.cases import case_queryset, case_payload
from ..services.rental_lifecycle.habitability import assess
from ..rental_lifecycle_serializers import CommandBody
from .common import endpoint, mutate, validated


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


@endpoint(["POST"])
def assessment(request, case_id):
    data = validated(AssessmentBody, request.data)

    def authorize():
        return get_object_or_404(case_queryset(request.user), id=case_id)

    def execute(case):
        item = assess(request.user, case, data)
        return item, case_payload(item, request.user), 200

    return mutate(request, "habitability.assess", authorize, execute)
