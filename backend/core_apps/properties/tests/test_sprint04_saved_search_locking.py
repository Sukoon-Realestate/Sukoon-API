"""Saved-search scans release the account lock and recheck authority at commit."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event
from types import SimpleNamespace

import pytest
from django.db import connection, connections
from django.db.models import F
from django.http import QueryDict
from rest_framework.exceptions import APIException

from core_apps.properties.models import Property, SavedSearchRead, SavedSearchVisit
from core_apps.properties.services import saved_search_reads as reads
from core_apps.users.models import User
from core_apps.users.services.sessions import issue_refresh
from .test_views import _create_property

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True, params=[False, True])
def storage_mode(settings, request):
    settings.SAVED_SEARCH_ITEMIZED_READS = request.param


def request(user, token=None, **params):
    query = QueryDict(mutable=True)
    query.update({"saved_search_id": "lock-budget", **params})
    return SimpleNamespace(user=user, auth=token, query_params=query)


def test_snapshot_scan_is_outside_shared_transaction(user, monkeypatch, settings):
    _create_property(owner=user)
    from core_apps.properties.services import saved_search_items

    module = saved_search_items if settings.SAVED_SEARCH_ITEMIZED_READS else reads
    name = "write_items" if settings.SAVED_SEARCH_ITEMIZED_READS else "snapshot_values"
    build = getattr(module, name)

    def values(*args, **kwargs):
        assert not connection.in_atomic_block
        return build(*args, **kwargs)

    monkeypatch.setattr(module, name, values)
    req = request(user)
    assert reads.apply_saved_search_read(Property.objects.filter(owner=user), req).count() == 1
    if settings.SAVED_SEARCH_ITEMIZED_READS:
        assert req.saved_search_snapshot.items.count() == 1
    else:
        assert len(req.saved_search_snapshot.versions) == 1


@pytest.mark.parametrize(
    "change,expected", [("revoke", 403), ("epoch", 401), ("definition", 409), ("acknowledge", 409)]
)
def test_postgres_current_authority_and_watermark_are_checked_after_scan(user, monkeypatch, change, expected, settings):
    if connection.vendor != "postgresql":
        pytest.skip("Concurrent row-lock proof requires disposable PostgreSQL")
    _create_property(owner=user)
    token = issue_refresh(user).access_token
    baseline = request(user, token)
    reads.apply_saved_search_read(Property.objects.filter(owner=user), baseline)
    reads.acknowledge(user, baseline.saved_search_snapshot.id, token)
    newer = request(user, token)
    reads.apply_saved_search_read(Property.objects.filter(owner=user), newer)
    before = SavedSearchRead.objects.count()
    entered, release = Event(), Event()
    from core_apps.properties.services import saved_search_items

    module = saved_search_items if settings.SAVED_SEARCH_ITEMIZED_READS else reads
    name = "write_items" if settings.SAVED_SEARCH_ITEMIZED_READS else "snapshot_values"
    build = getattr(module, name)

    def values(*args, **kwargs):
        assert not connection.in_atomic_block
        result = build(*args, **kwargs)
        entered.set()
        assert release.wait(15)
        return result

    monkeypatch.setattr(module, name, values)

    def worker():
        try:
            reads.apply_saved_search_read(Property.objects.filter(owner=user), request(user, token))
            return 200
        except APIException as error:
            return error.status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(worker)
        try:
            assert entered.wait(15)
            with connection.cursor() as cursor:
                cursor.execute("SET lock_timeout = '3s'")
            if change == "revoke":
                User.objects.filter(pk=user.pk).update(is_active=False)
            elif change == "epoch":
                User.objects.filter(pk=user.pk).update(security_epoch=F("security_epoch") + 1)
            elif change == "definition":
                SavedSearchVisit.objects.filter(user=user).update(definition_hash="newer", revision=F("revision") + 1)
            else:
                reads.acknowledge(user, newer.saved_search_snapshot.id, token)
        finally:
            release.set()
        assert future.result(timeout=20) == expected
    assert SavedSearchRead.objects.filter(items_ready=True).count() == before
    assert SavedSearchRead.objects.filter(items_ready=False).count() == int(settings.SAVED_SEARCH_ITEMIZED_READS)
