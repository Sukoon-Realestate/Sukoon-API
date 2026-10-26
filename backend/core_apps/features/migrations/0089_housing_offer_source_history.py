from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("features", "0088_refund_attempt_history")]
    operations = [
        migrations.AddField(
            model_name="housingoffer",
            name="source_changes",
            field=models.JSONField(default=list),
        ),
    ]
