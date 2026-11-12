"""Bounded snapshot buffers, cross-format compatibility, cleanup and rollback."""

from datetime import timedelta
from hashlib import sha256
from io import StringIO
from uuid import uuid4

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.urls import reverse
from django.utils import timezone
from rest_framework.exceptions import APIException

from core_apps.properties.models import Property, SavedSearchRead, SavedSearchReadItem, SavedSearchVisit
from core_apps.properties.services import saved_search_reads as reads
from core_apps.properties.services.saved_search_items import materialize_legacy_baseline
from core_apps.properties.tasks import purge_saved_search_reads
from .test_saved_search_reads import read, ack
from .test_sprint04_saved_search_locking import request
from .test_views import _create_property, _create_published_property
from tools.qa.performance import measured

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("size", [1, 100, 2000])
def test_itemized_snapshot_uses_bounded_buffers_and_empty_json(size, settings, user, monkeypatch):
    settings.SAVED_SEARCH_ITEMIZED_READS = True
    prop = _create_property(owner=user)
    Property.objects.bulk_create(
        [
            Property(
                owner=user,
                title=f"Snapshot {index}",
                price=1000,
                property_type=prop.property_type,
                governorate=prop.governorate,
                city=prop.city,
                district="Test",
            )
            for index in range(size - 1)
        ]
    )
    insert = SavedSearchReadItem.objects.bulk_create
    batches = []

    def bounded_batch(rows, **kwargs):
        assert connection.in_atomic_block  # Receipt-local batch, never the account lock.
        batches.append(len(rows))
        assert len(rows) <= 500
        return insert(rows, **kwargs)

    monkeypatch.setattr(SavedSearchReadItem.objects, "bulk_create", bounded_batch)
    settings.SAVED_SEARCH_ITEMIZED_READS = False
    control = request(user, saved_search_id="legacy-budget")
    legacy_rows, _ = measured(
        "saved-search-legacy",
        size,
        lambda: list(reads.apply_saved_search_read(Property.objects.filter(owner=user), control)[:5]),
    )
    assert len(control.saved_search_snapshot.versions) == size
    settings.SAVED_SEARCH_ITEMIZED_READS = True
    req = request(user)
    rows, report = measured(
        "saved-search-itemized",
        size,
        lambda: list(reads.apply_saved_search_read(Property.objects.filter(owner=user), req)[:5]),
    )
    snapshot = req.saved_search_snapshot
    assert snapshot.itemized and snapshot.items_ready
    assert snapshot.versions == snapshot.changes == {}
    assert snapshot.items.count() == size
    assert len(rows) == min(5, size)
    assert [row.id for row in rows] == [row.id for row in legacy_rows]
    assert sum(batches) == size
    assert report["http_calls"] == 0
    assert report["peak_python_bytes"] < 8 * 1024 * 1024


def test_itemized_reader_handles_legacy_baseline_and_creation_can_be_disabled(settings, user, auth_client):
    prop = _create_published_property(owner=user)
    settings.SAVED_SEARCH_ITEMIZED_READS = False
    first = read(auth_client)
    assert ack(auth_client, first).status_code == 200
    settings.SAVED_SEARCH_ITEMIZED_READS = True
    current = read(auth_client)
    assert current.status_code == 200
    assert current.data["saved_search_read"]["new_count"] == 0
    assert ack(auth_client, current).status_code == 200
    visit = SavedSearchVisit.objects.get(user=user)
    assert visit.versions == {} and visit.acknowledged_read_id
    settings.SAVED_SEARCH_ITEMIZED_READS = False
    replay = read(auth_client, saved_search_read_id=current.data["saved_search_read"]["read_id"])
    assert replay.status_code == 200
    assert replay.data["saved_search_read"]["new_count"] == 0
    legacy = read(auth_client)
    assert legacy.status_code == 200
    assert legacy.data["saved_search_read"]["new_count"] == 0
    receipt = SavedSearchRead.objects.get(id=legacy.data["saved_search_read"]["read_id"])
    assert not receipt.itemized and str(prop.id) in receipt.versions
    assert ack(auth_client, legacy).status_code == 200
    visit.refresh_from_db()
    assert visit.acknowledged_read_id is None and str(prop.id) in visit.versions


def test_incomplete_snapshots_cannot_be_read_or_acknowledged(settings, user):
    settings.SAVED_SEARCH_ITEMIZED_READS = True
    prop = _create_property(owner=user)
    req = request(user)
    reads.apply_saved_search_read(Property.objects.filter(pk=prop.pk), req)
    snapshot = req.saved_search_snapshot
    snapshot.items_ready = False
    snapshot.save(update_fields=["items_ready"])
    with pytest.raises(APIException) as error:
        reads.apply_saved_search_read(Property.objects.all(), request(user, saved_search_read_id=str(snapshot.id)))
    assert error.value.status_code == 409
    with pytest.raises(APIException) as error:
        reads.acknowledge(user, snapshot.id)
    assert error.value.status_code == 409


def test_rollback_materializes_baseline_only_after_creation_stops(settings, user, auth_client):
    settings.SAVED_SEARCH_ITEMIZED_READS = True
    prop = _create_published_property(owner=user)
    first = read(auth_client)
    assert ack(auth_client, first).status_code == 200
    visit = SavedSearchVisit.objects.select_related("acknowledged_read").get(user=user)
    observed_revision, observed_read_at = visit.revision, visit.last_read_at
    output = StringIO()
    call_command("materialize_saved_search_baselines", stdout=output)
    visit.refresh_from_db()
    assert visit.versions == {} and visit.acknowledged_read_id
    with pytest.raises(CommandError):
        call_command("materialize_saved_search_baselines", apply=True, stdout=StringIO())
    settings.SAVED_SEARCH_ITEMIZED_READS = False
    call_command("materialize_saved_search_baselines", apply=True, stdout=StringIO())
    visit.refresh_from_db()
    assert visit.revision == observed_revision and visit.last_read_at == observed_read_at
    assert visit.acknowledged_read_id is None
    assert visit.versions[str(prop.id)] == reads.version(prop)
    assert read(auth_client).data["saved_search_read"]["new_count"] == 0


def test_item_cleanup_resumes_in_bounded_batches_and_preserves_watermark(settings, user):
    settings.SAVED_SEARCH_ITEMIZED_READS = True
    _create_property(owner=user)
    req = request(user)
    reads.apply_saved_search_read(Property.objects.all(), req)
    snapshot = req.saved_search_snapshot
    reads.acknowledge(user, snapshot.id)
    visit = SavedSearchVisit.objects.get(user=user)
    SavedSearchReadItem.objects.bulk_create(
        [
            SavedSearchReadItem(read=snapshot, property_identity=uuid4(), review_revision=1, modified_at=timezone.now())
            for _ in range(500)
        ]
    )
    SavedSearchRead.objects.filter(pk=snapshot.pk).update(expires_at=timezone.now() - timedelta(days=31))
    # An active watermark is retained even if an old expiry was imported.
    assert purge_saved_search_reads() == 0
    assert SavedSearchReadItem.objects.filter(read=snapshot).count() == 501
    SavedSearchVisit.objects.filter(pk=visit.pk).update(last_read_at=timezone.now() - timedelta(days=31))
    assert purge_saved_search_reads() == 0
    assert SavedSearchReadItem.objects.filter(read=snapshot).count() == 1
    assert purge_saved_search_reads() == 1
    visit.refresh_from_db()
    assert visit.last_read_at is not None and visit.acknowledged_read_id is None
    assert not SavedSearchRead.objects.filter(pk=snapshot.pk).exists()


def test_old_reader_models_can_insert_after_forward_migration(settings, user):
    settings.SAVED_SEARCH_ITEMIZED_READS = False
    prop = _create_property(owner=user)
    req = request(user)
    apps = MigrationLoader(connection).project_state([("properties", "0045_viewing_arrival_cards")]).apps
    OldVisit, OldRead = apps.get_model("properties", "SavedSearchVisit"), apps.get_model(
        "properties", "SavedSearchRead"
    )
    digest = reads.definition(req.query_params)
    visit = OldVisit.objects.create(
        user_id=user.pk,
        workspace="individual",
        identity="lock-budget",
        identity_hash=sha256(b"lock-budget").hexdigest(),
        definition_hash=digest,
    )
    snapshot = OldRead.objects.create(
        visit_id=visit.pk,
        definition_hash=digest,
        base_revision=1,
        versions={str(prop.id): reads.version(prop)},
        changes={},
        baseline_state="first_visit",
        read_at=timezone.now(),
        expires_at=timezone.now() + timedelta(minutes=15),
    )
    current = SavedSearchRead.objects.get(pk=snapshot.pk)
    assert current.itemized is None and current.items_ready is None
    result = reads.apply_saved_search_read(Property.objects.all(), request(user, saved_search_read_id=str(current.id)))
    assert list(result.values_list("id", flat=True)) == [prop.id]
    assert reads.acknowledge(user, current.id)["acknowledged"]


def test_rollback_retires_expired_children_but_keeps_the_expired_receipt(settings, user):
    from core_apps.properties.services.saved_search_items import retire_expired_itemized_reads

    settings.SAVED_SEARCH_ITEMIZED_READS = True
    _create_property(owner=user)
    req = request(user)
    reads.apply_saved_search_read(Property.objects.all(), req)
    snapshot = req.saved_search_snapshot
    with pytest.raises(ValueError):
        retire_expired_itemized_reads()
    settings.SAVED_SEARCH_ITEMIZED_READS = False
    assert retire_expired_itemized_reads() == 0  # Live receipts must drain first.
    SavedSearchRead.objects.filter(pk=snapshot.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
    assert retire_expired_itemized_reads() == 1
    snapshot.refresh_from_db()
    assert snapshot.itemized is False
    assert snapshot.versions == snapshot.changes == {}
    assert not snapshot.items.exists()
    with pytest.raises(APIException) as error:
        reads.apply_saved_search_read(Property.objects.all(), request(user, saved_search_read_id=str(snapshot.id)))
    assert error.value.status_code == 410


def test_runtime_configuration_exposes_the_saved_search_rollout_mode(settings):
    from config.runtime import configuration_identity

    settings.SAVED_SEARCH_ITEMIZED_READS = False
    legacy = configuration_identity()
    settings.SAVED_SEARCH_ITEMIZED_READS = True
    current = configuration_identity()
    assert legacy["saved_search_itemized_reads"] is False
    assert current["saved_search_itemized_reads"] is True
    assert legacy["database_fingerprint"] == current["database_fingerprint"]


def test_rollback_cannot_overwrite_a_newer_baseline(settings, user):
    settings.SAVED_SEARCH_ITEMIZED_READS = True
    _create_property(owner=user)
    req = request(user)
    reads.apply_saved_search_read(Property.objects.all(), req)
    reads.acknowledge(user, req.saved_search_snapshot.id)
    observed = SavedSearchVisit.objects.select_related("acknowledged_read").get(user=user)
    SavedSearchVisit.objects.filter(pk=observed.pk).update(
        revision=observed.revision + 1, versions={"newer": [1, "value"]}
    )
    settings.SAVED_SEARCH_ITEMIZED_READS = False
    assert materialize_legacy_baseline(observed, apply=True) == "source_changed"
    observed.refresh_from_db()
    assert observed.versions == {"newer": [1, "value"]}
    assert observed.acknowledged_read_id is not None


def test_closed_accounts_are_not_copied_back_into_legacy_json(settings, user):
    settings.SAVED_SEARCH_ITEMIZED_READS = True
    _create_property(owner=user)
    req = request(user)
    reads.apply_saved_search_read(Property.objects.all(), req)
    reads.acknowledge(user, req.saved_search_snapshot.id)
    from core_apps.users.models import User

    User.objects.filter(pk=user.pk).update(closed_at=timezone.now(), is_active=False)
    settings.SAVED_SEARCH_ITEMIZED_READS = False
    visit = SavedSearchVisit.objects.select_related("acknowledged_read").get(user=user)
    assert materialize_legacy_baseline(visit, apply=True) == "closed_erased"
    visit.refresh_from_db()
    assert visit.versions == {} and visit.acknowledged_read_id is None


def test_expired_build_stops_after_one_batch_and_can_be_retired(settings, user, monkeypatch):
    from core_apps.properties.services.saved_search_items import retire_expired_itemized_reads

    settings.SAVED_SEARCH_ITEMIZED_READS = True
    prop = _create_property(owner=user)
    Property.objects.bulk_create(
        [
            Property(
                owner=user,
                title=f"Expiring {index}",
                price=1000,
                property_type=prop.property_type,
                governorate=prop.governorate,
                city=prop.city,
                district="Test",
            )
            for index in range(999)
        ]
    )
    insert = SavedSearchReadItem.objects.bulk_create

    def expire(rows, **kwargs):
        result = insert(rows, **kwargs)
        SavedSearchRead.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        return result

    monkeypatch.setattr(SavedSearchReadItem.objects, "bulk_create", expire)
    with pytest.raises(APIException) as error:
        reads.apply_saved_search_read(Property.objects.all(), request(user))
    assert error.value.status_code == 410
    snapshot = SavedSearchRead.objects.get()
    assert not snapshot.items_ready and snapshot.items.count() == 500
    settings.SAVED_SEARCH_ITEMIZED_READS = False
    assert retire_expired_itemized_reads() == 1
    assert not snapshot.items.exists()
