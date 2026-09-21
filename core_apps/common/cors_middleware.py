from typing import Callable
from django.http import HttpRequest, HttpResponse


class DevCorsMiddleware:
    """
    Lightweight middleware for local development to allow CORS requests
    from the frontend development server (e.g. Next.js on port 3000).
    """

    ALLOWED_ORIGIN_HOSTS = ("localhost", "127.0.0.1")

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        origin = request.headers.get("Origin", "")

        # ? Handle CORS preflight OPTIONS requests
        if request.method == "OPTIONS" and origin:
            response = HttpResponse(status=200)
            self._add_cors_headers(response, origin)
            return response

        response = self.get_response(request)
        if origin:
            self._add_cors_headers(response, origin)
        return response

    def _add_cors_headers(self, response: HttpResponse, origin: str) -> None:
        # ? Allow any localhost/127.0.0.1 origin during local dev
        is_allowed = any(
            origin.startswith(f"http://{host}:") or origin == f"http://{host}"
            for host in self.ALLOWED_ORIGIN_HOSTS
        )
        if is_allowed:
            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Allow-Credentials"] = "true"
            response["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            )
            response["Access-Control-Allow-Headers"] = (
                "Content-Type, Authorization, X-Requested-With, Accept, Origin, Cookie"
            )
            response["Access-Control-Max-Age"] = "86400"
