from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination class used across the API resources.
    Allows query parameter-driven page sizing with a maximum ceiling.
    """

    page_size = 9
    page_size_query_param = "page_size"
    max_page_size = 100
