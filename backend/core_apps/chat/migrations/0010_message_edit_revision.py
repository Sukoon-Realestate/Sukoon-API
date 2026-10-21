from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("chat", "0009_conversation_direct_pair_key")]
    operations = [
        migrations.AddField(
            model_name="message", name="edited_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="message", name="revision",
            field=models.PositiveIntegerField(default=1),
        ),
    ]
