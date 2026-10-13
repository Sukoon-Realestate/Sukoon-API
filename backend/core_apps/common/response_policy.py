"""Two-key JSON policy and bounded, non-sensitive transport metadata."""
import re
import uuid
from urllib.parse import parse_qs, urlsplit

from .response_messages import _default_success_message, _extract_message
from .translation import translate_message

PAGE_KEYS = {"results", "count", "per_page", "total_pages", "next", "previous", "page"}
SAFE_CODE = re.compile(r"^[a-zA-Z0-9_.-]{1,80}$")
EXPOSED_HEADERS = (
    "X-App-Error-Code", "X-Correlation-ID", "X-Page", "X-Per-Page",
    "X-Total-Count", "X-Total-Pages", "X-Next-Page", "X-Previous-Page",
    "Retry-After", "Content-Language",
)


def expose_metadata(response):
    existing = response.get("Access-Control-Expose-Headers", "").split(",")
    response["Access-Control-Expose-Headers"] = ", ".join(
        dict.fromkeys(x.strip() for x in [*existing, *EXPOSED_HEADERS] if x.strip())
    )


def error_metadata(response, data, exception=None):
    data = data if isinstance(data, dict) else {}
    code = data.get("code") or getattr(data.get("detail"), "code", None)
    if not code and exception is not None:
        code = getattr(exception, "default_code", None)
    if code and SAFE_CODE.fullmatch(str(code)):
        response["X-App-Error-Code"] = str(code)
    correlation = data.get("correlation_id")
    if correlation and SAFE_CODE.fullmatch(str(correlation)):
        response["X-Correlation-ID"] = str(correlation)


def page_number(link):
    if not link:
        return None
    if isinstance(link, int):
        return link if link > 0 else None
    try:
        return max(1, int(parse_qs(urlsplit(str(link)).query).get("page", [1])[0]))
    except (TypeError, ValueError):
        return None


def collection_payload(payload, response, request):
    """Flatten collections only. Aggregates keep their summaries and results."""
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        return payload
    if not set(payload).issubset(PAGE_KEYS):
        return payload
    items = payload["results"]
    count = payload.get("count")
    per_page = payload.get("per_page")
    total_pages = payload.get("total_pages")
    query = getattr(request, "query_params", getattr(request, "GET", {}))
    try:
        page = int(payload.get("page") or query.get("page", 1))
    except (TypeError, ValueError):
        page = 1
    # A complete unpaginated collection has a known total. Never infer a
    # paginated total from the number of items in this page.
    if count is None and not any(k in payload for k in ("per_page", "next", "total_pages")):
        count = len(items)
    if count is not None and total_pages is None and not payload.get("next"):
        total_pages = 1 if page == 1 else None
    if per_page is None and total_pages == 1:
        per_page = max(1, count)
    headers = {
        "X-Page": page, "X-Per-Page": per_page, "X-Total-Count": count,
        "X-Total-Pages": total_pages, "X-Next-Page": page_number(payload.get("next")),
        "X-Previous-Page": page_number(payload.get("previous")),
    }
    for name, value in headers.items():
        if value is not None:
            response[name] = str(value)
    return items


def envelope(data, response, request):
    language = getattr(request, "LANGUAGE_CODE", None)
    expose_metadata(response)
    if response.status_code >= 400:
        error_metadata(response, data)
        response["Cache-Control"] = "private, no-store"
        return {"message": _extract_message(data, language), "data": None}

    message = None
    payload = data
    if isinstance(data, dict):
        # GET resource fields called message retain their domain meaning.
        wrapped = "data" in data and set(data).issubset({"message", "msg", "key", "data"})
        if wrapped:
            message = data.get("message") or data.get("msg")
            payload = data["data"]
        elif getattr(request, "method", "GET") != "GET" and isinstance(data.get("message"), str):
            payload = {k: v for k, v in data.items() if k != "message"}
            message = data["message"]
            if not payload:
                payload = None
    if not isinstance(message, str) or not message.strip():
        message = str(_default_success_message(getattr(request, "method", None), response.status_code))
    if language:
        message = translate_message(message, language)
    if payload is not None and not isinstance(payload, (dict, list)):
        response.status_code = 500
        response["X-App-Error-Code"] = "malformed_response"
        response["X-Correlation-ID"] = uuid.uuid4().hex
        response["Cache-Control"] = "private, no-store"
        return {"message": translate_message("An error occurred.", language or "en"), "data": None}
    return {"message": message, "data": collection_payload(payload, response, request)}
