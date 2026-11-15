from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("profiles", "0014_profile_media_provenance")]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="google_avatar_url",
            field=models.URLField(blank=True, default="", editable=False, max_length=2048),
        ),
    ]
