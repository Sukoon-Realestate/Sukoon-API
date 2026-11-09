"""A3-01: tour-storage cleanup must keep live portfolio media and still reclaim orphans.

Sprint 00 recorded this as a strict xfail (cleanup_tours never referenced ResidentialMedia
blobs). Sprint 01 adds portfolio media to the single reference graph used for local and
remote sweeping.
"""

import hashlib
import io
import os
import time

import pytest
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile

from core_apps.features.services.company import portfolio_media as media
from core_apps.features.tests.test_company_housing import (  # noqa: F401
    company_setup,
    command,
    rental_participants,
    policy,
)
from core_apps.virtual_tours import storage
from core_apps.virtual_tours.tasks import cleanup_tours


def _photo(owner, building, colour="green"):
    image = io.BytesIO()
    Image.new("RGB", (4, 4), colour).save(image, "PNG")
    raw = image.getvalue()
    intent = media.create_intent(owner, "building", building.id, command(
        expected_revision=building.revision, purpose="photo", caption="Lobby", representative=False,
        sha256=hashlib.sha256(raw).hexdigest(), byte_size=len(raw), content_type="image/png",
    ))
    return intent, raw


def _age(target):
    old = time.time() - 8 * 24 * 3600
    os.utime(target, (old, old))


@pytest.mark.django_db
def test_cleanup_keeps_ready_portfolio_photo_after_retention_threshold(company_setup, settings, tmp_path):  # noqa: F811
    owner, _, _, _, building, *_ = company_setup
    settings.VIRTUAL_TOUR_PRIVATE_ROOT = str(tmp_path)
    image = io.BytesIO()
    Image.new("RGB", (4, 4), "green").save(image, "PNG")
    raw = image.getvalue()
    intent = media.create_intent(owner, "building", building.id, command(
        expected_revision=building.revision, purpose="photo", caption="Lobby", representative=True,
        sha256=hashlib.sha256(raw).hexdigest(), byte_size=len(raw), content_type="image/png",
    ))
    item = media.upload(owner, intent.id, SimpleUploadedFile("lobby.png", raw, content_type="image/png"))
    assert item.state == "ready"
    blob = storage.path(item.blob)
    old = time.time() - 8 * 24 * 3600
    os.utime(blob, (old, old))

    cleanup_tours()

    assert blob.exists(), "a live portfolio photo was deleted by tour-storage cleanup"
    assert storage.read_path(item.blob).read_bytes()


@pytest.mark.django_db
def test_cleanup_keeps_removed_evidence_and_reclaims_true_orphans(company_setup, settings, tmp_path):  # noqa: F811
    owner, _, _, _, building, *_ = company_setup
    settings.VIRTUAL_TOUR_PRIVATE_ROOT = str(tmp_path)
    intent, raw = _photo(owner, building)
    item = media.upload(owner, intent.id, SimpleUploadedFile("a.png", raw, content_type="image/png"))
    item = media.remove(owner, item.id, {"expected_revision": item.revision})
    kept = storage.path(item.blob)
    orphan_key, _, _ = storage.write_blob([b"orphan"], 1024)
    orphan = storage.path(orphan_key)
    for target in (kept, orphan):
        _age(target)

    result = cleanup_tours()

    assert kept.exists(), "removed portfolio media is retained as private evidence"
    assert not orphan.exists()
    assert result["removed_local_files"] == 1


@pytest.mark.django_db
def test_remote_sweep_receives_portfolio_references(company_setup, settings, tmp_path):  # noqa: F811
    from unittest.mock import patch

    owner, _, _, _, building, *_ = company_setup
    settings.VIRTUAL_TOUR_PRIVATE_ROOT = str(tmp_path)
    intent, raw = _photo(owner, building)
    item = media.upload(owner, intent.id, SimpleUploadedFile("a.png", raw, content_type="image/png"))
    with patch("core_apps.virtual_tours.tasks.remote_storage.sweep", return_value=0) as sweep:
        cleanup_tours()
    assert item.blob in sweep.call_args.args[0]


@pytest.mark.django_db
def test_losing_concurrent_upload_does_not_leave_its_local_write(company_setup, settings, tmp_path):  # noqa: F811
    owner, _, _, _, building, *_ = company_setup
    settings.VIRTUAL_TOUR_PRIVATE_ROOT = str(tmp_path)
    intent, raw = _photo(owner, building)
    first = media.upload(owner, intent.id, SimpleUploadedFile("a.png", raw, content_type="image/png"))
    # A second (retried/raced) transmission sees the row already ready.
    second = media.upload(owner, intent.id, SimpleUploadedFile("a.png", raw, content_type="image/png"))
    assert second.blob == first.blob
    assert sorted(p.name for p in tmp_path.iterdir()) == [first.blob]
