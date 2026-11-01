from django.db import transaction
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..renderers import FeatureJsonRenderer
from .access import FEATURES, enabled, require, scope_for, preferences


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def capabilities(request):
    scope = scope_for(request)
    return Response({'version': 1, 'scope': scope, 'features': [name for name in FEATURES if enabled(name)]})


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def personal_preferences(request):
    from .sync import payload, merge
    require('sync')
    scope = scope_for(request)
    with transaction.atomic():
        item = preferences(request.user, scope, lock=True)
        if request.method == 'POST':
            merge(item, request.data)
        return Response(payload(item))
