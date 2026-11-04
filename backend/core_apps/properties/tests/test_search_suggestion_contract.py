"""No database/provider needed: exercise canonical-view request isolation."""

from types import SimpleNamespace
from unittest import TestCase
from django.db import DatabaseError
from rest_framework.request import Request
from django.test import RequestFactory

from core_apps.properties.services.search_suggestions import search_suggestions


class SearchSuggestionContractTests(TestCase):
    def test_single_change_preserves_other_filters_and_counts_full_query(self):
        request = Request(
            RequestFactory().get(
                "/",
                {
                    "price_max": "5000",
                    "has_wifi": "true",
                    "city": "authorized-city",
                    "page": "4",
                    "rental_scope": "bed",
                },
            )
        )
        calls = []

        class View:
            def get_queryset(self):
                return "authorized-queryset"

            def filter_queryset(self, queryset):
                calls.append((queryset, self.request.query_params.copy()))
                return SimpleNamespace(count=lambda: 27)

        view = View()
        view.request = request
        result = search_suggestions(view)
        self.assertEqual([s["result_count"] for s in result["suggestions"]], [27, 27])
        self.assertIn("read_at", result)
        for queryset, params in calls:
            self.assertEqual(queryset, "authorized-queryset")
            self.assertEqual(params["city"], "authorized-city")
            self.assertEqual(params["rental_scope"], "bed")
            self.assertNotIn("page", params)
            self.assertEqual(sum(k not in params for k in ["price_max", "has_wifi"]), 1)
        self.assertEqual(request.query_params["page"], "4")
        self.assertEqual(request.query_params["price_max"], "5000")

    def test_maximum_three_positive_alternatives(self):
        from core_apps.properties.services.search_suggestions import RELAXABLE_FILTERS

        view = SimpleNamespace(
            request=Request(
                RequestFactory().get("/", {f: "1" for f in RELAXABLE_FILTERS})
            ),
            get_queryset=lambda: None,
            filter_queryset=lambda _: SimpleNamespace(count=lambda: 9),
        )
        self.assertEqual(len(search_suggestions(view)["suggestions"]), 3)

    def test_database_failure_preserves_an_empty_response_for_reset(self):
        class View:
            request = Request(RequestFactory().get("/", {"price_max": "5000"}))

            def get_queryset(self):
                raise DatabaseError("unavailable")

            def filter_queryset(self, queryset):
                return queryset

        result = search_suggestions(View())
        self.assertEqual(result["suggestions"], [])
        self.assertTrue(result["unavailable"])
