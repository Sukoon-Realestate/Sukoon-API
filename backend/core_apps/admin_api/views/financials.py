import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from core_apps.admin_api.permissions import IsAdminStaff
from core_apps.admin_api.services.financials_service import (
    get_financial_summary,
    get_transactions_list,
)

logger = logging.getLogger(__name__)


class AdminFinancialSummaryAPIView(APIView):
    """
    Returns financial KPIs, revenue breakdown, and six-month revenue trend.
    """

    permission_classes = [IsAdminStaff]

    def get(self, request):
        data = get_financial_summary()
        return Response(data, status=status.HTTP_200_OK)


class AdminTransactionListAPIView(APIView):
    """
    Returns paginated financial transactions list.
    
    Query Params:
    - status: 'all' | 'paid' | 'pending' | 'refunded'
    - search: str
    """

    permission_classes = [IsAdminStaff]
    pagination_class = PageNumberPagination

    def get(self, request):
        status_filter = request.query_params.get("status")
        search = request.query_params.get("search")

        txns = get_transactions_list(status_filter=status_filter, search=search)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(txns, request, view=self)
        if page is not None:
            return paginator.get_paginated_response(page)

        return Response({"results": txns, "count": len(txns)}, status=status.HTTP_200_OK)
