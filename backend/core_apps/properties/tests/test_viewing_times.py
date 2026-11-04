import uuid
import os
import json
from pathlib import Path
from datetime import time, timedelta
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import pytest
from django.db import connection, connections
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from core_apps.properties.models import PropertyVisit, OwnerAvailabilitySlot, ViewingTimeProposal, AvailabilityClosure
from core_apps.properties.services.viewing_times import instant
from .test_views import _create_published_property

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def arranged(user, another_user):
    assert connection.vendor == 'postgresql', 'Required locking tests must run on isolated PostgreSQL.'
    prop = _create_published_property(owner=user, price=1000)
    day = timezone.localdate() + timedelta(days=7)
    visit = PropertyVisit.objects.create(property=prop, tenant=another_user, status='confirmed',
        visit_date=day, visit_time=time(9))
    for hour in [10, 11, 12]:
        OwnerAvailabilitySlot.objects.create(property=prop, owner=user, date=day, time=time(hour))
    return visit, user, another_user, day


def call(visit, actor, body=None):
    client = APIClient()
    client.force_authenticate(actor)
    path = reverse('viewing-time-proposals', kwargs={'visit_id': visit.id})
    return client.get(path) if body is None else client.post(path, body, format='json')


def propose(visit, actor, slot=0):
    state = call(visit, actor).data
    response = call(visit, actor, {'request_key': str(uuid.uuid4()), 'action': 'propose',
        'expected_visit_revision': state['visit_revision'], 'availability_revision': state['availability_revision'],
        'slot_ids': [state['slots'][slot]['id']]})
    assert response.status_code == 200, response.data
    return response.data['proposals'][0]


def accept_body(proposal):
    return {'request_key': str(uuid.uuid4()), 'action': 'accept', 'proposal_id': proposal['id'],
        'expected_proposal_revision': proposal['revision'], 'slot_id': proposal['choices'][0]['id']}


def test_acceptance_is_atomic_idempotent_and_changes_visit_revision(arranged):
    visit, owner, renter, day = arranged
    original = visit.revision
    proposal = propose(visit, owner)
    if os.environ.get('MVP_FIXTURE_DIR'):
        path = Path(os.environ['MVP_FIXTURE_DIR'])
        path.mkdir(parents=True, exist_ok=True)
        (path / 'viewing_times.json').write_text(json.dumps(call(visit, renter).data), encoding='utf8')
    visit.refresh_from_db()
    assert visit.visit_time == time(9)
    assert call(visit, owner, accept_body(proposal)).status_code == 403
    body = accept_body(proposal)
    accepted = call(visit, renter, body)
    assert accepted.status_code == 200, accepted.data
    assert call(visit, renter, body).data == accepted.data
    visit.refresh_from_db()
    assert visit.visit_time == time(10) and visit.revision == original + 1
    assert len([h for h in visit.change_history if 'visit_time' in h['changed_fields']]) == 1


def test_expired_closed_and_stale_proposals_keep_original_appointment(arranged):
    visit, owner, renter, day = arranged
    proposal = propose(visit, owner)
    ViewingTimeProposal.objects.filter(id=proposal['id']).update(expires_at=timezone.now()-timedelta(seconds=1))
    assert call(visit, renter, accept_body(proposal)).status_code == 409
    proposal = propose(visit, owner, 1)
    AvailabilityClosure.objects.create(property=visit.property, starts_at=instant(day,time(11)),
        ends_at=instant(day,time(12)))
    assert call(visit, renter, accept_body(proposal)).status_code == 409
    visit.refresh_from_db()
    assert visit.visit_time == time(9)


def parallel(*commands):
    barrier = Barrier(len(commands))
    def run(command):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET lock_timeout = '10s'")
            barrier.wait(timeout=15)
            return command()
        finally:
            connections.close_all()
    with ThreadPoolExecutor(max_workers=len(commands)) as pool:
        futures = [pool.submit(run, command) for command in commands]
        return [future.result(timeout=35) for future in futures]


def test_competing_alternatives_accept_exactly_one_and_supersede_the_other(arranged):
    visit, owner, renter, day = arranged
    first, second = propose(visit, owner), propose(visit, owner, 1)
    results = parallel(lambda: call(visit, renter, accept_body(first)), lambda: call(visit, renter, accept_body(second)))
    assert sorted(r.status_code for r in results) == [200,409]
    assert ViewingTimeProposal.objects.filter(visit=visit, state='accepted').count() == 1
    assert ViewingTimeProposal.objects.filter(visit=visit, state='superseded').count() == 1


def test_same_owner_two_properties_cannot_accept_the_same_time(arranged, superuser):
    visit, owner, renter, day = arranged
    other_prop = _create_published_property(owner=owner, price=2000)
    other_visit = PropertyVisit.objects.create(property=other_prop, tenant=superuser, status='confirmed',
        visit_date=day, visit_time=time(8))
    OwnerAvailabilitySlot.objects.create(property=other_prop, owner=owner, date=day, time=time(10))
    first, second = propose(visit, owner), propose(other_visit, owner)
    results = parallel(lambda: call(visit, renter, accept_body(first)), lambda: call(other_visit, superuser, accept_body(second)))
    assert sorted(r.status_code for r in results) == [200,409]
    assert PropertyVisit.objects.filter(property__owner=owner, visit_date=day, visit_time=time(10)).count() == 1


def test_closure_and_acceptance_race_preserves_the_winning_revision(arranged):
    visit, owner, renter, day = arranged
    proposal = propose(visit, owner)
    client = APIClient()
    client.force_authenticate(owner)
    path = reverse('availability-closures', kwargs={'property_id': visit.property.id})
    values = {'starts_at': instant(day,time(10)).isoformat(), 'ends_at': instant(day,time(11)).isoformat(), 'timezone':'Africa/Cairo'}
    preview = client.post(path, values, format='json').data
    def close():
        other = APIClient()
        other.force_authenticate(owner)
        return other.put(path, {**values, 'revision':preview['revision'], 'decisions':{}},
            format='json', HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
    results = parallel(close, lambda: call(visit,renter,accept_body(proposal)))
    assert sorted(r.status_code for r in results) == [200,409]
    visit.refresh_from_db()
    if results[0].status_code == 200:
        assert visit.visit_time == time(9)
    else:
        assert visit.visit_time == time(10)
        assert not AvailabilityClosure.objects.filter(property=visit.property,active=True).exists()


def test_only_current_parties_in_individual_context_can_propose_up_to_three(arranged, superuser):
    visit, owner, renter, day = arranged
    assert call(visit, superuser).status_code == 403
    state = call(visit, owner).data
    response = call(visit, owner, {'request_key':str(uuid.uuid4()), 'action':'propose',
        'expected_visit_revision':state['visit_revision'], 'availability_revision':state['availability_revision'],
        'slot_ids':[state['slots'][0]['id']] * 4})
    assert response.status_code == 400
    assert not visit.time_proposals.exists()
    PropertyVisit.objects.filter(pk=visit.pk).update(renter_workspace='student')
    assert call(visit, owner).status_code == 403
    assert call(visit, renter).status_code == 403
