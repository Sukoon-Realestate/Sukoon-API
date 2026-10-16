from rest_framework.response import Response
from ..models import RentalInterest
from ..rental_serializers import RentalInterestSerializer
from ..services.rental_lifecycle.deals import deal_projection
from .common import endpoint, page


@endpoint(["GET"])
def rental_deal(request, subject_id):
    return Response(deal_projection(request.user, subject_id))


@endpoint(["GET"])
def owner_application_queue(request):
    queryset = (
        RentalInterest.objects.filter(property__owner=request.user)
        .exclude(status__in=["withdrawn", "rejected"])
        .select_related("property__owner", "tenant")
        .order_by("response_due_at", "created_at")
    )
    return page(
        request,
        queryset,
        lambda item: RentalInterestSerializer(item, context={"request": request}).data,
    )
