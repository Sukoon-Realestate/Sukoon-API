import uuid
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from core_apps.properties.models import AvailabilityClosure, PropertyVisit, OwnerAvailabilitySlot
from core_apps.properties.services.availability_closures import parse_range, slot_in_closure
from .test_ux_convenience import availability

pytestmark = pytest.mark.django_db


def values(day):
    zone = ZoneInfo('Africa/Cairo')
    return {'starts_at': datetime.combine(day, time(11), tzinfo=zone).isoformat(),
        'ends_at': datetime.combine(day, time(15), tzinfo=zone).isoformat(), 'timezone': 'Africa/Cairo'}


def test_closure_is_passive_until_commit_preserves_appointments_and_replays(availability, another_user):
    client, prop, day, weekly, weekly_path = availability
    path = reverse('availability-closures', kwargs={'property_id': prop.id})
    visit = PropertyVisit.objects.create(property=prop, tenant=another_user, status='confirmed',
        visit_date=day, visit_time=time(12))
    preview = client.post(path, values(day), format='json')
    assert preview.status_code == 200
    assert not AvailabilityClosure.objects.exists()
    body = {**values(day), 'revision': preview.data['revision']}
    key = str(uuid.uuid4())
    assert client.put(path, body, format='json', HTTP_IDEMPOTENCY_KEY=key).status_code == 400
    body['decisions'] = {str(visit.id): 'keep'}
    committed = client.put(path, body, format='json', HTTP_IDEMPOTENCY_KEY=key)
    assert committed.status_code == 200
    assert client.put(path, body, format='json', HTTP_IDEMPOTENCY_KEY=key).data == committed.data
    assert AvailabilityClosure.objects.count() == 1
    visit.refresh_from_db()
    assert visit.status == 'confirmed' and visit.visit_time == time(12)
    assert slot_in_closure(prop, day, time(14))
    slots = client.post(weekly_path, weekly, format='json').data['slots']
    assert [v['status'] for v in slots] == ['busy', 'closed']
    assert client.put(weekly_path, {**weekly, 'revision': client.post(weekly_path, weekly, format='json').data['revision']}, format='json').status_code == 200
    assert not OwnerAvailabilitySlot.objects.exists()
    row = AvailabilityClosure.objects.get()
    remove = {'action': 'remove', 'closure_id': str(row.id), 'expected_revision': 1}
    # POST always previews and cannot remove a closure.
    assert client.post(path, remove, format='json').status_code == 400
    assert client.put(path, remove, format='json', HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4())).status_code == 200
    assert not slot_in_closure(prop, day, time(14))
    assert not OwnerAvailabilitySlot.objects.exists()


def test_new_booking_invalidates_closure_preview_and_other_owner_cannot_read(availability, another_user):
    client, prop, day, _, _ = availability
    path = reverse('availability-closures', kwargs={'property_id': prop.id})
    preview = client.post(path, values(day), format='json').data
    PropertyVisit.objects.create(property=prop, tenant=another_user, status='confirmed', visit_date=day, visit_time=time(14))
    response = client.put(path, {**values(day), 'revision': preview['revision'], 'decisions': {}},
        format='json', HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
    assert response.status_code == 409
    assert not AvailabilityClosure.objects.exists()
    client.force_authenticate(another_user)
    assert client.get(path).status_code == 404


def test_cairo_dst_offsets_and_nonexistent_slots(monkeypatch):
    monkeypatch.setattr(timezone, 'now', lambda: datetime(2026, 1, 1, tzinfo=ZoneInfo('UTC')))
    for offset in ['+02:00', '+03:00']:
        data = {'starts_at': f'2026-04-24T00:30:00{offset}',
            'ends_at': '2026-04-24T02:00:00+03:00', 'timezone': 'Africa/Cairo'}
        with pytest.raises(ValidationError):
            parse_range(data)
    start, end, zone = parse_range({'starts_at': '2026-04-24T01:00:00+03:00',
        'ends_at': '2026-04-24T02:00:00+03:00', 'timezone': 'Africa/Cairo'})
    assert start.astimezone(zone).date().isoformat() == '2026-04-24'
