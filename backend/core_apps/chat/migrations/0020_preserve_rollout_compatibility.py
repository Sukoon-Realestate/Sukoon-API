"""Repair local databases that applied the unpublished column-removal variant."""

from django.db import migrations


def ensure_compatibility_column(apps, schema_editor):
    model = apps.get_model("chat", "Conversation")
    field = model._meta.get_field("workspace_archived")
    with schema_editor.connection.cursor() as cursor:
        columns = schema_editor.connection.introspection.get_table_description(
            cursor, model._meta.db_table
        )
    if field.column not in {column.name for column in columns}:
        schema_editor.add_field(model, field)


class Migration(migrations.Migration):
    dependencies = [("chat", "0019_classify_existing_direct_chats")]
    operations = [
        migrations.RunPython(ensure_compatibility_column, migrations.RunPython.noop)
    ]
