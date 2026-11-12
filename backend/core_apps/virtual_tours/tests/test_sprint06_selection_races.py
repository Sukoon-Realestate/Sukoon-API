"""Capture selection remains a fenced, recoverable draft command on PostgreSQL."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from threading import Barrier

import pytest
from django.db import connection, close_old_connections
from rest_framework.test import APIClient
from core_apps.virtual_tours.models import TourRevision, TourOperation
from .test_capture_delivery import selected_job as selected_job


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "mode", ["same_receipt", "same_selection", "competing_selection"]
)
def test_selection_races_keep_one_immutable_draft(request, user, mode):
    if connection.vendor != "postgresql":
        pytest.skip("Capture selection races require PostgreSQL row locks")
    job, document = request.getfixturevalue("selected_job")
    barrier = Barrier(2)
    path = f"/api/v1/property-captures/{job.manifest.session.id}/processing-jobs/{job.id}/select-outputs/"

    def submit(index):
        close_old_connections()
        try:
            client = APIClient()
            client.force_authenticate(user)
            selection = deepcopy(document)
            if mode == "competing_selection":
                selection["title"]["en"] = f"Synthetic competing selection {index}"
            key = (
                "sprint06-selection-same"
                if mode == "same_receipt"
                else f"sprint06-selection-{index}"
            )
            barrier.wait(timeout=10)
            response = client.post(
                path,
                {"authoring": selection, "expectedManifestHash": job.manifest.sha256},
                format="json",
                HTTP_IDEMPOTENCY_KEY=key,
            )
            return response.status_code
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        codes = sorted(pool.map(submit, range(2)))
    assert (
        codes
        == {
            "same_receipt": [202, 202],
            "same_selection": [200, 202],
            "competing_selection": [202, 409],
        }[mode]
    )
    assert TourRevision.objects.count() == 1
    revision = TourRevision.objects.get()
    assert revision.capture_job_id == job.pk
    assert revision.processing_state == "queued"
    assert revision.tour.active_revision_id is None
    assert TourOperation.objects.count() == (2 if mode == "same_selection" else 1)
