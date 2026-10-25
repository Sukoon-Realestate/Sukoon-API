from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("chat", "0025_message_productivity")]
    operations = [
        migrations.AddField(
            model_name="conversationparticipant",
            name="pinned_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="conversationparticipant",
            name="unread_reminder_sequence",
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="conversationparticipant",
            name="muted_until",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
