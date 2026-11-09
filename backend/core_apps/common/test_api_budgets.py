"""Sprint 00 fixture-backed query/payload budgets at small (5) and large (40) sizes.

Each screen is measured twice on the same synthetic fixtures: once with SMALL rows and
once after growing to LARGE rows. A screen passes when its query count does not grow
with the row count and stays within the recorded ceiling, and its payload stays within
its byte budget. Ceilings are the Sprint 00 baseline (BASELINE.md benchmark); lower them
when a change improves a screen, never raise them silently.

APIClient + SQLite + force_authenticate: these budgets exclude network, JWT validation
and PostgreSQL plans, and only cover the screens listed here, not the whole API.
Set S00_BUDGET_REPORT=/path.json to record the measurements as evidence.
"""

import json
import os

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from core_apps.admin_api.models import StaffProfile
from core_apps.notifications.models import Notification
from core_apps.properties.models import SavedProperty
from core_apps.properties.tests.conftest import property_types  # noqa: F401 (autouse catalog)
from core_apps.properties.tests.test_saved_properties import create_property

SMALL, LARGE = 5, 40
PAYLOAD_PER_ROW_BYTES = 6_000  # generous first bound; tighten per screen in Sprint 04
PAYLOAD_FIXED_BYTES = 20_000
MEASUREMENTS = {}

# name -> (url builder, client kind, query ceiling, grows with rows)
SCREENS = {
    "tenant-account": (lambda ctx: reverse("my-account"), "tenant", 9, False),
    "tenant-profile": (lambda ctx: reverse("profile-detail"), "tenant", 1, False),
    "tenant-settings": (lambda ctx: reverse("user-settings"), "tenant", 1, False),
    "anonymous-catalog": (lambda ctx: reverse("property-list"), "anonymous", 4, True),
    "tenant-catalog": (lambda ctx: reverse("property-list"), "tenant", 5, True),
    "property-detail": (lambda ctx: reverse("property-detail", args=[ctx["first"].id]), "tenant", 9, False),
    "owner-properties": (lambda ctx: reverse("my-property-list"), "owner", 3, True),
    "saved-properties": (lambda ctx: reverse("saved-property-list"), "tenant", 5, True),
    "governorates": (lambda ctx: reverse("governorate-list"), "anonymous", 2, False),
    "cities": (lambda ctx: reverse("city-list"), "anonymous", 2, False),
    "property-types": (lambda ctx: reverse("property-type-list"), "anonymous", 1, False),
    "notifications": (lambda ctx: reverse("notification-list") + "?scope=tenant", "tenant", 7, True),
    "notification-unread-count": (lambda ctx: reverse("notification-unread-count"), "tenant", 2, False),
}


def grow(ctx, target):
    tenant, owner = ctx["tenant"], ctx["owner"]
    while len(ctx["properties"]) < target:
        index = len(ctx["properties"])
        item = create_property(owner, title=f"Budget listing {index}")
        SavedProperty.objects.create(user=tenant, property=item)
        Notification.objects.create(user=tenant, title=f"Budget notification {index}", data={"workspace": "tenant"})
        ctx["properties"].append(item)
    ctx["first"] = ctx["properties"][0]


def measure(client, url):
    client.get(url)  # warm-up: lazy caches/catalog loads are not per-request cost
    with CaptureQueriesContext(connection) as queries:
        response = client.get(url)
    assert response.status_code == 200, (url, response.status_code, getattr(response, "data", None))
    return len(queries.captured_queries), len(response.content)


@pytest.fixture
def budget_context(db, user, another_user):
    return {"tenant": user, "owner": another_user, "properties": []}


@pytest.fixture(scope="module", autouse=True)
def record_measurements():
    yield
    target = os.environ.get("S00_BUDGET_REPORT")
    if target and MEASUREMENTS:
        existing = {}
        if os.path.exists(target):
            with open(target, encoding="utf-8") as handle:
                existing = json.load(handle)
        existing.update(MEASUREMENTS)
        with open(target, "w", encoding="utf-8") as handle:
            json.dump(existing, handle, indent=2, sort_keys=True)


def client_for(kind, ctx, api_client):
    if kind != "anonymous":
        api_client.force_authenticate(ctx["tenant"] if kind == "tenant" else ctx["owner"])
    return api_client


@pytest.mark.django_db
@pytest.mark.parametrize("screen", sorted(SCREENS))
def test_screen_query_and_payload_budget(screen, budget_context, api_client):
    url_for, kind, ceiling, grows = SCREENS[screen]
    client = client_for(kind, budget_context, api_client)

    grow(budget_context, SMALL)
    small_queries, small_bytes = measure(client, url_for(budget_context))
    grow(budget_context, LARGE)
    large_queries, large_bytes = measure(client, url_for(budget_context))

    MEASUREMENTS[screen] = {"queries": [small_queries, large_queries], "bytes": [small_bytes, large_bytes],
                            "ceiling": ceiling, "rows": [SMALL, LARGE]}
    assert large_queries == small_queries, f"{screen} queries grow with rows: {small_queries} -> {large_queries}"
    assert large_queries <= ceiling, f"{screen} uses {large_queries} queries; baseline ceiling is {ceiling}"
    if grows:  # the fixture must actually reach the page, or the budget proves nothing
        assert large_bytes > small_bytes, f"{screen} payload did not include the added rows"
    rows = LARGE if grows else 1
    assert large_bytes <= PAYLOAD_FIXED_BYTES + rows * PAYLOAD_PER_ROW_BYTES


@pytest.mark.django_db
@pytest.mark.xfail(strict=True, reason="A6-03: admin property list counts ContentView per row (Sprint 04/10)")
def test_admin_property_list_query_count_is_flat(budget_context, api_client):
    StaffProfile.objects.create(user=budget_context["tenant"], role_name="property_reviewer")
    client = client_for("tenant", budget_context, api_client)
    url = reverse("admin-properties-list")
    grow(budget_context, SMALL)
    small_queries, _ = measure(client, url + f"?page_size={LARGE}")
    grow(budget_context, LARGE)
    large_queries, _ = measure(client, url + f"?page_size={LARGE}")
    MEASUREMENTS["admin-properties-list"] = {"queries": [small_queries, large_queries], "rows": [SMALL, LARGE],
                                             "known_defect": "A6-03"}
    assert large_queries == small_queries
