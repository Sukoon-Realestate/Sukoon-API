from django.db import migrations, models
from django.utils import timezone


def observe_history(apps, schema_editor):
    now = timezone.now()
    apps.get_model("advertising", "Advertisement").objects.using(
        schema_editor.connection.alias
    ).filter(ends_at__lte=now).update(expiration_processed_at=now)


class Migration(migrations.Migration):
    dependencies = [("advertising", "0002_seed_advertising_plans")]
    operations = [
        migrations.AddField(
            model_name="advertisement",
            name="expiration_processed_at",
            field=models.DateTimeField(null=True, blank=True, editable=False),
        ),
        migrations.RunPython(observe_history, migrations.RunPython.noop),
    ]
