"""Coordinated development upgrades preserve existing rows (D09/S02)."""

from importlib import import_module
from uuid import uuid4

import pytest
from django.apps import apps
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from core_apps.chat.models import Conversation
from core_apps.notifications.models import DeviceToken
from core_apps.properties.models import Property, PropertyImage
from core_apps.users.models import User


@pytest.mark.django_db(transaction=True)
def test_coordinated_upgrade_preserves_previous_account_property_and_chat():
    if connection.vendor != "postgresql":
        pytest.skip("Forward schema preservation uses isolated PostgreSQL")
    # D09 updates writers together. It does not require an old development ORM
    # to keep writing after the schema changes. Preserve its existing records.
    schema = connection.ops.quote_name("coordinated_release_" + uuid4().hex)
    with connection.cursor() as cursor:
        cursor.execute("SHOW search_path")
        original_path = cursor.fetchone()[0]
        cursor.execute(f"CREATE SCHEMA {schema}")
        cursor.execute(f"SET search_path TO {schema}")
    try:
        executor = MigrationExecutor(connection)
        after = executor.loader.graph.leaf_nodes()
        before = [
            ("users", "0006_session_metadata"),
            ("notifications", "0010_rent_payment_reminders"),
            ("properties", "0031_merge_20261024_1458"),
            ("chat", "0018_conversation_consent_revision"),
        ]
        executor.migrate(before)
        previous = executor.loader.project_state(before).apps
        owner = previous.get_model("users", "User").objects.create(
            email="coordinated-release@example.test",
        )
        device = previous.get_model("notifications", "DeviceToken").objects.create(
            user_id=owner.pk,
            token="coordinated-release-test-token",
        )
        governorate = previous.get_model("properties", "Governorate").objects.create(
            name="Preserved region"
        )
        city = previous.get_model("properties", "City").objects.create(
            name="Preserved city", governorate=governorate
        )
        kind = previous.get_model("properties", "PropertyType").objects.create(
            name="Preserved type", slug="preserved-type"
        )
        prop = previous.get_model("properties", "Property").objects.create(
            owner_id=owner.pk,
            title="Preserved listing",
            price=6500,
            property_type=kind,
            city=city,
            governorate=governorate,
            district="Test district",
        )
        photo = previous.get_model("properties", "PropertyImage").objects.create(
            property_id=prop.pk,
            image="properties/coordinated-release-test-image",
        )
        conversation = previous.get_model("chat", "Conversation").objects.create(
            last_message_preview="Preserved conversation history"
        )
        MigrationExecutor(connection).migrate(after)
        current = Property.objects.get(pk=prop.pk)
        assert current.id == prop.id and current.title == prop.title
        assert current.price == prop.price and current.owner_id == owner.pk
        assert current.review_revision >= 1 and not current.moderation_blocked
        assert not User.objects.get(pk=owner.pk).requires_bound_session
        assert DeviceToken.objects.get(pk=device.pk).language == "ar"
        current_photo = PropertyImage.objects.get(pk=photo.pk)
        assert current_photo.position == 0 and str(current_photo.image) == str(
            photo.image
        )
        assert Conversation.objects.get(pk=conversation.pk).last_message_preview == (
            "Preserved conversation history"
        )
        new_record = Property.objects.create(
            owner_id=owner.pk,
            title="Current writer",
            property_type_id=kind.pk,
            city_id=city.pk,
            governorate_id=governorate.pk,
        )
        assert new_record.review_revision == 1 and not new_record.moderation_blocked
    finally:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT set_config('search_path', %s, false)", [original_path]
            )
            cursor.execute(f"DROP SCHEMA {schema} CASCADE")


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
