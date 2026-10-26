from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("features", "0089_housing_offer_source_history")]
    operations = [
        migrations.AddField(
            model_name="commercefeature",
            name="revision",
            field=models.PositiveIntegerField(default=1, editable=False),
        ),
        migrations.AddField(
            model_name="planbenefit",
            name="revision",
            field=models.PositiveIntegerField(default=1, editable=False),
        ),
    ]
