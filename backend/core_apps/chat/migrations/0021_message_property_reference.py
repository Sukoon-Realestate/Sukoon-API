from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("chat", "0020_preserve_rollout_compatibility")]
    operations = [
        migrations.AddField(
            model_name="message",
            name="property_reference",
            field=models.JSONField(null=True, blank=True),
        ),
    ]
