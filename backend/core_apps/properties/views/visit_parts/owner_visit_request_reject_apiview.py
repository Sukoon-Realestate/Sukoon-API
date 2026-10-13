"""Visit: owner visit request reject apiview."""

from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from core_apps.common.renderers import GenericJsonRenderer
from ...models import PropertyVisit
from ...serializers import OwnerVisitRequestDetailSerializer, OwnerVisitRejectSerializer
from ...services import PropertyVisitService


class OwnerVisitRequestRejectAPIView(generics.GenericAPIView):
    """
    API view for the owner to reject a pending visit request (Screen 3).

    Request Body Example (POST):
    {
        "reason": "timing_not_suitable",
        "custom_reason": ""
    }
    """

    serializer_class = OwnerVisitRejectSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        visit = get_object_or_404(
            PropertyVisit.objects.select_related(
                "tenant", "tenant__profile", "property"
            ),
            id=self.kwargs["id"],
            property__owner=request.user,
        )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get("reason")
        custom_reason = serializer.validated_data.get("custom_reason", "")
        visit = PropertyVisitService.reject_visit(
            user=request.user,
            visit_obj=visit,
            reason=reason,
            custom_reason=custom_reason,
        )
        data = OwnerVisitRequestDetailSerializer(
            visit, context={"request": request}
        ).data
        return Response(
            {"message": "تم رفض طلب الزيارة بنجاح.", **data},
            status=status.HTTP_200_OK,
        )


class OwnerVisitRequestAcceptAPIView(generics.GenericAPIView):
    """
    API view for the owner to accept a pending visit request (Screen 2 accept button).

    Request Body Example (POST):
    {}
    """

    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        visit = get_object_or_404(
            PropertyVisit.objects.select_related(
                "tenant", "tenant__profile", "property"
            ),
            id=self.kwargs["id"],
            property__owner=request.user,
        )
        visit = PropertyVisitService.accept_visit(
            user=request.user,
            visit_obj=visit,
        )
        data = OwnerVisitRequestDetailSerializer(
            visit, context={"request": request}
        ).data
        return Response(
            {"message": "تم قبول طلب الزيارة بنجاح.", **data},
            status=status.HTTP_200_OK,
        )
