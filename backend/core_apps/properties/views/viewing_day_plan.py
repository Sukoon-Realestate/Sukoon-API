from zoneinfo import ZoneInfo
from decimal import Decimal
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from core_apps.common.renderers import GenericJsonRenderer
from core_apps.users.models import User
from core_apps.users.services.sessions import validate_session
from ..services.viewing_day_plan import day_plan


class StartingPoint(serializers.Serializer):
    latitude = serializers.DecimalField(max_digits=10,decimal_places=7,min_value=Decimal('-90'),max_value=Decimal('90'))
    longitude = serializers.DecimalField(max_digits=10,decimal_places=7,min_value=Decimal('-180'),max_value=Decimal('180'))


class DayPlanQuery(serializers.Serializer):
    day = serializers.DateField()
    workspace = serializers.ChoiceField(choices=['owner','individual'])
    viewing_minutes = serializers.IntegerField(min_value=5,max_value=180,default=30)
    buffer_minutes = serializers.IntegerField(min_value=0,max_value=120,default=10)
    mode = serializers.ChoiceField(choices=['driving','walking','cycling','transit'],default='driving')
    origin = StartingPoint(required=False)
    start_at = serializers.DateTimeField(required=False)

    def validate_start_at(self,value):
        raw=self.initial_data.get('start_at')
        parsed=parse_datetime(raw) if isinstance(raw,str) else None
        if parsed is None or timezone.is_naive(parsed):
            raise ValidationError('Include an explicit UTC offset for the departure time.')
        return value

    def validate(self,data):
        if ('origin' in data) != ('start_at' in data):
            raise ValidationError('A starting point needs an explicit departure time.')
        if 'start_at' in data and data['start_at'].astimezone(ZoneInfo('Africa/Cairo')).date()!=data['day']:
            raise ValidationError('The departure time must fall on the chosen Cairo day.')
        return data


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
def viewing_day_plan(request):
    actor = User.objects.get(pk=request.user.pk)
    if not actor.is_active or actor.closed_at:
        raise PermissionDenied()
    if request.auth:
        validate_session(actor,request.auth)
    body = DayPlanQuery(data=request.data)
    body.is_valid(raise_exception=True)
    result = day_plan(actor,body.validated_data)
    if not User.objects.filter(pk=actor.pk,is_active=True,closed_at__isnull=True).exists():
        raise PermissionDenied()
    return Response(result,headers={'Cache-Control':'private, no-store'})
