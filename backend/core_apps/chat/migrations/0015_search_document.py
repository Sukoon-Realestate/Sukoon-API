from django.db import migrations, models
import django.db.models.deletion


def indexes(apps, editor):
    if editor.connection.vendor == "postgresql":
        # The production app role can migrate its schema but cannot install
        # database extensions. Search still uses the authorized conversation
        # and message indexes; trigram acceleration is optional.
        with editor.connection.cursor() as cursor:
            cursor.execute(
                "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname='pg_trgm')"
            )
            if not cursor.fetchone()[0]:
                return
        editor.execute(
            "CREATE INDEX chat_search_body_trgm ON chat_chatsearchdocument USING gin (body gin_trgm_ops)"
        )


def remove_indexes(apps, editor):
    if editor.connection.vendor == "postgresql":
        editor.execute("DROP INDEX IF EXISTS chat_search_body_trgm")


class Migration(migrations.Migration):
    dependencies = [("chat", "0014_rich_attachments_location_waveform")]
    operations = [
        migrations.CreateModel(
            name="ChatSearchDocument",
            fields=[
                (
                    "message",
                    models.OneToOneField(
                        primary_key=True,
                        serialize=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="search_document",
                        to="chat.message",
                    ),
                ),
                ("body", models.TextField(blank=True, default="")),
                ("links", models.JSONField(blank=True, default=list)),
                ("revision", models.PositiveIntegerField(default=1)),
            ],
        ),
        migrations.RunPython(indexes, remove_indexes),
    ]
