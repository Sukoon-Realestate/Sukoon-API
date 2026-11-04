import pytest
import json
import os
from pathlib import Path
from django.urls import reverse
from .test_views import _create_published_property


@pytest.mark.django_db
def test_empty_results_offer_exact_full_query_counts_without_changing_filters(
    api_client, user
):
    for index in range(12):
        _create_published_property(
            owner=user, title=f"Eligible {index}", price=1000, has_wifi=True
        )
    _create_published_property(
        owner=user, title="Excluded by wifi", price=1000, has_wifi=False
    )
    response = api_client.get(
        reverse("property-list"), {"price_max": "10", "has_wifi": "true"}
    )
    assert response.status_code == 200
    assert response.data["count"] == 0
    if os.environ.get("MVP_FIXTURE_DIR"):
        directory = Path(os.environ["MVP_FIXTURE_DIR"])
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "search_suggestions.json").write_text(
            json.dumps(response.data, indent=2) + "\n", encoding="utf-8"
        )
    suggestions = response.data["search_suggestions"]
    assert suggestions["read_at"]
    price_change = next(
        item
        for item in suggestions["suggestions"]
        if item["remove_filter"] == "price_max"
    )
    assert price_change["result_count"] == 12
    accepted = api_client.get(reverse("property-list"), {"has_wifi": "true"})
    assert accepted.status_code == 200
    assert accepted.data["count"] == 12
    assert len(accepted.data["results"]) < 12
    assert "search_suggestions" not in accepted.data
