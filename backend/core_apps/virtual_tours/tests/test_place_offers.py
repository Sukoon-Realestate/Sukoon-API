import copy
import json
import os
import uuid
from pathlib import Path
import pytest
from rest_framework.test import APIClient
from core_apps.properties.models import Property
from core_apps.virtual_tours import sessions
from core_apps.virtual_tours.errors import TourError
from core_apps.virtual_tours.place_offers import binding, validate_link
from core_apps.virtual_tours.policy import scope_policy
from .test_tours import ready_variant

pytestmark = pytest.mark.django_db

@pytest.fixture
def linked(property_obj, user):
    rid, oid = str(uuid.uuid4()), str(uuid.uuid4())
    offer = {'id': oid, 'rental_scope': 'room', 'room_ids': [rid], 'availability': 'available'}
    inventory = {'mode': 'whole', 'rooms': [{'id': rid, 'beds': []}], 'offers': [offer]}
    Property.objects.filter(pk=property_obj.pk).update(rental_inventory=inventory)
    property_obj.refresh_from_db()
    tour, revision, variant = ready_variant(property_obj)
    space = {'id': 'room', 'space_kind': 'room', 'floor_id': 'ground',
             'label': {'en': 'Same name', 'ar': 'Synthetic'},
             'room_id': rid, 'offer_link': binding(offer)}
    variant.manifest.update(spaces=[space], scenes=[{'id': 'scene', 'space_id': 'room'}])
    variant.scope_fingerprint = scope_policy(property_obj, 'overview', [space])
    variant.save()
    opened = sessions.create_session(tour, user, {})
    from core_apps.virtual_tours.models import TourViewerSession
    session = TourViewerSession.objects.get(id=opened['session_id'])
    credential = sessions.exchange(session)['credential']
    client = APIClient()
    client.credentials(HTTP_X_TOUR_CREDENTIAL=credential)
    url = f'/api/v1/virtual-tour-viewer/sessions/{session.id}/places/scene/offer/'
    return client, url, property_obj, session, space, inventory


def test_resolve_current_room_offer_private_and_no_booking(linked):
    client, url, prop, session, space, inventory = linked
    response = client.get(url)
    assert response.status_code == 200
    assert response['Cache-Control'] == 'private, no-store'
    assert response.data['status'] == 'available'
    assert response.data['offer_id'] == inventory['offers'][0]['id']
    assert 'price' not in response.data
    assert client.get(url.replace('/scene/', '/deleted/')).status_code == 404
    assert APIClient().get(url).status_code == 401
    directory = os.environ.get('MVP_FIXTURE_DIR')
    if directory:
        Path(directory, 'tour_offer_destination.json').write_text(json.dumps(response.data), encoding='utf-8')


@pytest.mark.parametrize('change', ['unavailable', 'archived', 'identity'])
def test_offer_changes_do_not_destroy_tour_context(linked, change):
    client, url, prop, session, space, inventory = linked
    if change == 'identity': inventory['offers'][0]['rental_scope'] = 'room_group'
    else: inventory['offers'][0][change if change == 'archived' else 'availability'] = True if change == 'archived' else 'unavailable'
    Property.objects.filter(pk=prop.pk).update(rental_inventory=inventory)
    response = client.get(url)
    assert response.status_code == 200
    assert response.data['status'] == 'unavailable'
    assert 'offer_id' not in response.data
    assert client.get(url.split('places/')[0] + 'manifest/').status_code == 200


def test_shared_foreign_and_incorrect_bed_links_rejected(linked):
    _, _, prop, _, space, _ = linked
    for changes in ({'space_kind': 'shared'}, {'bed_id': str(uuid.uuid4())},
                    {'offer_link': {**space['offer_link'], 'offer_id': str(uuid.uuid4())}}):
        with pytest.raises(TourError): validate_link(prop, {**space, **changes})


def test_revoked_and_superseded_sessions_cannot_resolve(linked):
    client, url, prop, session, _, _ = linked
    from django.utils import timezone
    session.revoked_at = timezone.now()
    session.save()
    assert client.get(url).status_code == 401


def test_preview_is_passive_and_linked_component_never_inferred(linked):
    client, url, _, session, _, _ = linked
    session.preview = True
    session.save()
    assert client.get(url).data['status'] == 'preview'
    session.variant.manifest['scenes'] = [{'id': 'scene', 'space_ids': ['room', 'other']}]
    session.variant.save()
    assert client.get(url).data['status'] == 'shared'
