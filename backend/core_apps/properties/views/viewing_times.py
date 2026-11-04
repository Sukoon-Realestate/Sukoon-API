from django.db import transaction
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from core_apps.common.renderers import GenericJsonRenderer
from core_apps.common.idempotency import execute_idempotent
from core_apps.users.services.sessions import validate_session
from ..services.viewing_times import locked_visit, snapshot, command


class ViewingTimeCommand(serializers.Serializer):
    request_key = serializers.UUIDField()
    action = serializers.ChoiceField(choices=['propose', 'accept', 'reject', 'withdraw'])
    expected_visit_revision = serializers.IntegerField(min_value=1, required=False)
    availability_revision = serializers.CharField(max_length=64, required=False)
    slot_ids = serializers.ListField(child=serializers.UUIDField(), min_length=1, max_length=3, required=False)
    proposal_id = serializers.UUIDField(required=False)
    expected_proposal_revision = serializers.IntegerField(min_value=1, required=False)
    slot_id = serializers.UUIDField(required=False)

    def validate(self, data):
        required = ['expected_visit_revision', 'availability_revision', 'slot_ids'] if data['action'] == 'propose' else ['proposal_id', 'expected_proposal_revision']
        if data['action'] == 'accept':
            required.append('slot_id')
        if any(key not in data for key in required):
            raise ValidationError('Refresh and select the complete proposal details.')
        if 'slot_ids' in data and len(set(data['slot_ids'])) != len(data['slot_ids']):
            raise ValidationError('Choose distinct viewing times.')
        return data


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
def viewing_times(request, visit_id):
    with transaction.atomic():
        visit = locked_visit(visit_id, request.user)
        if request.auth:
            validate_session(request.user, request.auth)
        if request.method == 'GET':
            return Response(snapshot(visit), headers={'Cache-Control': 'private, no-store'})
        body = ViewingTimeCommand(data=request.data)
        body.is_valid(raise_exception=True)
        data = body.validated_data
        def apply():
            return command(visit, request.user, data), 200, visit.id
        result, code, _ = execute_idempotent(user=request.user, operation=f'viewing.times:{visit_id}',
            key=str(data['request_key']), payload=data, action=apply)
        return Response(result, status=code, headers={'Cache-Control': 'private, no-store'})
