from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("virtual_tours", "0004_tourrevision_capture_job")]

    operations = [
        migrations.AddField(
            model_name="tourrevision",
            name="processing_token",
            field=models.UUIDField(editable=False, null=True),
        ),
    ]
