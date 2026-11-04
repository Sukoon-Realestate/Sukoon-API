from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from core_apps.common.renderers import GenericJsonRenderer
from core_apps.common.idempotency import fingerprint, IdempotencyConflict, request_key, execute_idempotent
from core_apps.users.models import User
from core_apps.users.services.sessions import validate_session
from ..models import Property, AvailabilityClosure
from ..services.availability_closures import parse_range, affected_visits
from uuid import UUID


def project(row):
    from zoneinfo import ZoneInfo
    zone = ZoneInfo(row.timezone)
    return {'id': str(row.id), 'starts_at': row.starts_at.astimezone(zone).isoformat(),
        'ends_at': row.ends_at.astimezone(zone).isoformat(), 'timezone': row.timezone,
        'revision': row.revision, 'retained_visits': row.retained_visits}


@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
def availability_closures(request, property_id):
    with transaction.atomic():
        actor = User.objects.select_for_update().get(pk=request.user.pk)
        if not actor.is_active or actor.closed_at:
            raise PermissionDenied()
        if request.auth:
            validate_session(actor, request.auth)
        prop = get_object_or_404(Property.objects.select_for_update(), id=property_id, owner=actor, retired_at__isnull=True)
        if request.method == 'GET':
            return Response({'protocol': 1, 'closures': [project(row) for row in prop.dated_closures.filter(active=True)]},
                headers={'Cache-Control': 'private, no-store'})
        def operation():
            if request.data.get('action') == 'remove':
                if request.method != 'PUT':
                    raise ValidationError('Removing a closure requires an explicit commit.')
                try:
                    identity = UUID(request.data.get('closure_id', ''))
                except (ValueError, TypeError, AttributeError):
                    raise ValidationError('Select a valid closure.')
                row = get_object_or_404(AvailabilityClosure, property=prop, id=identity)
                if request.data.get('expected_revision') != row.revision:
                    raise IdempotencyConflict('The closure changed. Refresh it.')
                row.active = False
                row.revision += 1
                row.save(update_fields=['active', 'revision', 'updated_at'])
                return {'protocol': 1, 'removed': str(row.id)}, 200, row.id
            start, end, zone = parse_range(request.data)
            visits = affected_visits(prop, start, end)
            preview = {'protocol': 1, 'starts_at': start.isoformat(), 'ends_at': end.isoformat(),
                'timezone': str(zone), 'affected_visits': visits}
            preview['revision'] = fingerprint({'property': str(prop.id), **preview,
                'closures': list(prop.dated_closures.values_list('id', 'revision', 'active'))})
            if request.method == 'POST':
                return preview, 200, None
            if request.data.get('revision') != preview['revision']:
                raise IdempotencyConflict('Availability or an appointment changed. Preview again.')
            decisions = request.data.get('decisions', {})
            if not isinstance(decisions, dict) or decisions != {v['id']: 'keep' for v in visits}:
                raise ValidationError('Explicitly keep each existing appointment, or arrange its change before closing these times.')
            row = AvailabilityClosure.objects.create(property=prop, starts_at=start, ends_at=end,
                timezone=str(zone), retained_visits=visits)
            return {'protocol': 1, 'closure': project(row)}, 200, row.id
        if request.method == 'POST':
            body, code, _ = operation()
        else:
            key = request_key(request)
            if not key:
                raise ValidationError('An Idempotency-Key is required.')
            body, code, _ = execute_idempotent(user=actor, operation='property.availability-closure',
                key=key, payload={'property': str(prop.id), **dict(request.data)}, action=operation)
        return Response(body, status=code, headers={'Cache-Control': 'private, no-store'})
