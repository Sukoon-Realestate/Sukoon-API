from django.db import migrations, models
import core_apps.support.storage


class Migration(migrations.Migration):
    dependencies = [("support", "0005_ticket_revision")]
    operations = [
        migrations.AlterField(
            model_name="ticketattachment",
            name="file",
            field=models.FileField(
                blank=True, upload_to="support/attachments/", verbose_name="File"
            ),
        ),
        migrations.AddField(
            model_name="ticketattachment",
            name="private_file",
            field=models.FileField(
                blank=True,
                upload_to="attachments/",
                storage=core_apps.support.storage.SupportPrivateStorage(),
            ),
        ),
    ]
