from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("features", "0064_rolling_writer_compatibility")]
    operations = [
        migrations.AddField(
            "rentalevidence", "media_metadata", models.JSONField(null=True, blank=True)
        )
    ]
