"""Opt-in bounded identity reads; omitted controls preserve legacy envelopes."""
from collections import defaultdict
from dataclasses import dataclass

from django.core.paginator import Paginator, InvalidPage
from django.db.models import Count, F, Window
from django.db.models.functions import RowNumber
from rest_framework import serializers
from rest_framework.exceptions import NotFound


class PageInput(serializers.Serializer):
    page = serializers.IntegerField(min_value=1, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, default=20)


class HistoryInput(serializers.Serializer):
    history_page = serializers.IntegerField(min_value=1, default=1)
    history_page_size = serializers.IntegerField(min_value=1, max_value=20, default=5)


def bounded(params):
    return params.get("bounded") == "true"


def collection_requested(params):
    return bounded(params) or "page" in params or "page_size" in params


def collection_page(rows, params):
    body = PageInput(data=params)
    body.is_valid(raise_exception=True)
    data = body.validated_data
    paginator = Paginator(rows, data["page_size"])
    try:
        page = paginator.page(data["page"])
    except InvalidPage:
        raise NotFound("Invalid page.")
    return list(page.object_list), {
        "page": page.number, "per_page": paginator.per_page,
        "count": paginator.count, "total_pages": paginator.num_pages,
        "next_page": page.next_page_number() if page.has_next() else None,
        "previous_page": page.previous_page_number() if page.has_previous() else None,
    }


@dataclass(frozen=True)
class HistoryPage:
    number: int
    size: int

    @property
    def offset(self):
        return (self.number - 1) * self.size

    def metadata(self, count):
        return {"page": self.number, "per_page": self.size, "count": count,
                "next_page": self.number + 1 if self.offset + self.size < count else None}


def history_page(params):
    if not (bounded(params) or "history_page" in params or "history_page_size" in params):
        return None
    body = HistoryInput(data=params)
    body.is_valid(raise_exception=True)
    data = body.validated_data
    return HistoryPage(data["history_page"], data["history_page_size"])


def prepare_history(items, model, parent, *, page=None, attribute="prepared_history"):
    """Fetch only this page's child rows; window limits apply in SQL per parent."""
    items = list(items)
    ids = [item.pk for item in items]
    if not ids:
        return items
    rows = model.objects.filter(**{parent + "_id__in": ids}).order_by("created_at", "pk")
    counts = {}
    if page:
        counts = dict(rows.order_by().values(parent + "_id").annotate(total=Count("pk"))
                      .values_list(parent + "_id", "total"))
        rows = rows.annotate(history_number=Window(
            expression=RowNumber(), partition_by=[F(parent + "_id")],
            order_by=[F("created_at").asc(), F("pk").asc()],
        )).filter(history_number__gt=page.offset, history_number__lte=page.offset + page.size)
    grouped = defaultdict(list)
    for row in rows:
        grouped[getattr(row, parent + "_id")].append(row)
    for item in items:
        setattr(item, attribute, grouped[item.pk])
        if page:
            setattr(item, attribute + "_page", page.metadata(counts.get(item.pk, 0)))
    return items
