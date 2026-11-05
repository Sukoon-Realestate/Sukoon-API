from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("virtual_tours", "0006_capture_processing_retry")]
    operations = [migrations.AddField(
        model_name="tourreviewevent", name="public_reason",
        field=models.TextField(blank=True, default=""),
    )]
