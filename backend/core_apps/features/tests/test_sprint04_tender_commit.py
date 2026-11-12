"""Tender construction searches without locks and commits only current quotes."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event, Barrier

import pytest
from django.db import connection, connections
from django.db.models import F

from core_apps.features.advanced_tender_models import TenderPackageRun, OwnerBid
from core_apps.features.services.housing_tenders import jobs
from core_apps.users.models import User
from .test_advanced_tender_construction import (
    scenario as scenario_fixture,
    enabled,
    rental_participants,
    published,
    two_unit_bid,
    start,
)  # noqa: F401


@pytest.fixture(name="scenario")
def prepared_scenario(request):
    request.getfixturevalue("enabled")
    return scenario_fixture.__wrapped__(request.getfixturevalue("rental_participants"))


pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.mvp_deferred]


def queued(scenario, monkeypatch):
    monkeypatch.setattr(jobs, "enqueue", lambda _: True)
    tender = published(scenario)
    bid = two_unit_bid(scenario, tender)
    return start(scenario, tender), bid


def test_tender_search_is_outside_atomic(scenario, monkeypatch):
    run, _ = queued(scenario, monkeypatch)
    calculate = jobs.calculate

    def compute(value):
        assert not connection.in_atomic_block
        return calculate(value)

    monkeypatch.setattr(jobs, "calculate", compute)
    assert jobs.process_tender_packages(run["id"]) == "feasible"
    assert TenderPackageRun.objects.get(id=run["id"]).packages.count() == 2


@pytest.mark.parametrize("change", ["withdraw", "revoke"])
def test_postgres_tender_change_during_search_prevents_publication(scenario, monkeypatch, change):
    if connection.vendor != "postgresql":
        pytest.skip("Requires disposable PostgreSQL row locks")
    run, bid = queued(scenario, monkeypatch)
    calculate = jobs.calculate
    done, release = Event(), Event()

    def compute(value):
        assert not connection.in_atomic_block
        result = calculate(value)
        done.set()
        assert release.wait(15)
        return result

    monkeypatch.setattr(jobs, "calculate", compute)

    def worker():
        try:
            return jobs.process_tender_packages(run["id"])
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(worker)
        try:
            assert done.wait(15)
            with connection.cursor() as cursor:
                cursor.execute("SET lock_timeout = '3s'")
            if change == "withdraw":
                OwnerBid.objects.filter(id=bid["id"]).update(status="withdrawn", revision=F("revision") + 1)
            else:
                User.objects.filter(pk=TenderPackageRun.objects.get(id=run["id"]).created_by_id).update(is_active=False)
        finally:
            release.set()
        assert future.result(timeout=20) == "source_changed"
    assert not TenderPackageRun.objects.get(id=run["id"]).packages.exists()


def test_postgres_duplicate_tender_workers_publish_once(scenario, monkeypatch):
    if connection.vendor != "postgresql":
        pytest.skip("Requires disposable PostgreSQL row locks")
    run, _ = queued(scenario, monkeypatch)
    calculate = jobs.calculate
    barrier = Barrier(2)

    def compute(value):
        result = calculate(value)
        barrier.wait(timeout=15)
        return result

    monkeypatch.setattr(jobs, "calculate", compute)

    def worker(_):
        try:
            return jobs.process_tender_packages(run["id"])
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(worker, range(2))) == ["feasible", "feasible"]
    result = TenderPackageRun.objects.get(id=run["id"])
    assert result.revision == 2
    assert result.packages.count() == 2


def test_tender_run_budget(scenario, monkeypatch):
    from tools.qa.performance import measured

    run, _ = queued(scenario, monkeypatch)
    result, report = measured("tender-construction-job", 2, lambda: jobs.process_tender_packages(run["id"]))
    assert result == "feasible"
    assert report["http_calls"] == 0
    assert report["max_transaction_seconds"] < 3
    assert report["peak_python_bytes"] < 64 * 1024 * 1024
