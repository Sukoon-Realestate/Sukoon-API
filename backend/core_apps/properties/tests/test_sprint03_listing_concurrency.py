"""Actual PostgreSQL locks serialize competing scalar aliases."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4
import pytest
from django.db import connection, connections
from django.urls import reverse
from rest_framework.test import APIClient
from .test_views import _create_property

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def postgres_only():
    if connection.vendor != "postgresql":
        pytest.skip("Listing races require PostgreSQL row locks")


def run_parallel(calls):
    barrier = Barrier(2)

    def run(call):
        try:
            with connections["default"].cursor() as cursor:
                cursor.execute("SET lock_timeout = '5s'")
            barrier.wait(timeout=10)
            return call()
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run, call) for call in calls]
        return [future.result(timeout=30) for future in futures]


def test_competing_aliases_one_scalar_version_wins(user):
    prop = _create_property(owner=user)
    expected = prop.updated_at.isoformat()

    def write(route, title):
        client = APIClient()
        client.force_authenticate(user)
        return client.patch(
            reverse(route, kwargs={"id": prop.id}),
            {"title": title},
            format="json",
            HTTP_IF_UNMODIFIED_SINCE=expected,
        )

    responses = run_parallel(
        [
            lambda: write("property-detail", "Editor one"),
            lambda: write("property-update", "Editor two"),
        ]
    )
    assert sorted(r.status_code for r in responses) == [200, 409]
    prop.refresh_from_db()
    assert prop.title in {"Editor one", "Editor two"}
    assert prop.review_revision == 2


def test_concurrent_alias_retry_commits_one_revision(user):
    user.is_verified = True
    user.save(update_fields=["is_verified"])
    prop = _create_property(owner=user)
    expected, key = prop.updated_at.isoformat(), str(uuid4())

    def write(route):
        client = APIClient()
        client.force_authenticate(user)
        return client.patch(
            reverse(route, kwargs={"id": prop.id}),
            {"title": "Same edit"},
            format="json",
            HTTP_IF_UNMODIFIED_SINCE=expected,
            HTTP_IDEMPOTENCY_KEY=key,
        )

    responses = run_parallel([lambda: write("property-detail"), lambda: write("property-update")])
    assert [r.status_code for r in responses] == [200, 200]
    assert responses[0].json() == responses[1].json()
    prop.refresh_from_db()
    assert prop.review_revision == 2
