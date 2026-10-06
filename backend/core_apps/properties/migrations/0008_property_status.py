# Hand-written migration (project rule: makemigrations is never run)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("properties", "0007_propertyvisit_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="property",
            name="status",
            field=models.CharField(
                choices=[
                    ("verified", "Verified"),
                    ("under_review", "Under Review"),
                    ("needs_revision", "Needs Revision"),
                ],
                default="under_review",
                max_length=20,
                verbose_name="Status",
            ),
        ),
    ]
