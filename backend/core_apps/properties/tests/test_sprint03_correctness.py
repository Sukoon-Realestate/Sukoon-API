"""Sprint 03 alias recovery and honest aggregates."""

from types import SimpleNamespace
from uuid import uuid4
import pytest
from django.urls import reverse
from core_apps.properties.amenities import AMENITY_FIELDS, property_amenities
from core_apps.properties.services import OwnerDashboardService
from core_apps.features.services.housing_offer_matching import property_requirements
from .test_views import _create_property

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "route,method",
    [("property-detail", "patch"), ("property-update", "patch"), ("property-update", "put")],
)
def test_every_update_alias_checks_locked_scalar_version(auth_client, user, route, method):
    prop = _create_property(owner=user)
    previous = prop.updated_at.isoformat()
    prop.title = "Newer editor"
    prop.save()
    response = getattr(auth_client, method)(
        reverse(route, kwargs={"id": prop.id}),
        {"title": "Stale editor"},
        format="json",
        HTTP_IF_UNMODIFIED_SINCE=previous,
    )
    assert response.status_code == 409
    prop.refresh_from_db()
    assert prop.title == "Newer editor"


def test_patch_aliases_share_immutable_receipt(auth_client, user):
    user.is_verified = True
    user.save(update_fields=["is_verified"])
    prop = _create_property(owner=user)
    expected = prop.updated_at.isoformat()
    headers = {"HTTP_IDEMPOTENCY_KEY": str(uuid4()), "HTTP_IF_UNMODIFIED_SINCE": expected}
    body = {"title": "Reviewed edit"}
    first = auth_client.patch(
        reverse("property-detail", kwargs={"id": prop.id}), body, format="json", **headers
    )
    assert first.status_code == 200
    prop.refresh_from_db()
    revision = prop.review_revision
    second = auth_client.patch(
        reverse("property-update", kwargs={"id": prop.id}), body, format="json", **headers
    )
    assert second.status_code == 200
    assert second.json() == first.json()
    prop.refresh_from_db()
    assert prop.review_revision == revision
    conflict = auth_client.patch(
        reverse("property-update", kwargs={"id": prop.id}),
        {"title": "Different"},
        format="json",
        **headers
    )
    assert conflict.status_code == 409


def test_metro_registry_matches_planners_and_query_filter(user):
    positive = _create_property(owner=user, near_metro=True, has_wifi=True)
    negative = _create_property(owner=user, near_metro=False)
    from core_apps.features.services.transition_network.solver import (
        property_amenities as transition_amenities,
    )

    assert transition_amenities(positive) == property_amenities(positive) == ["near_metro", "wifi"]
    assert "near_metro" not in transition_amenities(negative)
    from core_apps.properties.models import Property

    assert list(
        property_requirements(Property.objects.all(), {"amenities": ["near_metro"]}).values_list(
            "id", flat=True
        )
    ) == [positive.id]
    for name, field in AMENITY_FIELDS.items():
        assert name in property_amenities(SimpleNamespace(**{field: True}))


def test_dashboard_uses_canonical_reputation_and_null_no_history(user, monkeypatch):
    from core_apps.features.services.reputation import visibility

    monkeypatch.setattr(visibility, "summary", lambda *args: {"average": 4.25, "review_count": 4})
    dashboard = OwnerDashboardService.get_dashboard(user)
    assert dashboard["overall_rating"] == 4.25
    assert dashboard["reviews_count"] == 4
    monkeypatch.setattr(visibility, "subject_rows", lambda *args, **kwargs: [])
    profile = OwnerDashboardService.get_owner_profile(user)
    assert profile["owner"]["average_rating"] == dashboard["overall_rating"]
    assert profile["stats"]["acceptance_rate"] is None
    assert profile["stats"]["handled_visits_count"] == 0
    prop = _create_property(owner=user)
    from core_apps.properties.services import PropertyService

    stats = PropertyService.get_property_statistics(prop)
    assert stats["acceptance_rate"] is None
    assert stats["handled_visits_count"] == 0


def test_cover_retry_keeps_media_identity_across_aliases(auth_client, user, monkeypatch):
    from core_apps.properties.models import PropertyImage
    from .test_views import generate_test_image
    from unittest.mock import Mock

    upload = Mock(
        return_value={
            "public_id": "sprint03_cover",
            "version": 1,
            "resource_type": "image",
            "type": "upload",
            "format": "png",
        }
    )
    monkeypatch.setattr("cloudinary.uploader.upload", upload)
    user.is_verified = True
    user.save(update_fields=["is_verified"])
    prop = _create_property(owner=user)
    headers = {
        "HTTP_IDEMPOTENCY_KEY": str(uuid4()),
        "HTTP_IF_UNMODIFIED_SINCE": prop.updated_at.isoformat(),
    }
    first = auth_client.patch(
        reverse("property-detail", kwargs={"id": prop.id}),
        {"main_image": generate_test_image()},
        format="multipart",
        **headers
    )
    assert first.status_code == 200
    media_id = PropertyImage.objects.get(property=prop).id
    second = auth_client.patch(
        reverse("property-update", kwargs={"id": prop.id}),
        {"main_image": generate_test_image()},
        format="multipart",
        **headers
    )
    assert second.status_code == 200
    assert PropertyImage.objects.get(property=prop).id == media_id
    assert upload.call_count == 1


@pytest.mark.requires_postgres
def test_full_put_replays_without_another_review_revision(auth_client, user):
    user.is_verified = True
    user.save(update_fields=["is_verified"])
    prop = _create_property(owner=user)
    body = {
        "title": "PUT edit",
        "property_type": prop.property_type.slug,
        "governorate": str(prop.governorate.id),
        "city": str(prop.city.id),
        "price": "15000.00",
    }
    headers = {
        "HTTP_IDEMPOTENCY_KEY": str(uuid4()),
        "HTTP_IF_UNMODIFIED_SINCE": prop.updated_at.isoformat(),
    }
    url = reverse("property-update", kwargs={"id": prop.id})
    first = auth_client.put(url, body, format="json", **headers)
    assert first.status_code == 200
    prop.refresh_from_db()
    revision = prop.review_revision
    second = auth_client.put(url, body, format="json", **headers)
    assert second.status_code == 200
    assert second.json() == first.json()
    prop.refresh_from_db()
    assert prop.review_revision == revision
