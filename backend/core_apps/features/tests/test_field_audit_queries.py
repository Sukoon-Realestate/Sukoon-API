import pytest

from core_apps.features.tests.test_rental_phase5 import phase5_lease, client_for

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "collection",
    [
        "billing-schedule",
        "timeline",
        "handovers",
        "maintenance-requests",
        "payment-extension-requests",
        "amendments",
        "renewals",
        "termination-requests",
        "external-payment-claims",
    ],
)
def test_lease_list_identity_comes_from_url_and_authenticated_participant(
    phase5_lease, collection
):
    owner, tenant, lease = phase5_lease
    path = f"/api/v1/features/v1/leases/{lease.id}/{collection}/"
    for participant in (owner, tenant):
        client = client_for(participant)
        current = client.get(path, {"page": 1, "page_size": 20})
        legacy = client.get(
            path,
            {
                "page": 1,
                "page_size": 20,
                "workspace": "owner" if participant == owner else "tenant",
                "lease_id": str(lease.id),
            },
        )
        assert current.status_code == legacy.status_code == 200
        assert current.json() == legacy.json()
        assert set(current.json()) == {"message", "data"}
        assert isinstance(current.json()["data"], list)
        assert current["X-Total-Count"] == legacy["X-Total-Count"]
    outsider = type(owner).objects.create_user(
        email="query-outsider@example.com", password="pass"
    )
    denied = client_for(outsider).get(path, {"workspace": "owner"})
    assert denied.status_code == 404 and denied.json()["data"] is None


def test_analytics_language_changes_explanations_not_metric_identity(phase5_lease):
    owner, tenant, lease = phase5_lease
    client = client_for(owner)
    path = f"/api/v1/features/v1/owner-analytics/{lease.property.id}/"
    english = client.get(path, {"period_days": 30, "lang": "en"}).json()["data"]
    arabic = client.get(path, {"period_days": 30, "lang": "ar"}).json()["data"]
    assert arabic["methodology"] != english["methodology"]
    assert arabic["metrics"][0]["label"] == "الزوار الفريدون"
    for left, right in zip(english["metrics"], arabic["metrics"]):
        assert left["label"] != right["label"]
        assert left["definition"] != right["definition"]
        assert {k: left[k] for k in ("key", "value", "unit")} == {
            k: right[k] for k in ("key", "value", "unit")
        }
    header = client.get(path, HTTP_ACCEPT_LANGUAGE="ar-EG").json()["data"]
    assert header["metrics"] == arabic["metrics"]
    for params in ({}, {"lang": ""}, {"lang": "unknown"}):
        assert client.get(path, params).json()["data"]["metrics"] == english["metrics"]
    denied = client_for(tenant).get(path, {"lang": "ar"})
    assert denied.status_code == 404 and denied.json()["data"] is None
