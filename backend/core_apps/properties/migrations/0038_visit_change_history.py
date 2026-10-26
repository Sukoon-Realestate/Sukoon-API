from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("properties", "0037_alter_city_options_alter_district_options_and_more")
    ]
    operations = [
        migrations.AddField(
            model_name="propertyvisit",
            name="change_history",
            field=models.JSONField(default=list, blank=True, editable=False),
        ),
    ]
