"""Measured owner acceptance: confirmed / (confirmed + rejected) visits."""

from django.db.models import Count, Q
from ..models import PropertyVisit


def visit_acceptance(queryset):
    counts = queryset.aggregate(
        confirmed=Count("pk", filter=Q(status=PropertyVisit.Status.CONFIRMED)),
        rejected=Count("pk", filter=Q(status=PropertyVisit.Status.REJECTED)),
    )
    handled = counts["confirmed"] + counts["rejected"]
    return (round(counts["confirmed"] * 100 / handled) if handled else None), handled
