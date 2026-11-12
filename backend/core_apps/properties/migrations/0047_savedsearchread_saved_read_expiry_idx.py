"""Use an online index build on PostgreSQL; keep the SQLite test path supported."""

from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models


class AddPortableOnlineIndex(AddIndexConcurrently):
    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor == "postgresql":
            return super().database_forwards(app_label, schema_editor, from_state, to_state)
        return migrations.AddIndex.database_forwards(self, app_label, schema_editor, from_state, to_state)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor == "postgresql":
            return super().database_backwards(app_label, schema_editor, from_state, to_state)
        return migrations.AddIndex.database_backwards(self, app_label, schema_editor, from_state, to_state)


class Migration(migrations.Migration):
    atomic = False
    dependencies = [("properties", "0046_savedsearchread_itemized_savedsearchread_items_ready_and_more")]
    operations = [
        AddPortableOnlineIndex(
            model_name="savedsearchread",
            index=models.Index(fields=["expires_at", "pkid"], name="saved_read_expiry_idx"),
        )
    ]
