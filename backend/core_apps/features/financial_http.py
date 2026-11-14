"""Transport for the explicit opt-in compact personal finance collection."""

from .pagination import FeaturePagination
from .services.financial_lists import financial_list, financial_summary


def compact_financial_response(request, kind):
    query = financial_list(
        request.user,
        kind,
        workspace=request.query_params.get("workspace"),
        lease_id=request.query_params.get("lease_id"),
    )
    pager = FeaturePagination()
    page = pager.paginate_queryset(query, request)
    return pager.get_paginated_response(
        [financial_summary(item, kind) for item in page]
    )


__all__ = ["compact_financial_response"]
