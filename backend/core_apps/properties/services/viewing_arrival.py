"""Arrival directions stay private to the current confirmed viewing parties."""
from rest_framework.exceptions import NotFound


def arrival_payload(visit, actor):
    owner = visit.property.owner_id == actor.pk
    if not owner and visit.status != 'confirmed':
        raise NotFound('Arrival instructions are no longer available.')
    row = getattr(visit, 'arrival_card', None)
    visible = row is not None and (owner or row.active)
    return {'protocol': 1, 'visit_id': str(visit.id), 'visit_revision': visit.revision,
        'can_edit': owner and visit.status == 'confirmed', 'revision': row.revision if visible else 0,
        'card': {'active': row.active, 'meeting_point': row.meeting_point, 'entrance': row.entrance,
            'instructions': row.instructions, 'latitude': str(row.latitude) if row.latitude is not None else None,
            'longitude': str(row.longitude) if row.longitude is not None else None} if visible else None}


def notify_arrival(visit, revision):
    from core_apps.features.planning_models import PlanningEvent
    # Never put directions, access codes or precise map points in notifications.
    PlanningEvent.objects.get_or_create(event_key=f'arrival:{visit.id}:{revision}:{visit.tenant_id}',
        defaults={'recipient_id': visit.tenant_id, 'destination': {
            'action_type':'view_visit', 'event_kind':'viewing_changed', 'target_id':str(visit.id),
            'visit_id':str(visit.id), 'workspace':'individual', 'schema_version':'1',
            'revision':visit.revision, 'instructions_revision':revision, 'change':'arrival_instructions_changed'}})
