from core_apps.common.pagination import StandardResultsSetPagination


class AdminResultsSetPagination(StandardResultsSetPagination):
    """Expose authoritative metadata without changing the existing admin page size."""

    page_size = 10
    page_size_query_param = None
