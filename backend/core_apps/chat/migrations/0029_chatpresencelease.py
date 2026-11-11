from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("chat", "0028_voicetranscription"),
    ]

    operations = [
        migrations.CreateModel(
            name="ChatPresenceLease",
            fields=[
                (
                    "connection_id",
                    models.CharField(max_length=255, primary_key=True, serialize=False),
                ),
                ("expires_at", models.DateTimeField(db_index=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                        to_field="id",
                    ),
                ),
            ],
        ),
    ]
