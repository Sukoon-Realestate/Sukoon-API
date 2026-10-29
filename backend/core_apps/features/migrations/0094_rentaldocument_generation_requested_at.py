from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("features", "0093_rentalchange_termination_notice_snapshot")]

    operations = [
        migrations.AddField(
            model_name="rentaldocument",
            name="generation_requested_at",
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
        migrations.AddIndex(
            model_name="rentaldocument",
            index=models.Index(
                fields=["updated_at", "id"],
                condition=models.Q(
                    status="queued",
                    document_type="statement",
                    generation_requested_at__isnull=False,
                ),
                name="queued_statement_generation",
            ),
        ),
    ]
