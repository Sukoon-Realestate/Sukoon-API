from datetime import datetime
from zoneinfo import ZoneInfo
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from core_apps.properties.models import PropertyVisit
from core_apps.properties.services.viewing_access import can_read
from ..renderers import FeatureJsonRenderer
from .access import require, scope_for


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def viewing_calendar(request, identity):
    require('sync')
    scope_for(request)
    visit = get_object_or_404(PropertyVisit.objects.select_related('property', 'tenant', 'company'), id=identity)
    if not request.user.is_active or not can_read(visit, request.user):
        raise NotFound()
    start = datetime.combine(visit.visit_date, visit.visit_time, ZoneInfo('Africa/Cairo')) if visit.visit_date and visit.visit_time else None
    return Response({'id': str(visit.id), 'revision': visit.revision, 'status': visit.status,
        'title': visit.property.title, 'starts_at': start.isoformat() if start else None,
        # Use only the listing title; no contact details or precise private address.
        'location': '', 'timezone': 'Africa/Cairo'})
