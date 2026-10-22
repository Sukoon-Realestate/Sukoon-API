import csv
import io
import pytest
from .test_rental_phase4 import phase4_lease, client_for

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("days", [7, 30, 90])
@pytest.mark.parametrize("language", ["ar", "en"])
def test_csv_matches_authorized_metrics_and_unknown_values(phase4_lease, days, language):
    owner, tenant, lease = phase4_lease
    path = f"/api/v1/features/v1/owner-analytics/{lease.property.id}/"
    query = {"period_days": days, "lang": language}
    client = client_for(owner)
    report = client.get(path, query).data
    result = client.get(path + "export/", query)
    assert result.status_code == 200
    assert result.content.startswith(b"\xef\xbb\xbf")
    assert result["Cache-Control"] == "private, no-store"
    rows = list(csv.DictReader(io.StringIO(result.content.decode("utf-8-sig"))))
    assert len(rows) == len(report["metrics"])
    for row, metric in zip(rows, report["metrics"]):
        assert row["metric"] == metric["key"]
        assert row["label"] == metric["label"]
        assert row["value"] == ("" if metric["value"] is None else str(metric["value"]))
        assert row["unit"] == metric["unit"]
    assert client_for(tenant).get(path + "export/").status_code == 404
    assert client.get(path + "export/", {"period_days": 365}).status_code == 400


def test_csv_formula_protection_preserves_numeric_values():
    from core_apps.features.views_parts.listing_suggestions import csv_cell
    assert csv_cell(" =SUM(A1:A9)").startswith("'")
    assert csv_cell("@cmd").startswith("'")
    assert csv_cell(-2) == "-2"
    assert csv_cell(None) == ""
