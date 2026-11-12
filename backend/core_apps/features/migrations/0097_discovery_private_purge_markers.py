from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("features", "0096_experience_tools")]
    operations = [
        migrations.AddField(
            model_name="commutesearch",
            name="private_purged_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="tenantassistantturn",
            name="private_purged_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddIndex(
            model_name="commutesearch",
            index=models.Index(
                fields=["expires_at", "pkid"],
                condition=models.Q(private_purged_at__isnull=True),
                name="commute_pending_purge_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="tenantassistantturn",
            index=models.Index(
                fields=["expires_at", "pkid"],
                condition=models.Q(private_purged_at__isnull=True),
                name="assistant_pending_purge_idx",
            ),
        ),
    ]
