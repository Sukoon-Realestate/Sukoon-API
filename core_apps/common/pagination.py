from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination class used across the API resources.
    Allows query parameter-driven page sizing with a maximum ceiling.
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        """Return the project-wide compact pagination payload."""
        return Response(
            {
                "per_page": self.page.paginator.per_page,
                "total_pages": self.page.paginator.num_pages,
                "results": data,
            }
        )
