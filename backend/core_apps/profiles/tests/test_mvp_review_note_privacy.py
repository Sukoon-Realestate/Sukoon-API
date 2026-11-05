"""The applicant sees the correction reason, never private reviewer notes."""
import pytest
from django.urls import reverse

from core_apps.admin_api.models import KYCSubmission
from .test_identity_corrections import reject_front

pytestmark = pytest.mark.django_db


def test_identity_correction_reason_does_not_disclose_internal_review_notes(auth_client, user, superuser):
    original = reject_front(user, superuser)
    KYCSubmission.objects.filter(id=original['submission_id']).update(notes='Synthetic internal reviewer-only assessment')
    response = auth_client.get(reverse('verification-status'))
    assert response.status_code == 200
    data = response.json()['data']
    assert data['rejection_reason'] == 'Front blurred'
    assert 'Synthetic internal reviewer-only assessment' not in str(data)
    assert 'notes' not in data and 'reviewer' not in data
    assert response['Cache-Control'] == 'private, no-store'
