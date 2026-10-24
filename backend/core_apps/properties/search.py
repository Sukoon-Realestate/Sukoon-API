from functools import lru_cache
from difflib import SequenceMatcher
from django.db import connection
from django.db.models import Q, Case, When, Value, FloatField
from rest_framework.filters import BaseFilterBackend
from rest_framework.exceptions import ValidationError
from .services.search_document import normalize, STOP, AMENITIES


@lru_cache(maxsize=8)
def trigram_available(alias, name):
    if connection.vendor != "postgresql":
        return False
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname='pg_trgm')"
        )
        return cursor.fetchone()[0]


class PropertySearchFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        raw = request.query_params.get("search", "").strip()
        if not raw:
            return queryset
        if len(raw) > 250:
            raise ValidationError(
                {"search": "Search text must not exceed 250 characters."}
            )
        words = normalize(raw).split()
        tokens, negative = [], False
        for word in words:
            if word in {"بدون", "بلا", "no", "without"}:
                negative = True
                continue
            if word in AMENITIES:
                queryset = queryset.filter(**{AMENITIES[word]: not negative})
                negative = False
            elif word not in STOP:
                tokens.append(word)
                negative = False
        tokens = list(dict.fromkeys(tokens))[:12]
        if not tokens:
            return queryset.annotate(search_rank=Value(0.0, output_field=FloatField()))
        phrase = " ".join(tokens)
        if trigram_available(
            connection.alias, connection.settings_dict.get("NAME", "")
        ):
            from django.contrib.postgres.search import (
                TrigramWordSimilarity,
                SearchRank,
                SearchVector,
                SearchQuery,
            )

            for word in tokens:
                match = Q(search_document__contains=word)
                if len(word) >= 3:
                    match |= Q(search_document__trigram_word_similar=word)
                queryset = queryset.filter(match)
            queryset = queryset.annotate(
                search_rank=SearchRank(
                    SearchVector("title", weight="A", config="simple")
                    + SearchVector("search_document", weight="B", config="simple"),
                    SearchQuery(phrase, config="simple"),
                )
                + TrigramWordSimilarity(Value(phrase), "search_document")
            )
        elif connection.vendor == "postgresql":
            # Never silently omit older matches while an administrator provisions
            # pg_trgm. Exact fragments remain complete and database-backed.
            for word in tokens:
                queryset = queryset.filter(search_document__contains=word)
            queryset = queryset.annotate(
                search_rank=Value(1.0, output_field=FloatField())
            )
        else:
            # SQLite/dev and installations awaiting pg_trgm remain useful.
            # Production readiness requires the indexed PostgreSQL path.
            ids, ranks = [], {}
            for identity, title, text in queryset.order_by("-created_at").values_list(
                "pk", "title", "search_document"
            )[:500]:
                split = text.split()
                scores = [
                    (
                        1.0
                        if word in text
                        else (
                            max(
                                (
                                    SequenceMatcher(None, word, candidate).ratio()
                                    for candidate in split
                                ),
                                default=0,
                            )
                            if len(word) >= 3
                            else 0
                        )
                    )
                    for word in tokens
                ]
                if all(score >= 0.72 for score in scores):
                    ids.append(identity)
                    ranks[identity] = sum(scores) + (
                        2 if phrase in normalize(title) else 0
                    )
            queryset = queryset.filter(pk__in=ids).annotate(
                search_rank=Case(
                    *[When(pk=key, then=Value(value)) for key, value in ranks.items()],
                    default=Value(0.0),
                    output_field=FloatField()
                )
            )
        if request.query_params.get("ordering", "relevance") == "relevance":
            queryset = queryset.order_by("-search_rank", "-created_at", "pk")
        return queryset
