from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("features", "0060_canonical_chargeback_resolution")]
    operations = [
        migrations.AddField(
            model_name="companyhousingrequest",
            name="project_code",
            field=models.CharField(max_length=100, blank=True, default=""),
        ),
        migrations.AddField(
            model_name="companyhousingrequest",
            name="worksite_latitude",
            field=models.DecimalField(
                max_digits=9, decimal_places=6, null=True, blank=True
            ),
        ),
        migrations.AddField(
            model_name="companyhousingrequest",
            name="worksite_longitude",
            field=models.DecimalField(
                max_digits=9, decimal_places=6, null=True, blank=True
            ),
        ),
        migrations.AddField(
            model_name="companyhousingrequest",
            name="requirements",
            field=models.JSONField(default=list, blank=True),
        ),
        migrations.AddField(
            model_name="rentaloperationalcase",
            name="housing_request",
            field=models.ForeignKey(
                "features.companyhousingrequest",
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="assistance_cases",
            ),
        ),
        migrations.AddConstraint(
            model_name="rentaloperationalcase",
            constraint=models.UniqueConstraint(
                fields=("housing_request",),
                condition=models.Q(kind="company_sourcing")
                & ~models.Q(status="resolved"),
                name="one_open_company_sourcing",
            ),
        ),
    ]
