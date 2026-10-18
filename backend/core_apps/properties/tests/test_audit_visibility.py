"""Owner visibility commands must not approve edited or pending content."""

import pytest
from django.urls import reverse

from core_apps.properties.models import Property
from .test_owner_property_screen import _create_property


@pytest.fixture
def reviewed_property(user, apartment_type, cairo_city, cairo_governorate):
    return _create_property(user, apartment_type, cairo_city, cairo_governorate)


@pytest.mark.django_db
def test_edit_then_show_cannot_restore_old_moderation_approval(
    auth_client, reviewed_property
):
    prop = reviewed_property
    response = auth_client.patch(
        reverse("property-detail", kwargs={"id": prop.id}),
        {"description": "Changed content requiring review"},
        format="json",
    )
    assert response.status_code == 200, response.data
    response = auth_client.patch(
        reverse("property-toggle-visibility", kwargs={"id": prop.id}),
        {"is_hidden": False},
        format="json",
    )
    assert response.status_code == 200, response.data
    prop.refresh_from_db()
    assert prop.status == Property.Status.UNDER_REVIEW
    assert prop.is_verified is False


@pytest.mark.django_db
def test_editing_hidden_content_keeps_it_unlisted(auth_client, reviewed_property):
    prop = reviewed_property
    prop.status = Property.Status.HIDDEN
    prop.save(update_fields=["status"])
    response = auth_client.patch(
        reverse("property-detail", kwargs={"id": prop.id}),
        {"title": "Updated hidden listing"},
        format="json",
    )
    assert response.status_code == 200, response.data
    prop.refresh_from_db()
    assert prop.status == Property.Status.HIDDEN
    assert prop.is_verified is False
    # Explicit later publication returns to review, not the old approval.
    response = auth_client.patch(
        reverse("property-toggle-visibility", kwargs={"id": prop.id}),
        {"is_hidden": False},
        format="json",
    )
    assert response.status_code == 200
    prop.refresh_from_db()
    assert prop.status == Property.Status.UNDER_REVIEW


@pytest.mark.django_db
@pytest.mark.parametrize(
    "moderation_state", [Property.Status.UNDER_REVIEW, Property.Status.NEEDS_REVISION]
)
def test_historical_pending_approval_flag_cannot_self_approve(
    auth_client, reviewed_property, moderation_state
):
    prop = reviewed_property
    prop.status = moderation_state
    prop.save(update_fields=["status"])
    visibility = reverse("property-toggle-visibility", kwargs={"id": prop.id})
    # A historical pending record may still contain is_verified=True.
    assert (
        auth_client.patch(visibility, {"is_hidden": True}, format="json").status_code
        == 200
    )
    assert (
        auth_client.patch(visibility, {"is_hidden": False}, format="json").status_code
        == 200
    )
    prop.refresh_from_db()
    assert prop.status == Property.Status.UNDER_REVIEW
    assert prop.is_verified is False
