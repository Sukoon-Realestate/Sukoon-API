"""The nearest confirmed appointment in the requested presentation workspace."""

from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.common.renderers import GenericJsonRenderer
from core_apps.features.services.company.access import company_for
from ..models import PropertyVisit
from ..services.viewing_access import for_user


class HomeVisitReminderQuery(serializers.Serializer):
    workspace = serializers.ChoiceField(choices=['individual', 'owner', 'student', 'company'])
    company_id = serializers.UUIDField(required=False)

    def validate(self, data):
        if data['workspace'] == 'company' and not data.get('company_id'):
            raise serializers.ValidationError({'company_id': 'This field is required.'})
        return data


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
def home_visit_reminder(request):
    query = HomeVisitReminderQuery(data=request.query_params)
    query.is_valid(raise_exception=True)
    workspace = query.validated_data['workspace']
    if workspace == 'owner':
        visits = PropertyVisit.objects.filter(property__owner=request.user)
    else:
        visits = for_user(request.user)
        if workspace == 'company':
            company = company_for(request.user, query.validated_data['company_id'])
            visits = visits.filter(company=company)
        else:
            visits = visits.filter(company__isnull=True)
            student = (
                Q(renter_workspace='student')
                | Q(context_kind__in=['student', 'group', 'student_group'])
                | Q(academic_plan__isnull=False)
                | Q(groupprocess__academic_plan__isnull=False)
            )
            visits = visits.filter(student) if workspace == 'student' else visits.exclude(student)
    today = timezone.localdate()
    visit = (
        visits.filter(status=PropertyVisit.Status.CONFIRMED, visit_date__gte=today)
        .select_related('property')
        .order_by('visit_date', 'visit_time', 'pk')
        .first()
    )
    banner = None if visit is None else {
        'visit_id': str(visit.id),
        'property_id': str(visit.property.id),
        'property_title': visit.property.title,
        'property_district': visit.property.district,
        'visit_date': visit.visit_date.isoformat(),
        'visit_time': visit.visit_time.strftime('%H:%M'),
        'is_today': visit.visit_date == today,
    }
    response = Response({'banner': banner})
    response['Cache-Control'] = 'private, no-store'
    return response
