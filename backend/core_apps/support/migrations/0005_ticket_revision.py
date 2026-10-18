from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("support", "0004_seed_help_content")]
    operations = [
        migrations.AddField(
            model_name="ticket",
            name="revision",
            field=models.PositiveIntegerField(default=1),
        )
    ]
