"""Retry one failed output without rebuilding a successful sibling output."""
from copy import deepcopy
from unittest.mock import patch
from uuid import uuid4

import pytest

from core_apps.virtual_tours import capture_reconstruction, capture_worker
from core_apps.virtual_tours.capture_models import CaptureProcessingJob
from .test_owner_updates import capture_job

pytestmark = pytest.mark.django_db


def prepared(property_obj, user):
    job = capture_job(property_obj, user)
    job.state, job.attempt = 'needs_capture', 1
    job.outputs = {'panorama360': {'status': 'ready', 'stations': []},
                   'walkthrough3d': {'status': 'needsProcessing', 'code': 'GPU_RUNTIME_NOT_CONFIGURED'}}
    job.save()
    path = f'/api/v1/property-captures/{job.manifest.session.id}/processing-jobs/{job.id}/retry/'
    body = {'expectedAttempt': 1, 'expectedManifestHash': job.manifest.sha256}
    return job, path, body


def test_capture_retry_preserves_success_and_links_exact_original_without_duplicate(
    property_obj, user, auth_client, settings,
):
    settings.PROPERTY_CAPTURE_ENABLED = settings.CAPTURE_RECONSTRUCTION_ENABLED = True
    original, path, body = prepared(property_obj, user)
    original_outputs = deepcopy(original.outputs)
    key = str(uuid4())
    with patch.object(capture_reconstruction, 'runtime_status', return_value={'available': True}):
        first = auth_client.post(path, body, format='json', HTTP_IDEMPOTENCY_KEY=key)
        assert first.status_code == 202, first.data
        replay = auth_client.post(path, body, format='json', HTTP_IDEMPOTENCY_KEY=key)
        assert replay.status_code == 202 and replay.data['id'] == first.data['id']
        # A second operation resolving the same original also finds its existing child.
        recovered = auth_client.post(path, body, format='json', HTTP_IDEMPOTENCY_KEY=str(uuid4()))
        assert recovered.status_code == 200 and recovered.data['id'] == first.data['id']
    child = CaptureProcessingJob.objects.get(id=first.data['id'])
    assert child.retry_of_id == original.pk and child.manifest_id == original.manifest_id
    assert child.outputs['panorama360'] == original_outputs['panorama360']
    assert child.outputs['walkthrough3d'] == {'status': 'pending'}
    assert CaptureProcessingJob.objects.count() == 2
    claimed = capture_worker.claim()
    assert claimed.id == child.id
    with patch.object(capture_worker.capture_panorama, 'process') as panorama, patch.object(
        capture_reconstruction, 'process', return_value=original_outputs['walkthrough3d'],
    ) as reconstruction:
        capture_worker.run(claimed)
        panorama.assert_not_called()
        reconstruction.assert_called_once()
    original.refresh_from_db()
    child.refresh_from_db()
    assert original.outputs == original_outputs
    assert child.outputs['panorama360'] == original_outputs['panorama360']
    assert child.outputs['walkthrough3d']['status'] == 'needsProcessing'


def test_unavailable_reconstruction_retry_keeps_original_outputs_and_creates_nothing(
    property_obj, user, auth_client, settings,
):
    settings.PROPERTY_CAPTURE_ENABLED = settings.CAPTURE_RECONSTRUCTION_ENABLED = True
    original, path, body = prepared(property_obj, user)
    before = deepcopy(original.outputs)
    with patch.object(capture_reconstruction, 'runtime_status', return_value={'available': False}):
        response = auth_client.post(path, body, format='json', HTTP_IDEMPOTENCY_KEY=str(uuid4()))
    assert response.status_code == 409
    original.refresh_from_db()
    assert original.outputs == before
    assert CaptureProcessingJob.objects.count() == 1
