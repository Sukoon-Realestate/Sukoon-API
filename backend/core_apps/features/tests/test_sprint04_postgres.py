"""Disposable PostgreSQL retention contention; not a production load benchmark."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import connection, connections
from django.utils import timezone
from core_apps.features.planning_models import CommuteSearch
from core_apps.features.services.planning import purge_expired_discovery

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.requires_postgres]


def test_concurrent_discovery_sweeps_do_not_rescrub_completed_rows(user):
    CommuteSearch.objects.bulk_create(
        [
            CommuteSearch(user=user, query={"private": i}, expires_at=timezone.now())
            for i in range(6)
        ]
    )
    barrier = Barrier(2)

    def run():
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET lock_timeout = '10s'")
            barrier.wait(timeout=10)
            return purge_expired_discovery(batch_size=3)
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run) for _ in range(2)]
        counts = [future.result(timeout=20) for future in futures]
    assert sum(counts) == 6
    assert (
        CommuteSearch.objects.filter(private_purged_at__isnull=False, query={}).count()
        == 6
    )
    assert purge_expired_discovery() == 0
