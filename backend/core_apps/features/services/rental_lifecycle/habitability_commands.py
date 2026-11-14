"""Named habitability commands; adapters supply typed data and current actor."""

from django.shortcuts import get_object_or_404
from core_apps.features.services.rental_lifecycle.cases import (
    case_queryset,
    case_payload,
)
from core_apps.features.services.rental_lifecycle.habitability import assess


def assessment_post_authorize(*, actor, case_id):
    return get_object_or_404(case_queryset(actor), id=case_id)


def assessment_post_execute(case, *, actor, data):
    item = assess(actor, case, data)
    return (item, case_payload(item, actor), 200)
