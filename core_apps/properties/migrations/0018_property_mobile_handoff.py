import cloudinary.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("properties", "0017_property_video_property_video_duration"),
    ]

    operations = [
        migrations.AlterField(
            model_name="property",
            name="smoking_allowed",
            field=models.BooleanField(
                blank=True, default=False, null=True, verbose_name="Smoking Allowed"
            ),
        ),
        migrations.AddField(
            model_name="property",
            name="street",
            field=models.CharField(
                blank=True, default="", max_length=255, verbose_name="Street"
            ),
        ),
        migrations.AddField(
            model_name="property",
            name="country",
            field=models.CharField(
                blank=True, default="Egypt", max_length=100, verbose_name="Country"
            ),
        ),
        migrations.AddField(
            model_name="property",
            name="building_year",
            field=models.PositiveIntegerField(
                blank=True, null=True, verbose_name="Building Year"
            ),
        ),
        migrations.AddField(
            model_name="property",
            name="deposit",
            field=models.CharField(
                blank=True, default="", max_length=50, verbose_name="Deposit"
            ),
        ),
        migrations.AddField(
            model_name="property",
            name="ownership_proof",
            field=cloudinary.models.CloudinaryField(
                blank=True,
                max_length=255,
                null=True,
                verbose_name="Ownership Proof",
            ),
        ),
        migrations.AddField(
            model_name="property",
            name="is_ownership_verified",
            field=models.BooleanField(
                default=False, verbose_name="Is Ownership Verified"
            ),
        ),
    ]
