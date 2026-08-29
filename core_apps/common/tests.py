import json
import uuid

import pytest
from django.contrib.contenttypes.models import ContentType
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from core_apps.common.models import TimeStampedModel, ContentView
from core_apps.common.pagination import StandardResultsSetPagination
from core_apps.common.renderers import GenericJsonRenderer, custom_exception_handler


@pytest.mark.django_db
class TestTimeStampedModel:
    def test_abstract_model_fields_present_on_concrete_subclass(self, user):
        profile = user.profile
        assert isinstance(profile.id, uuid.UUID)
        assert isinstance(profile.pkid, int)
        assert profile.created_at is not None
        assert profile.updated_at is not None

    def test_default_ordering_is_by_created_at_desc(self):
        assert TimeStampedModel._meta.ordering == ["-created_at", "-updated_at"]


@pytest.mark.django_db
class TestContentView:
    def test_record_view_creates_entry(self, user):
        """
        Bug: record_view uses wrong field for object_id (content_type.pkid instead
        of content_object.pkid) and uses variable keys in defaults dict.
        This test documents expected behavior.
        """
        profile = user.profile
        ContentView.record_view(
            content_object=profile,
            user=user,
            viewer_ip="127.0.0.1",
        )
        content_type = ContentType.objects.get_for_model(profile)
        assert ContentView.objects.filter(
            content_type=content_type,
            object_id=profile.pkid,
        ).exists()


class TestGenericJsonRenderer:
    def test_get_request_wraps_payload_in_data(self):
        factory = APIRequestFactory()
        request = factory.get("/")
        response = Response({"id": 1})
        renderer = GenericJsonRenderer()

        rendered = renderer.render(
            response.data,
            renderer_context={"response": response, "request": request},
        )

        assert json.loads(rendered) == {"data": {"id": 1}}

    def test_post_request_extracts_message_and_wraps_payload(self):
        factory = APIRequestFactory()
        request = factory.post("/")
        response = Response({"message": "Created", "id": 1}, status=201)
        renderer = GenericJsonRenderer()

        rendered = renderer.render(
            response.data,
            renderer_context={"response": response, "request": request},
        )

        assert json.loads(rendered) == {"message": "Created", "data": {"id": 1}}

    def test_post_request_without_message_uses_default(self):
        factory = APIRequestFactory()
        request = factory.post("/")
        response = Response({"id": 1}, status=201)
        renderer = GenericJsonRenderer()

        rendered = renderer.render(
            response.data,
            renderer_context={"response": response, "request": request},
        )

        assert json.loads(rendered) == {
            "message": "Created successfully.",
            "data": {"id": 1},
        }

    def test_patch_request_uses_updated_default_message(self):
        factory = APIRequestFactory()
        request = factory.patch("/")
        response = Response({"id": 1})
        renderer = GenericJsonRenderer()

        rendered = renderer.render(
            response.data,
            renderer_context={"response": response, "request": request},
        )

        assert json.loads(rendered) == {
            "message": "Updated successfully.",
            "data": {"id": 1},
        }

    def test_delete_request_uses_deleted_default_message(self):
        factory = APIRequestFactory()
        request = factory.delete("/")
        response = Response(status=204)
        renderer = GenericJsonRenderer()

        rendered = renderer.render(
            response.data,
            renderer_context={"response": response, "request": request},
        )

        assert json.loads(rendered) == {
            "message": "Deleted successfully.",
            "data": {},
        }

    def test_error_response_wraps_detail_as_message(self):
        response = Response({"detail": "Invalid token"}, status=400)
        renderer = GenericJsonRenderer()

        rendered = renderer.render(
            response.data,
            renderer_context={"response": response},
        )

        assert json.loads(rendered) == {"message": "Invalid token"}

    def test_error_response_wraps_field_errors_as_message(self):
        response = Response({"name": ["This field is required."]}, status=400)
        renderer = GenericJsonRenderer()

        rendered = renderer.render(
            response.data,
            renderer_context={"response": response},
        )

        assert json.loads(rendered) == {"message": "Name: This field is required."}

    def test_custom_exception_handler_standardizes_errors(self):
        factory = APIRequestFactory()
        request = factory.get("/")
        from rest_framework.exceptions import AuthenticationFailed

        response = custom_exception_handler(
            AuthenticationFailed("Unauthorized"),
            {"request": request, "view": None},
        )

        assert response.status_code == 401
        assert response.data == {"message": "Unauthorized"}


class TestStandardResultsSetPagination:
    def test_response_contains_only_compact_pagination_metadata_and_results(self):
        paginator = StandardResultsSetPagination()
        request = Request(APIRequestFactory().get("/?page_size=2"))
        page = paginator.paginate_queryset([1, 2, 3], request)

        response = paginator.get_paginated_response(page)

        assert response.data == {
            "per_page": 2,
            "total_pages": 2,
            "results": [1, 2],
        }
