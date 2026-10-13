"""Typed collection adapter for business assertions after the wire migration.

Contract tests inspect response.json() directly. Existing business scenarios use
this adapter to keep their domain assertions while verifying envelope/headers.
"""
def api_json(response):
    body = response.json()
    assert set(body) == {"message", "data"}
    assert isinstance(body["message"], str) and body["message"].strip()
    if response.status_code >= 400:
        assert body["data"] is None
        return body
    if not isinstance(body["data"], list) or "X-Page" not in response.headers:
        return body
    for key in ("X-Page", "X-Per-Page", "X-Total-Count", "X-Total-Pages"):
        assert key in response.headers, key
    return {**body, "data": {
        "results": body["data"], "count": int(response.headers["X-Total-Count"]),
        "per_page": int(response.headers["X-Per-Page"]), "total_pages": int(response.headers["X-Total-Pages"]),
        "next": response.headers.get("X-Next-Page"), "previous": response.headers.get("X-Previous-Page"),
    }}
