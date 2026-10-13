import json

import pytest
from rest_framework.exceptions import APIException, Throttled, ValidationError
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from core_apps.advertising.renderers import AdvertisingJsonRenderer
from core_apps.features.renderers import FeatureJsonRenderer
from core_apps.properties.views.post_visit_decision import PostVisitJsonRenderer
from .renderers import GenericJsonRenderer, custom_exception_handler

RENDERERS = [
    GenericJsonRenderer,
    FeatureJsonRenderer,
    AdvertisingJsonRenderer,
    PostVisitJsonRenderer,
]


@pytest.mark.parametrize("renderer", RENDERERS)
@pytest.mark.parametrize("payload", [True, 42, "private server detail"])
def test_scalar_server_payload_is_a_safe_failure(renderer, payload):
    value, response = render(renderer, payload)
    assert response.status_code == 500
    assert value == {"message": "An error occurred.", "data": None}
    assert response["X-App-Error-Code"] == "malformed_response"
    assert response["X-Correlation-ID"]


def render(renderer, payload, status=200, method="GET", language="en"):
    request = getattr(APIRequestFactory(), method.lower())(
        "/?page=2", HTTP_ACCEPT_LANGUAGE=language
    )
    request.LANGUAGE_CODE = language
    response = Response(payload, status=status)
    body = renderer().render(
        payload, renderer_context={"response": response, "request": request}
    )
    return json.loads(body), response


@pytest.mark.parametrize("renderer", RENDERERS)
@pytest.mark.parametrize("payload", [{"id": "a"}, [], [{"id": "a"}], None])
def test_success_has_exact_message_data_contract(renderer, payload):
    body, _ = render(renderer, payload)
    assert set(body) == {"message", "data"}
    assert isinstance(body["message"], str) and body["message"].strip()
    assert body["data"] == payload


@pytest.mark.parametrize("renderer", RENDERERS)
@pytest.mark.parametrize(
    "status", [400, 401, 403, 404, 409, 422, 429, 500, 502, 503, 504]
)
def test_failure_is_null_with_safe_machine_header(renderer, status):
    body, response = render(
        renderer,
        {"message": "Rejected.", "code": "stale_revision", "subject_id": "private"},
        status,
    )
    assert body == {"message": "Rejected.", "data": None}
    assert response["X-App-Error-Code"] == "stale_revision"
    assert "no-store" in response["Cache-Control"]
    assert "private" not in response["Access-Control-Expose-Headers"]


@pytest.mark.parametrize("renderer", RENDERERS)
def test_pagination_is_array_with_exact_headers(renderer):
    body, response = render(
        renderer,
        {
            "results": [{"id": 21}],
            "count": 21,
            "per_page": 20,
            "total_pages": 2,
            "next": None,
            "previous": "http://test/?page=1",
        },
    )
    assert body["data"] == [{"id": 21}]
    for key, value in {
        "X-Page": "2",
        "X-Per-Page": "20",
        "X-Total-Count": "21",
        "X-Total-Pages": "2",
        "X-Previous-Page": "1",
    }.items():
        assert response[key] == value
        assert key in response["Access-Control-Expose-Headers"]
    assert not response.has_header("X-Next-Page")


def test_empty_page_preserves_authoritative_total():
    body, response = render(
        GenericJsonRenderer,
        {"results": [], "count": 0, "per_page": 20, "total_pages": 1},
    )
    assert body["data"] == []
    assert response["X-Total-Count"] == "0"


def test_aggregate_and_domain_message_are_not_flattened():
    payload = {"message": "Customer text", "results": [], "unread_count": 3}
    body, _ = render(GenericJsonRenderer, payload)
    assert body["data"] == payload


@pytest.mark.parametrize("renderer", RENDERERS)
def test_prewrapped_message_is_not_double_wrapped(renderer):
    payload = {"message": "Saved.", "data": {"id": 1}}
    assert render(renderer, payload)[0] == payload


def test_header_rejects_personal_unbounded_or_multiline_values():
    for code in ["person@example.com", "a" * 81, "ok\r\nSecret: nope"]:
        _, response = render(
            GenericJsonRenderer, {"message": "Invalid.", "code": code}, 400
        )
        assert not response.has_header("X-App-Error-Code")


def test_exception_keeps_retry_after_and_classification():
    response = custom_exception_handler(Throttled(wait=12), {})
    assert response.status_code == 429
    assert response["Retry-After"] == "12"
    assert response["X-App-Error-Code"] == "throttled"
    assert set(response.data) == {"message", "data"}
    assert response.data["data"] is None


def test_unexpected_failure_has_safe_correlation(caplog):
    response = custom_exception_handler(RuntimeError("private password"), {})
    assert response.status_code == 500
    assert response["X-Correlation-ID"]
    assert "private password" not in caplog.text
    assert response.data == {"message": "An error occurred.", "data": None}


def test_validation_and_success_are_localized():
    en, _ = render(GenericJsonRenderer, {"email": ["This field is required."]}, 400)
    ar, _ = render(
        GenericJsonRenderer, {"email": ["This field is required."]}, 400, language="ar"
    )
    assert en["message"] != ar["message"]
    assert (
        render(GenericJsonRenderer, None, language="en")[0]["message"]
        != render(GenericJsonRenderer, None, language="ar")[0]["message"]
    )
