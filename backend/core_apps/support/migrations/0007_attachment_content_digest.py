from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("support", "0006_private_attachments")]
    operations = [migrations.AddField(model_name="ticketattachment", name="content_sha256", field=models.CharField(max_length=64, blank=True, editable=False))]
