from django.db import transaction
from rest_framework.decorators import api_view,permission_classes,renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from core_apps.common.idempotency import IdempotencyConflict
from core_apps.common.renderers import GenericJsonRenderer
from core_apps.users.services.sessions import validate_session
from ..services.viewing_times import locked_visit


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
def viewing_message_context(request,visit_id):
    with transaction.atomic():
        visit=locked_visit(visit_id,request.user)
        if request.auth:
            validate_session(request.user,request.auth)
        if visit.status!='confirmed' or visit.visit_date is None or visit.visit_time is None:
            raise IdempotencyConflict('An arrival-delay draft needs a confirmed appointment with an agreed time.')
        expected=request.query_params.get('expected_revision')
        if expected is not None:
            try:
                expected=int(expected)
            except (ValueError,TypeError):
                raise ValidationError('Supply the viewing revision you reviewed.')
            if expected!=visit.revision:
                raise IdempotencyConflict('The appointment changed. Review its current time before preparing a message.')
        other=visit.tenant if visit.property.owner_id==request.user.pk else visit.property.owner
        return Response({'protocol':1,'visit_id':str(visit.id),'revision':visit.revision,
            'property_id':str(visit.property.id),'property_title':visit.property.title,
            'offer_id':visit.offer_id,'offer_name':(visit.offer_snapshot or {}).get('name',''),
            'date':visit.visit_date.isoformat(),'time':visit.visit_time.strftime('%H:%M'),
            'timezone':'Africa/Cairo','other_user_id':str(other.id)},headers={'Cache-Control':'private, no-store'})
