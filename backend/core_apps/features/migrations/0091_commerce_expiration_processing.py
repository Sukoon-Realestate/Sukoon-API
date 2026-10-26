from django.db import migrations, models
from django.utils import timezone


def observe_history(apps, schema_editor):
    # No historical notification backfill. Future expiry remains eligible.
    now = timezone.now()
    for name in ("AccountSubscription", "BoostCampaign"):
        apps.get_model("features", name).objects.using(
            schema_editor.connection.alias
        ).filter(ends_at__lte=now).update(expiration_processed_at=now)


class Migration(migrations.Migration):
    dependencies = [
        ("features", "0090_commerce_benefit_revisions"),
        ("advertising", "0003_expiration_processing"),
    ]
    operations = [
        migrations.AddField(
            model_name=name,
            name="expiration_processed_at",
            field=models.DateTimeField(null=True, blank=True, editable=False),
        )
        for name in ("accountsubscription", "boostcampaign")
    ] + [migrations.RunPython(observe_history, migrations.RunPython.noop)]
