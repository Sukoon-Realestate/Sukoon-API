"""A3-01 failing-before case: tour-storage cleanup must keep live portfolio media.

cleanup_tours() builds its reference set from tour, capture, variant and upload records only;
ResidentialMedia blobs live in the same private storage but are never referenced, so a ready
portfolio photo older than seven days is deleted. Strict xfail: Sprint 01 must make this pass.
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


@pytest.mark.django_db
@pytest.mark.xfail(strict=True, reason="A3-01: cleanup_tours does not reference ResidentialMedia blobs (Sprint 01)")
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
