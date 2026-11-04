import uuid
import json
import os
from pathlib import Path
from datetime import time,timedelta
import pytest
from django.urls import reverse
from django.utils import timezone
from core_apps.properties.models import PropertyVisit,ViewingArrival
from core_apps.features.planning_models import PlanningEvent
from .test_views import _create_published_property

pytestmark=pytest.mark.django_db


@pytest.fixture
def appointments(user,another_user):
    day=timezone.localdate()+timedelta(days=7)
    visits=[]
    for hour,minute in [(10,0),(10,40)]:
        prop=_create_published_property(owner=user,price=1000)
        visits.append(PropertyVisit.objects.create(property=prop,tenant=another_user,status='confirmed',
            visit_date=day,visit_time=time(hour,minute)))
    return visits,day


def directions(visit,**changes):
    return {'request_key':str(uuid.uuid4()),'expected_revision':0,'expected_visit_revision':visit.revision,
        'active':True,'meeting_point':'Synthetic meeting point','entrance':'Fixture entrance',
        'instructions':'PRIVATE_FIXTURE_DIRECTIONS','latitude':'30.1000000','longitude':'31.2000000',**changes}


def test_arrival_permissions_revision_idempotency_withdrawal_and_cancellation(api_client,user,another_user,superuser,appointments):
    visits,day=appointments
    visit=visits[0]
    path=reverse('viewing-arrival',kwargs={'visit_id':visit.id})
    api_client.force_authenticate(user)
    body=directions(visit)
    response=api_client.post(path,body,format='json')
    assert response.status_code==200,response.data
    exported=os.environ.get('MVP_FIXTURE_DIR')
    if exported:
        root=Path(exported);root.mkdir(parents=True,exist_ok=True)
        (root/'viewing_arrival_owner.json').write_text(json.dumps(response.data),encoding='utf8')
    assert api_client.post(path,body,format='json').data==response.data
    assert ViewingArrival.objects.count()==1
    assert PlanningEvent.objects.count()==1
    assert 'PRIVATE_FIXTURE_DIRECTIONS' not in json.dumps(list(PlanningEvent.objects.values_list('destination',flat=True)))
    assert api_client.post(path,directions(visit),format='json').status_code==409
    api_client.force_authenticate(another_user)
    assert api_client.get(path).data['card']['instructions']=='PRIVATE_FIXTURE_DIRECTIONS'
    if exported:
        (root/'viewing_arrival_renter.json').write_text(json.dumps(api_client.get(path).data),encoding='utf8')
    assert api_client.post(path,directions(visit),format='json').status_code==403
    api_client.force_authenticate(superuser)
    assert api_client.get(path).status_code==403
    api_client.force_authenticate(user)
    assert api_client.post(path,directions(visit,active=False,expected_revision=1),format='json').status_code==200
    api_client.force_authenticate(another_user)
    assert api_client.get(path).data['card'] is None
    visit.status='canceled'
    visit.save(update_fields=['status','updated_at'])
    assert api_client.get(path).status_code==404


def test_day_plan_uses_authorized_points_and_revision_scoped_estimates(api_client,user,another_user,appointments,settings,monkeypatch):
    visits,day=appointments
    for i,visit in enumerate(visits):
        ViewingArrival.objects.create(visit=visit,meeting_point='Fixture',latitude=30+i/10,longitude=31+i/10)
    settings.PLANNING_ROUTES_API_KEY='isolated-provider-fixture'
    calls=[]
    def provider(origins,destination):
        calls.append((origins,destination))
        return [{'status':'ok','duration_seconds':900,'distance_meters':5000}]
    monkeypatch.setattr('core_apps.properties.services.viewing_day_plan.route_matrix',provider)
    api_client.force_authenticate(another_user)
    path=reverse('viewing-day-plan')
    body={'day':day.isoformat(),'workspace':'individual','viewing_minutes':30,'buffer_minutes':10,'mode':'driving'}
    response=api_client.post(path,body,format='json')
    assert response.status_code==200,response.data
    rows=response.data['visits']
    assert rows[0]['travel']['duration_seconds'] is None
    assert rows[1]['travel']['duration_seconds']==900 and rows[1]['conflict']=='travel_conflict'
    assert len(calls)==1
    assert 'latitude' not in json.dumps(response.data)
    assert api_client.post(path,body,format='json').status_code==200
    assert len(calls)==1
    visits[0].visit_time=time(10,10)
    visits[0].save(update_fields=['visit_time','updated_at'])
    newer=api_client.post(path,body,format='json')
    assert newer.data['revision']!=response.data['revision']
    assert len(calls)==2
    visits[0].refresh_from_db()
    assert visits[0].visit_time==time(10,10)
    exported=os.environ.get('MVP_FIXTURE_DIR')
    if exported:
        root=Path(exported);root.mkdir(parents=True,exist_ok=True)
        (root/'viewing_day_plan.json').write_text(json.dumps(newer.data),encoding='utf8')


def test_day_plan_never_uses_revoked_points_and_remains_available_without_routes(api_client,another_user,appointments,monkeypatch):
    visits,day=appointments
    ViewingArrival.objects.create(visit=visits[0],active=False,latitude=30,longitude=31,meeting_point='Revoked')
    def forbidden(*args,**kwargs):
        raise AssertionError('An unshared point must not reach a route provider')
    monkeypatch.setattr('core_apps.properties.services.viewing_day_plan.route_matrix',forbidden)
    api_client.force_authenticate(another_user)
    response=api_client.post(reverse('viewing-day-plan'),{'day':day.isoformat(),'workspace':'individual'},format='json')
    assert response.status_code==200
    assert len(response.data['visits'])==2
    assert all(row['travel']['duration_seconds'] is None for row in response.data['visits'])


def test_changed_appointment_during_provider_read_discards_obsolete_plan(api_client,another_user,appointments,settings,monkeypatch):
    visits,day=appointments
    for visit in visits:
        ViewingArrival.objects.create(visit=visit,meeting_point='Fixture',latitude=30,longitude=31)
    settings.PLANNING_ROUTES_API_KEY='isolated-fixture'
    def provider(*args,**kwargs):
        visits[0].status='canceled'
        visits[0].save(update_fields=['status','updated_at'])
        return [{'status':'ok','duration_seconds':600,'distance_meters':2000}]
    monkeypatch.setattr('core_apps.properties.services.viewing_day_plan.route_matrix',provider)
    api_client.force_authenticate(another_user)
    response=api_client.post(reverse('viewing-day-plan'),{'day':day.isoformat(),'workspace':'individual'},format='json')
    assert response.status_code==409
    response=api_client.post(reverse('viewing-day-plan'),{'day':day.isoformat(),'workspace':'individual',
        'origin':{'latitude':30,'longitude':31},'start_at':f'{day.isoformat()}T08:00:00'},format='json')
    assert response.status_code==400
