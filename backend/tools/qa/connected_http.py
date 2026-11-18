"""Loopback-only HTTP client for disposable connected acceptance tests.

Only method/path/status leave the client as evidence. Cookies, credentials and
response bodies stay in memory. Redirects and environment proxies are disabled.
"""

import json
from http.cookiejar import CookieJar
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import (
    HTTPCookieProcessor, HTTPRedirectHandler, ProxyHandler, Request, build_opener,
)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class ConnectedHTTP:
    def __init__(self, origin):
        parsed = urlsplit(origin)
        if (parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
                or not parsed.port or parsed.username or parsed.password
                or parsed.path or parsed.query or parsed.fragment):
            raise ValueError("Acceptance requires an explicit loopback HTTP origin and port")
        self.origin = origin
        self.cookies = CookieJar()
        self.opener = build_opener(ProxyHandler({}), NoRedirect(), HTTPCookieProcessor(self.cookies))
        self.observations = []

    def request(self, method, path, expected, *, body=None, origin=None):
        parsed = urlsplit(path)
        if (not path.startswith("/") or path.startswith("//") or parsed.scheme
                or parsed.netloc or parsed.query or parsed.fragment or "\\" in path):
            raise ValueError("Only local paths without query strings are allowed")
        headers = {"Accept": "application/json", "Accept-Language": "en"}
        if origin is not None:
            headers["Origin"] = origin
        if body is not None:
            headers["Content-Type"] = "application/json"
        request = Request(self.origin + path, method=method, headers=headers,
                          data=None if body is None else json.dumps(body).encode())
        try:
            response = self.opener.open(request, timeout=10)
        except HTTPError as error:
            response = error
        with response:
            status = response.code
            raw = response.read()
        # Do not include bodies in failures: login responses contain bearer tokens.
        assert status == expected, f"{method} {path}: expected {expected}, received {status}"
        self.observations.append({"method": method, "path": path, "status": status})
        return json.loads(raw) if raw else None
