from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.common.renderers import GenericJsonRenderer
from ..serializers import PropertyDetailSerializer
from ..services.image_ordering import order_property_images


class OrderImagesAPIView(APIView):
    http_method_names = ["patch", "options"]
    name = "Order Images"
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def patch(self, request, property_id):
        prop = order_property_images(
            request.user, property_id, request.data, request.auth
        )
        return Response(
            PropertyDetailSerializer(prop, context={"request": request}).data
        )
