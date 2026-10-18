from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("features", "0042_tender_package_jobs_and_bid_revisions")]
    # Legacy appointments retain their original time; no unreviewed end or
    # consent is invented. A new proposal is needed before starting work.
    operations = [
        migrations.AddField(
            model_name="maintenancerequest",
            name="appointment_ends_at",
            field=models.DateTimeField(null=True, blank=True),
        )
    ]
