from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .renderers import FeatureJsonRenderer
from .services.chargebacks import operations
from .services.chargebacks.projection import payload


class ChargebackApprovalBody(serializers.Serializer):
    request_key = serializers.UUIDField()
    expected_revision = serializers.IntegerField(min_value=1)
    action = serializers.ChoiceField(choices=["approve_excess_refund"])
    refund_id = serializers.UUIDField()
    reason = serializers.CharField(max_length=2000)

    def to_internal_value(self, data):
        if set(data) - set(self.fields):
            raise serializers.ValidationError("Unsupported chargeback approval fields.")
        return super().to_internal_value(data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def chargeback_detail(request, chargeback_id):
    if request.method == "GET":
        return Response(payload(operations.detail(request.user, chargeback_id)))
    body = ChargebackApprovalBody(data=request.data)
    body.is_valid(raise_exception=True)
    result, status = operations.approve_refund(
        request.user, chargeback_id, body.validated_data
    )
    return Response(result, status=status)
