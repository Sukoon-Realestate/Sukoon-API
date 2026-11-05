from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from ..models import Property
from ..ownership_proof import read_proof


@method_decorator(never_cache, name='dispatch')
class PropertyOwnershipProofAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, property_id):
        prop = get_object_or_404(Property, id=property_id)
        return read_proof(prop, request.user, request.query_params.get('version'))
