"""Public historical reading remains available; no new review workflow opens."""
from uuid import uuid4
import pytest
from core_apps.properties.models import PropertyVisit, PropertyVisitReview
from core_apps.features.models import ReviewSection, ReviewSubmission
from core_apps.features.services.reputation.legacy import import_one
from .test_rental_phase2 import authenticated, rental_participants  # noqa: F401

pytestmark = pytest.mark.django_db
API = '/api/v1/features/v1/reviews/'


def test_mvp_reads_original_public_history_without_claiming_verified_scores(rental_participants, api_client, settings):
    settings.REVIEWS_ENABLED = True
    owner, tenant, stranger, prop, _ = rental_participants
    visit = PropertyVisit.objects.create(property=prop, tenant=tenant, status='completed')
    historical = PropertyVisitReview.objects.create(visit=visit, overall_rating=4,
        cleanliness_rating=4, listing_accuracy_rating=4, owner_interaction_rating=4,
        comment='Historical synthetic public opinion')
    assert import_one(historical, 'property_visit_review')
    section = ReviewSection.objects.get()
    detail = api_client.get(API + f'{section.id}/')
    assert detail.status_code == 200
    assert historical.comment in str(detail.json())
    assert 'legacy_unverified' in str(detail.json())
    summary = api_client.get(API + f'subjects/property_visit/{prop.id}/summary/')
    assert summary.status_code == 200 and summary.json()['data']['average'] is None
    original_count = ReviewSubmission.objects.count()
    for actor in [owner, tenant, stranger]:
        response = authenticated(actor).post(API + f'{section.id}/reply/',
            {'request_key': str(uuid4()), 'comment': 'Must not create a reply'}, format='json')
        assert response.status_code == 403
    assert ReviewSubmission.objects.count() == original_count


def test_mvp_capabilities_never_advertise_deferred_review_actions(rental_participants, settings):
    settings.REVIEWS_ENABLED = True
    actor = authenticated(rental_participants[1])
    data = actor.get(API + 'capabilities/').json()['data']
    assert data['enabled'] is True
    assert not any(data['capabilities'].values())
    settings.SUKOON_MVP = False
    assert all(actor.get(API + 'capabilities/').json()['data']['capabilities'].values())
