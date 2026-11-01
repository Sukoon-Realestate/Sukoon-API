from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("admin_api", "0009_remove_campaignrecipient_campaign_one_recipient_and_more")]
    operations = [
        migrations.AddField(
            model_name="kycsubmission", name="document_decisions",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
