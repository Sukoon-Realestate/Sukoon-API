from django.db import transaction
from decimal import Decimal
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from core_apps.common.renderers import GenericJsonRenderer
from core_apps.common.idempotency import execute_idempotent, IdempotencyConflict
from core_apps.users.services.sessions import validate_session
from ..models import ViewingArrival
from ..services.viewing_times import locked_visit
from ..services.viewing_arrival import arrival_payload, notify_arrival


class ArrivalCommand(serializers.Serializer):
    request_key = serializers.UUIDField()
    expected_revision = serializers.IntegerField(min_value=0)
    expected_visit_revision = serializers.IntegerField(min_value=1)
    active = serializers.BooleanField()
    meeting_point = serializers.CharField(max_length=300, allow_blank=True)
    entrance = serializers.CharField(max_length=300, allow_blank=True)
    instructions = serializers.CharField(max_length=2000, allow_blank=True)
    latitude = serializers.DecimalField(max_digits=10, decimal_places=7, min_value=Decimal('-90'), max_value=Decimal('90'), allow_null=True)
    longitude = serializers.DecimalField(max_digits=10, decimal_places=7, min_value=Decimal('-180'), max_value=Decimal('180'), allow_null=True)

    def validate(self, data):
        if (data['latitude'] is None) != (data['longitude'] is None):
            raise ValidationError('Supply both map coordinates, or neither.')
        if data['active'] and not any(data[key] for key in ['meeting_point','entrance','instructions']):
            raise ValidationError('Supply text directions so the card remains useful without maps.')
        return data


@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
def viewing_arrival(request, visit_id):
    with transaction.atomic():
        visit = locked_visit(visit_id, request.user)
        if request.auth:
            validate_session(request.user, request.auth)
        if request.method == 'GET':
            return Response(arrival_payload(visit, request.user), headers={'Cache-Control':'private, no-store'})
        if request.user.pk != visit.property.owner_id:
            raise PermissionDenied('Only the owner may edit arrival instructions.')
        body = ArrivalCommand(data=request.data)
        body.is_valid(raise_exception=True)
        data = body.validated_data
        def apply():
            if visit.status != 'confirmed' or visit.revision != data['expected_visit_revision']:
                raise IdempotencyConflict('The viewing changed. Refresh before sharing directions.')
            row = ViewingArrival.objects.filter(visit=visit).first()
            if (row.revision if row else 0) != data['expected_revision']:
                raise IdempotencyConflict('Arrival directions changed. Refresh and review them.')
            values = {key:data[key] for key in ['active','meeting_point','entrance','instructions','latitude','longitude']}
            if row:
                for key, value in values.items():
                    setattr(row, key, value)
                row.revision += 1
                row.save()
            else:
                row = ViewingArrival.objects.create(visit=visit, **values)
            visit._state.fields_cache.pop('arrival_card', None)
            notify_arrival(visit, row.revision)
            return arrival_payload(visit, request.user), 200, row.id
        result, code, _ = execute_idempotent(user=request.user, operation=f'viewing.arrival:{visit_id}',
            key=str(data['request_key']), payload=data, action=apply)
        return Response(result, status=code, headers={'Cache-Control':'private, no-store'})
