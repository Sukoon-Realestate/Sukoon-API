"""Estimated daily travel over explicitly shared meeting points, never bookings."""
from datetime import timedelta
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from rest_framework.exceptions import Throttled
from core_apps.common.idempotency import fingerprint, IdempotencyConflict
from core_apps.features.services.planning_providers_parts.route_matrix import route_matrix, provider_budget, DiscoveryUnavailable
from ..models import PropertyVisit
from .viewing_times import instant


def visits_for(actor, day, workspace):
    query = PropertyVisit.objects.filter(status='confirmed', visit_date=day, visit_time__isnull=False,
        context_kind='personal', renter_workspace='individual', company__isnull=True, academic_plan__isnull=True,
        property__retired_at__isnull=True, property__owner__is_active=True, tenant__is_active=True)
    query = query.filter(property__owner=actor) if workspace == 'owner' else query.filter(tenant=actor)
    return query.select_related('property','arrival_card').order_by('visit_time','pk')


def point(visit):
    card = getattr(visit, 'arrival_card', None)
    if not card or not card.active or card.latitude is None or card.longitude is None:
        return None
    return {'latitude':float(card.latitude), 'longitude':float(card.longitude)}


def source_revision(visits):
    return fingerprint([{'visit':str(v.id), 'revision':v.revision,
        'instructions_revision':getattr(getattr(v,'arrival_card',None),'revision',0)} for v in visits])


def estimate(actor, origin, destination, departure, mode, identity):
    unknown = {'duration_seconds':None, 'distance_meters':None, 'unknown_reason':'meeting_point_unavailable'}
    if origin is None or destination is None:
        return unknown
    if not settings.PLANNING_ROUTES_API_KEY:
        return {**unknown,'unknown_reason':'route_provider_unconfigured'}
    query = {'origin':origin, 'destination':destination, 'mode':mode, 'departure_at':departure.isoformat(),
        'source_revision':identity}
    key = 'viewing-day-route:' + fingerprint({'actor':actor.pk, **query})
    found = cache.get(key)
    if found:
        return found
    try:
        provider_budget(actor,'viewing_day_routes')
        row = route_matrix([origin],{'mode':mode,'time_kind':'depart_at','at':departure.isoformat(),
            'location':destination})[0]
        seconds, distance = row.get('duration_seconds'), row.get('distance_meters')
        if row.get('status') != 'ok' or row.get('timing_fallback') or type(seconds) is not int or seconds < 0:
            return {**unknown,'unknown_reason':'route_or_timing_not_confirmed'}
        fetched = timezone.now()
        result = {'duration_seconds':seconds, 'distance_meters':distance,
            'unknown_reason':None, 'fetched_at':fetched.isoformat(),
            'expires_at':(fetched+timedelta(minutes=10)).isoformat(), 'estimated':True}
        cache.set(key,result,timeout=600)
        return result
    except (DiscoveryUnavailable,Throttled,IndexError,KeyError,TypeError):
        return {**unknown,'unknown_reason':'route_provider_unavailable'}


def day_plan(actor, data):
    visits = list(visits_for(actor,data['day'],data['workspace']))
    identity = source_revision(visits)
    origin = {key:float(value) for key,value in data['origin'].items()} if data.get('origin') else None
    departure = data.get('start_at')
    duration = data['viewing_minutes']
    buffer = data['buffer_minutes']
    entries = []
    for visit in visits:
        at = instant(visit.visit_date,visit.visit_time)
        destination = point(visit)
        travel = estimate(actor,origin,destination,departure,data['mode'],identity) if departure else {
            'duration_seconds':None,'distance_meters':None,'unknown_reason':'start_time_unset'}
        arrival = departure+timedelta(seconds=travel['duration_seconds'],minutes=buffer) if departure and travel['duration_seconds'] is not None else None
        conflict = 'travel_conflict' if arrival and arrival > at else (
            'viewing_overlap' if departure and departure > at else
            'travel_unknown' if departure and travel['duration_seconds'] is None else None)
        entries.append({'visit_id':str(visit.id),'visit_revision':visit.revision,'title':visit.property.title,
            'starts_at':at.isoformat(),'estimated_end_at':(at+timedelta(minutes=duration)).isoformat(),
            'travel':travel,'departure_at':departure.isoformat() if departure else None,'conflict':conflict,
            'arrival_card_available':bool(getattr(visit,'arrival_card',None) and visit.arrival_card.active)})
        origin = destination
        departure = at+timedelta(minutes=duration)
    # A long provider response must not resurrect canceled or revised appointments.
    if source_revision(list(visits_for(actor,data['day'],data['workspace']))) != identity:
        raise IdempotencyConflict('The viewing day changed. Refresh its estimates.')
    return {'protocol':1,'day':data['day'].isoformat(),'timezone':'Africa/Cairo','revision':identity,
        'viewing_minutes':duration,'buffer_minutes':buffer,'mode':data['mode'],'estimated':True,'visits':entries}
