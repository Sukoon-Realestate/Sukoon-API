"""Page complete histories in SQL, hydrating only the selected identities."""

from django.db.models import CharField, F, Value
from django.db.models.functions import Cast, Concat


class HistoryPage:
    ordered = True

    def __init__(self, sources, loader):
        self.loader = loader
        queries = []
        for name, queryset, timestamp, prefix in sources:
            queries.append(
                queryset.order_by()
                .annotate(
                    history_source=Value(name, output_field=CharField()),
                    history_identity=Cast("pk", output_field=CharField()),
                    history_at=F(timestamp),
                    history_key=Concat(Value(prefix), Cast("id", output_field=CharField())),
                )
                .values("history_source", "history_identity", "history_at", "history_key")
            )
        self.query = (
            queries[0].union(*queries[1:], all=True).order_by("-history_at", "-history_key")
            if queries
            else None
        )

    def count(self):
        return self.query.count() if self.query is not None else 0

    def __len__(self):
        return self.count()

    def __getitem__(self, item):
        if not isinstance(item, slice) or item.step not in (None, 1):
            raise TypeError("History pages require a contiguous slice.")
        identities = {}
        if self.query is not None:
            for row in self.query[item]:
                identities.setdefault(row["history_source"], []).append(row["history_identity"])
        return self.loader(identities)
