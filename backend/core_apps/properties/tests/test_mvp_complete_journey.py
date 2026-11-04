"""One isolated owner/individual journey across real authenticated HTTP APIs."""
from datetime import timedelta
from uuid import uuid4
import json
import os
from pathlib import Path

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from core_apps.chat.models import Conversation, Message
from core_apps.chat.tests.conftest import message_request
from core_apps.features.models import Lease, TenancyInvitation
from core_apps.properties.models import Property, PropertyVisit, OwnerAvailabilitySlot
from .test_rental_inventory import _room_offer_payload
from .viewing_support import response_body

pytestmark = pytest.mark.django_db


def login(person, password):
    client = APIClient()
    rejected = client.post(reverse('login'), {'email': person.email, 'password': 'incorrect'}, format='json')
    assert rejected.status_code == 401
    assert 'access_token' not in client.cookies
    response = client.post(reverse('login'), {'email': person.email, 'password': password}, format='json')
    assert response.status_code == 200, response.data
    client.credentials(HTTP_AUTHORIZATION='Bearer ' + response.data['access'])
    return client


def test_owner_to_individual_viewing_and_direct_chat_is_one_scoped_journey(
    user, another_user, superuser, cairo_city, cairo_governorate,
):
    # Verification is synthetic accepted setup; no identity provider is contacted.
    for person in (user, another_user):
        person.is_verified = True
        person.save(update_fields=['is_verified'])
    owner = login(user, 'Testpass123!')
    renter = login(another_user, 'Testpass123!')
    guest = APIClient()
    create_key = str(uuid4())
    submitted = owner.post(reverse('property-create'), {
        'title': 'Synthetic complete MVP journey',
        'city': str(cairo_city.id), 'governorate': str(cairo_governorate.id),
        'property_type': 'apartment', 'rental_inventory': _room_offer_payload(),
    }, format='json', HTTP_IDEMPOTENCY_KEY=create_key, HTTP_X_RENTAL_OFFERS_VERSION='1')
    assert submitted.status_code == 201, submitted.data
    prop = Property.objects.get(id=submitted.data['id'])
    assert guest.get(reverse('property-detail', kwargs={'id': prop.id})).status_code == 404
    staff = APIClient()
    staff.force_authenticate(superuser)
    review = staff.get(reverse('admin-property-detail', kwargs={'property_id': prop.id}))
    assert review.status_code == 200, review.data
    approved = staff.post(reverse('admin-property-approve', kwargs={'property_id': prop.id}),
        {'expected_version': review.data['review_version']}, format='json', HTTP_IDEMPOTENCY_KEY=str(uuid4()))
    assert approved.status_code == 200, approved.data
    results = renter.get(reverse('property-list'), {'search': prop.title})
    assert results.status_code == 200, results.data
    assert str(prop.id) in {str(row['id']) for row in results.data['results']}
    detail = renter.get(reverse('property-detail', kwargs={'id': prop.id}))
    assert detail.status_code == 200
    offer = detail.data['rental_inventory']['offers'][0]
    assert offer['terms']['price'] == '5000.00' and offer['rental_scope'] == 'room'

    day = timezone.localdate() + timedelta(days=7)
    week = day - timedelta(days=day.weekday())
    availability_path = f'/api/v1/properties/owner/properties/{prop.id}/availability/'
    weekly = {'week_start': str(week), 'slots': [{'weekday': day.isoweekday(), 'time': '13:00'}]}
    preview = owner.post(availability_path, weekly, format='json')
    assert preview.status_code == 200 and not OwnerAvailabilitySlot.objects.exists()
    applied = owner.put(availability_path, {**weekly, 'revision': preview.data['revision']}, format='json')
    assert applied.status_code == 200
    booking_path = reverse('property-visit-create', kwargs={'property_id': prop.id})
    booking = {'visit_date': str(day), 'visit_time': '13:00:00', 'offer_id': offer['id'],
               'expected_offer_revision': offer['revision'], 'note': 'Synthetic viewing'}
    assert guest.post(booking_path, booking, format='json').status_code == 401
    booking_key = str(uuid4())
    booked = renter.post(booking_path, booking, format='json', HTTP_IDEMPOTENCY_KEY=booking_key)
    assert booked.status_code == 201, booked.data
    visit = PropertyVisit.objects.get()
    original = visit.offer_snapshot.copy()
    assert visit.offer_id == offer['id'] and visit.status == 'pending'
    receipt = renter.get(reverse('viewing-creation-receipt'), {'request_key': booking_key})
    assert receipt.status_code == 200 and receipt.data['visit']['id'] == str(visit.id)
    accepted = owner.post(reverse('owner-visit-request-accept', kwargs={'id': visit.id}),
                          response_body(visit.revision), format='json')
    assert accepted.status_code == 200, accepted.data
    visit.refresh_from_db()
    assert visit.status == 'confirmed' and visit.offer_snapshot == original
    # Existing requests start without an appointment. A separate two-party
    # proposal establishes the time; neither request nor acceptance invents one.
    assert visit.visit_date is None and visit.visit_time is None
    times_path = reverse('viewing-time-proposals', kwargs={'visit_id': visit.id})
    times = owner.get(times_path)
    assert times.status_code == 200 and times.data['can_propose']
    proposed = owner.post(times_path, {
        'request_key': str(uuid4()), 'action': 'propose',
        'expected_visit_revision': times.data['visit_revision'],
        'availability_revision': times.data['availability_revision'],
        'slot_ids': [times.data['slots'][0]['id']],
    }, format='json')
    assert proposed.status_code == 200, proposed.data
    visit.refresh_from_db()
    assert visit.visit_date is None
    proposal = proposed.data['proposals'][0]
    scheduled = renter.post(times_path, {
        'request_key': str(uuid4()), 'action': 'accept', 'proposal_id': proposal['id'],
        'expected_proposal_revision': proposal['revision'],
        'slot_id': proposal['choices'][0]['id'],
    }, format='json')
    assert scheduled.status_code == 200, scheduled.data
    visit.refresh_from_db()
    assert visit.visit_date == day and visit.visit_time.strftime('%H:%M') == '13:00'
    assert visit.offer_snapshot == original

    chat = renter.post(reverse('conversation-create'), {
        'user_id': str(user.id), 'workspace': 'individual',
        'expected_visit_revision': visit.revision,
        'rental_context': {'property_id': str(prop.id), 'visit_id': str(visit.id)},
    }, format='json')
    assert chat.status_code == 200, chat.data
    conversation = Conversation.objects.get()
    assert Message.objects.count() == 0
    messages_path = f'/api/v1/chat/conversations/{conversation.id}/messages/create/'
    question = message_request('Is there a lift for this room?')
    first = renter.post(messages_path, question, format='json')
    assert first.status_code == 201, first.data
    replay = renter.post(messages_path, question, format='json')
    assert replay.status_code == 201 and replay.data['id'] == first.data['id']
    reply = owner.post(messages_path, message_request('Yes, meet at the entrance.'), format='json')
    assert reply.status_code == 201, reply.data
    assert Message.objects.count() == 2
    assert not Lease.objects.exists() and not TenancyInvitation.objects.exists()
    assert renter.post(reverse('post-visit-decision', kwargs={'id': visit.id}), {}, format='json').status_code == 403
    if root := os.environ.get('MVP_FIXTURE_DIR'):
        summary = renter.get(f'/api/v1/chat/conversations/{conversation.id}/chat/')
        current = renter.get(reverse('tenant-visit-request-detail', kwargs={'id': visit.id}))
        assert summary.status_code == current.status_code == 200
        owner_detail = owner.get(reverse('owner-visit-request-detail', kwargs={'id': visit.id}))
        for response in [current, owner_detail]:
            assert response.status_code == 200
            assert response.data['visit_date'] == day.isoformat()
            assert response.data['visit_time'] == '13:00:00'
            assert response.data['day_label'] and response.data['time_label']
        bundle = {'source': 'isolated_postgresql_complete_mvp_journey',
                  'property_id': str(prop.id), 'offer_id': offer['id'],
                  'visit_id': str(visit.id), 'conversation_id': str(conversation.id),
                  'visit': current.json()['data'], 'owner_visit': owner_detail.json()['data'], 'chat': summary.json()['data'],
                  'question': first.json()['data'], 'reply': reply.json()['data']}
        Path(root, 'mvp-complete-journey.json').write_text(json.dumps(bundle), encoding='utf8')
