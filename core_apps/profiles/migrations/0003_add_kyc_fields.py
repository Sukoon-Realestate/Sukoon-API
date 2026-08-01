# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="id_face",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="profile_documents/id_face/",
                verbose_name="ID Face",
            ),
        ),
        migrations.AddField(
            model_name="profile",
            name="id_back",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="profile_documents/id_back/",
                verbose_name="ID Back",
            ),
        ),
        migrations.AddField(
            model_name="profile",
            name="confirmation_selfi",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="profile_documents/selfie/",
                verbose_name="Confirmation Selfie",
            ),
        ),
        migrations.AddField(
            model_name="profile",
            name="national_id",
            field=models.CharField(
                blank=True,
                default="",
                max_length=50,
                verbose_name="National ID",
            ),
        ),
    ]
