"""Owner correction text is explicit, revision-bound and separate from staff notes."""
import json
import os
from pathlib import Path
from uuid import uuid4

import pytest

from core_apps.virtual_tours import notifications, services
from core_apps.virtual_tours.errors import TourError
from core_apps.virtual_tours.models import TourReviewEvent
from .test_tours import ready_variant

pytestmark = pytest.mark.django_db
PUBLIC = 'Correct the bedroom panorama / صحح صورة الغرفة'
PRIVATE = 'Private staff investigation detail'


def test_public_correction_validation_is_localized_without_translating_staff_notes():
    from core_apps.common.translation import translate_message
    message = 'Provide a correction reason visible to the owner when rejecting a tour.'
    assert translate_message(message, 'en') == message
    assert translate_message(message, 'ar') == 'اكتب سبب التصحيح الذي سيظهر للمالك عند رفض الجولة.'


@pytest.mark.parametrize('public_reason', ['', '   ', None, {}, 'x' * 2001])
def test_new_tour_rejection_requires_explicit_owner_visible_reason(property_obj, superuser, public_reason):
    _, revision, _ = ready_variant(property_obj)
    revision.review_state = 'pending'
    revision.save(update_fields=['review_state'])
    with pytest.raises(TourError):
        services.review(revision, superuser, {'decision': 'rejected',
            'expected_source_hash': revision.source_hash, 'reason': PRIVATE, 'public_reason': public_reason})
    revision.refresh_from_db()
    assert revision.review_state == 'pending' and not revision.reviews.exists()


def test_owner_gets_only_current_public_correction_and_retry_keeps_one_review(
    property_obj, superuser, auth_client, another_user,
):
    tour, revision, _ = ready_variant(property_obj)
    revision.review_state = 'pending'
    revision.save(update_fields=['review_state'])
    path = f'/api/v1/admin/properties/{property_obj.id}/virtual-tours/{tour.id}/revisions/{revision.id}/review-decisions/'
    key = str(uuid4())
    body = {'decision': 'rejected', 'expected_source_hash': revision.source_hash,
            'reason': PRIVATE, 'public_reason': PUBLIC}
    auth_client.force_authenticate(superuser)
    first = auth_client.post(path, body, format='json', HTTP_IDEMPOTENCY_KEY=key)
    assert first.status_code == 200, first.data
    assert auth_client.post(path, body, format='json', HTTP_IDEMPOTENCY_KEY=key).status_code == 200
    assert revision.reviews.count() == 1
    changed = auth_client.post(path, {**body, 'public_reason': 'changed correction'},
        format='json', HTTP_IDEMPOTENCY_KEY=key)
    assert changed.status_code == 409
    revision.refresh_from_db()
    event = notifications.record_tour(revision, 'rejected')
    auth_client.force_authenticate(property_obj.owner)
    owner_path = f'/api/v1/virtual-tour-updates/{event.id}/'
    response = auth_client.get(owner_path)
    assert response.status_code == 200, response.data
    assert response.data['revision']['review_reason'] == PUBLIC
    assert PRIVATE not in str(response.data)
    auth_client.force_authenticate(another_user)
    assert auth_client.get(owner_path).status_code == 404
    if destination := os.environ.get('MVP_FIXTURE_DIR'):
        Path(destination, 'tour_correction_reason.json').write_text(json.dumps(response.json()['data']), encoding='utf-8')


def test_legacy_private_rejection_and_other_source_hash_never_become_public(property_obj, superuser):
    _, revision, _ = ready_variant(property_obj)
    revision.review_state = 'rejected'
    revision.save(update_fields=['review_state'])
    TourReviewEvent.objects.create(revision=revision, reviewer=superuser,
        decision='rejected', source_hash=revision.source_hash, reason=PRIVATE)
    assert services.revision_payload(revision)['review_reason'] == ''
    TourReviewEvent.objects.create(revision=revision, reviewer=superuser,
        decision='rejected', source_hash='another-source', reason=PRIVATE, public_reason=PUBLIC)
    assert services.revision_payload(revision)['review_reason'] == ''
    revision.review_state = 'not_submitted'
    assert services.revision_payload(revision)['review_reason'] == ''


def test_existing_django_review_console_keeps_public_and_private_reasons_separate(
    property_obj, superuser, client, settings,
):
    settings.STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
    _, revision, _ = ready_variant(property_obj)
    revision.review_state = 'pending'
    revision.save(update_fields=['review_state'])
    client.force_login(superuser)
    path = f'/admin/virtual_tours/tourrevision/{revision.pk}/review/'
    missing = client.post(path, {'decision': 'rejected', 'source_hash': revision.source_hash, 'reason': PRIVATE})
    assert missing.status_code == 200 and not revision.reviews.exists()
    response = client.post(path, {'decision': 'rejected', 'source_hash': revision.source_hash,
        'reason': PRIVATE, 'public_reason': PUBLIC})
    assert response.status_code == 302
    event = revision.reviews.get()
    assert event.reason == PRIVATE and event.public_reason == PUBLIC
