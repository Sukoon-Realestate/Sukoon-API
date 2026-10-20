from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "properties",
            "0028_propertyvisit_academic_plan_propertyvisit_company_and_more",
        )
    ]
    operations = [
        migrations.AddField(
            model_name="propertyvisit",
            name="stay_preferences",
            field=models.JSONField(blank=True, null=True),
        )
    ]
