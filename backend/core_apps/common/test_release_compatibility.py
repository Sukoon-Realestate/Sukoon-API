"""The previous deployed ORM must keep reading/writing during the rollout."""

from importlib import import_module

import pytest
from django.apps import apps
from django.db import connection
from django.db.migrations.loader import MigrationLoader

from core_apps.chat.models import Conversation
from core_apps.notifications.models import DeviceToken
from core_apps.properties.models import Property, PropertyImage
from core_apps.properties.tests.conftest import (  # noqa: F401
    apartment_type,
    cairo_city,
    cairo_governorate,
)
from core_apps.users.models import User


@pytest.mark.django_db
def test_previous_release_can_create_rows_after_new_migrations(
    apartment_type,
    cairo_city,
    cairo_governorate,
):
    if connection.vendor != "postgresql":
        pytest.skip("The deployed rolling release uses PostgreSQL")
    previous = (
        MigrationLoader(connection)
        .project_state(
            [
                ("users", "0006_session_metadata"),
                ("notifications", "0010_rent_payment_reminders"),
                ("properties", "0031_merge_20261024_1458"),
                ("chat", "0018_conversation_consent_revision"),
            ]
        )
        .apps
    )
    owner = previous.get_model("users", "User").objects.create(
        email="rolling-release@example.test",
    )
    device = previous.get_model("notifications", "DeviceToken").objects.create(
        user_id=owner.pk,
        token="rolling-release-test-token",
    )
    prop = previous.get_model("properties", "Property").objects.create(
        owner_id=owner.pk,
        title="Rolling release",
        price=6500,
        property_type_id=apartment_type.pk,
        city_id=cairo_city.pk,
        governorate_id=cairo_governorate.pk,
        district="Test district",
    )
    photo = previous.get_model("properties", "PropertyImage").objects.create(
        property_id=prop.pk,
        image="properties/rolling-release-test-image",
    )
    conversation = previous.get_model("chat", "Conversation").objects.create()
    # The old ORM selects its retired column, and new readers receive defaults.
    assert (
        not previous.get_model("chat", "Conversation")
        .objects.get(pk=conversation.pk)
        .workspace_archived
    )
    assert not User.objects.get(pk=owner.pk).requires_bound_session
    assert DeviceToken.objects.get(pk=device.pk).language == "ar"
    current = Property.objects.get(pk=prop.pk)
    assert current.media_revision == 0 and current.search_document == ""
    assert PropertyImage.objects.get(pk=photo.pk).position == 0


@pytest.mark.django_db(transaction=True)
def test_local_unpublished_column_removal_can_be_repaired_without_history_loss():
    if connection.vendor != "postgresql":
        pytest.skip("Schema recovery is verified against PostgreSQL")
    repair = import_module(
        "core_apps.chat.migrations.0020_preserve_rollout_compatibility"
    ).ensure_compatibility_column
    original = Conversation.objects.create(last_message_preview="Keep history")
    field = Conversation._meta.get_field("workspace_archived")
    with connection.schema_editor() as editor:
        editor.remove_field(Conversation, field)
        repair(apps, editor)
        repair(apps, editor)
    restored = Conversation.objects.get(pk=original.pk)
    assert restored.last_message_preview == "Keep history"
    assert restored.workspace_archived is False
