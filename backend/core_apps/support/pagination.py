from core_apps.common.pagination import ClientResultsSetPagination


class SupportPagination(ClientResultsSetPagination):
    """
    Pagination for support tickets listing matching mobile client specs.
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
