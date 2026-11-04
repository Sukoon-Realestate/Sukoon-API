import json
import os
from pathlib import Path
from datetime import timedelta
import pytest
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.urls import reverse
from core_apps.common.models import ContentView
from core_apps.properties.models import Property, PropertyVisit
from core_apps.properties.services.property import PropertyService
from .test_views import _create_published_property

pytestmark = pytest.mark.django_db


def test_funnel_counts_deduplicated_measured_records_and_excludes_owner_and_deferred_contexts(user, another_user):
    prop = _create_published_property(owner=user, price=1000)
    content_type = ContentType.objects.get_for_model(Property)
    now = timezone.now()
    for actor, ip, when in [(user, '127.0.0.1', now), (another_user, '127.0.0.2', now),
            (None, '127.0.0.3', now - timedelta(days=40))]:
        ContentView.objects.create(content_type=content_type, object_id=prop.pk, user=actor,
            viewer_ip=ip, last_viewed=when)
    ContentView.record_view(prop, another_user, '127.0.0.2')
    PropertyVisit.objects.create(property=prop, tenant=another_user)
    PropertyVisit.objects.create(property=prop, tenant=another_user, renter_workspace='student')
    funnel = PropertyService.get_property_statistics(prop, '30_days')['funnel']
    assert [stage['count'] for stage in funnel['stages']] == [1, None, 1]
    assert funnel['rates'] is None
    assert set(funnel['suggestions']) == {'listing_information', 'listing_photos'}
    assert 'user_id' not in json.dumps(funnel)
    exported = os.environ.get('MVP_FIXTURE_DIR')
    if exported:
        path = Path(exported)
        path.mkdir(parents=True, exist_ok=True)
        (path / 'listing_funnel.json').write_text(json.dumps(funnel), encoding='utf8')


def test_owner_preview_does_not_record_interest(api_client, user):
    prop = _create_published_property(owner=user, price=1000)
    api_client.force_authenticate(user)
    assert api_client.get(reverse('property-detail', kwargs={'id': prop.id})).status_code == 200
    assert api_client.get(reverse('owner-draft-review', kwargs={'property_id': prop.id})).status_code == 200
    assert ContentView.objects.count() == 0
    funnel = PropertyService.get_property_statistics(prop, '30_days')['funnel']
    assert [stage['count'] for stage in funnel['stages']] == [0, None, 0]
