from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def copy_coordinator(apps, schema_editor):
    Tenancy = apps.get_model("features", "CompanyTenancy")
    for row in Tenancy.objects.select_related(
        "preparation__booking__request"
    ).iterator():
        row.coordinator_id = row.preparation.booking.request.coordinator_id
        row.save(update_fields=["coordinator"])


class Migration(migrations.Migration):
    dependencies = [
        ("features", "0054_company_maintenance_consent"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.AddField(
            model_name="companytenancy",
            name="coordinator",
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="coordinated_company_tenancies",
            ),
        ),
        migrations.RunPython(copy_coordinator, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="companytenancy",
            name="coordinator",
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="coordinated_company_tenancies",
            ),
        ),
    ]
