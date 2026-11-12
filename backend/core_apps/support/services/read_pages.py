"""Opt-in support GET pages, prepared only after ticket authorization.

Legacy mutation receipts and GETs retain complete lists. Counts describe current
relations, not a cross-request snapshot; clients should retain ticket revision.
"""

from dataclasses import dataclass

from django.db.models import Count, Prefetch
from rest_framework.exceptions import ValidationError

from core_apps.support.models import TicketAttachment


@dataclass(frozen=True)
class Page:
    number: int
    size: int

    @property
    def start(self):
        return (self.number - 1) * self.size

    def slice(self, queryset):
        return queryset[self.start:self.start + self.size]

    def metadata(self, count):
        return {"count": count, "page": self.number, "page_size": self.size,
                "has_next": self.start + self.size < count}


class ReadPages:
    limits = {
        "messages": (20, 100), "information_requests": (20, 100),
        "internal_notes": (20, 100), "transitions": (20, 100),
        "history": (5, 20), "evidence_versions": (5, 20),
        "attachments": (3, 20),
    }

    def __init__(self, params):
        self.specs = {}
        self.metadata = {}
        for name, (default, maximum) in self.limits.items():
            values = []
            for suffix, fallback, ceiling in (("page", 1, 10000),
                                              ("page_size", default, maximum)):
                key = f"{name}_{suffix}"
                raw = str(params.get(key, fallback))
                if not raw.isascii() or not raw.isdecimal() or len(raw) > 6:
                    raise ValidationError({key: "Use a positive integer."})
                value = int(raw)
                if not 1 <= value <= ceiling:
                    raise ValidationError({key: f"Use a value from 1 to {ceiling}."})
                values.append(value)
            self.specs[name] = Page(*values)

    @classmethod
    def parse(cls, params):
        value = params.get("bounded", "false")
        if value not in {"true", "false"}:
            raise ValidationError({"bounded": "Use true or false."})
        return cls(params) if value == "true" else None

    def select(self, name, queryset):
        spec = self.specs[name]
        self.metadata[name] = spec.metadata(queryset.count())
        return spec.slice(queryset)


def child_counts(model, parent_field, ids):
    return dict(model.objects.filter(**{f"{parent_field}__in": ids})
                .order_by().values(parent_field).annotate(total=Count("pk"))
                .values_list(parent_field, "total")) if ids else {}


def prepare_messages(ticket, pages=None):
    attachments = TicketAttachment.objects.defer("private_content").order_by(
        "created_at", "pk")
    messages = ticket.messages.order_by("created_at", "pk")
    if pages:
        messages = pages.select("messages", messages)
        attachments = pages.specs["attachments"].slice(attachments)
    rows = list(messages.prefetch_related(Prefetch(
        "attachments", queryset=attachments, to_attr="prepared_attachments")))
    # Cache both reverse links for attachment URL projection without per-file SQL.
    for message in rows:
        message.ticket = ticket
    if pages:
        counts = child_counts(TicketAttachment, "message_id", [row.pk for row in rows])
        for message in rows:
            message.read_pages = {"attachments": pages.specs["attachments"].metadata(
                counts.get(message.pk, 0))}
    ticket.prepared_messages = rows
    return rows
