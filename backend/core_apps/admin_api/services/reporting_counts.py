"""Set-based reporting counts without changing the API's interval boundaries."""

from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone


def interval_counts(query, field, intervals):
    # Rolling analytics windows are exact timestamp intervals, not calendar days.
    # At most 90 supported intervals; one aggregate never fetches event rows.
    counts = query.aggregate(
        **{
            f"bucket_{i}": Count(
                "pk", filter=Q(**{f"{field}__gte": start, f"{field}__lt": end})
            )
            for i, (start, end) in enumerate(intervals)
        }
    )
    return [counts[f"bucket_{i}"] for i in range(len(intervals))]


def date_counts(query, field, start, end):
    # Match Django's __date lookup in the active reporting timezone, including DST.
    return dict(
        query.filter(**{f"{field}__date__gte": start, f"{field}__date__lte": end})
        .order_by()
        .annotate(report_day=TruncDate(field, tzinfo=timezone.get_current_timezone()))
        .values_list("report_day")
        .annotate(total=Count("pk"))
    )
