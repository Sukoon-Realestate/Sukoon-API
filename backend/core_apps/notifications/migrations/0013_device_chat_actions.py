from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("notifications", "0012_push_delivery")]
    operations = [
        migrations.AddField(
            model_name="devicetoken",
            name="chat_actions_version",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        )
    ]
