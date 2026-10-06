from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("properties", "0011_governorate_city_property_locations")]

    operations = [
        migrations.AlterField(
            model_name="city",
            name="slug",
            field=models.SlugField(blank=True, max_length=100, verbose_name="Slug"),
        ),
        migrations.AlterField(
            model_name="governorate",
            name="slug",
            field=models.SlugField(
                blank=True, max_length=100, unique=True, verbose_name="Slug"
            ),
        ),
    ]
