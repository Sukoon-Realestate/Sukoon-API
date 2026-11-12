from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from core_apps.common.renderers import GenericJsonRenderer
from core_apps.features.services.company.access import company_for


class RepresentativesAPIView(APIView):
    http_method_names = ["get", "options"]
    name = "Representatives"
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def get(self, request, company_id):
        company = company_for(request.user, company_id, "coordinate")
        rows = (
            company.memberships.filter(
                is_active=True, user__is_active=True, user__is_verified=True
            )
            .select_related("user")
            .order_by("id")
        )
        paginator = PageNumberPagination()
        paginator.page_size = 30
        page = paginator.paginate_queryset(rows, request)
        return paginator.get_paginated_response(
            [
                {
                    "id": str(row.id),
                    "name": row.user.get_full_name,
                    "user_id": str(row.user.id),
                }
                for row in page
            ]
        )
