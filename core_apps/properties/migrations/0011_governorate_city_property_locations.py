import uuid

from django.db import migrations, models
import django.db.models.deletion
from django.utils.text import slugify


def timestamped_fields():
    return [
        (
            "pkid",
            models.BigAutoField(editable=False, primary_key=True, serialize=False),
        ),
        ("id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
        ("created_at", models.DateTimeField(auto_now_add=True)),
        ("updated_at", models.DateTimeField(auto_now=True)),
    ]


def migrate_legacy_cities(apps, schema_editor):
    Property = apps.get_model("properties", "Property")
    Governorate = apps.get_model("properties", "Governorate")
    City = apps.get_model("properties", "City")

    for property_obj in Property.objects.all().iterator():
        legacy_city = property_obj.city.strip()
        base_slug = slugify(legacy_city) or "legacy-location"
        governorate, _ = Governorate.objects.get_or_create(
            name=legacy_city,
            defaults={"slug": base_slug},
        )
        city, _ = City.objects.get_or_create(
            governorate=governorate,
            name=legacy_city,
            defaults={"slug": base_slug},
        )
        property_obj.governorate = governorate
        property_obj.city_relation = city
        property_obj.save(update_fields=["governorate", "city_relation"])


class Migration(migrations.Migration):
    dependencies = [("properties", "0010_property_engagement_and_availability")]

    operations = [
        migrations.CreateModel(
            name="Governorate",
            fields=timestamped_fields()
            + [
                (
                    "name",
                    models.CharField(max_length=100, unique=True, verbose_name="Name"),
                ),
                (
                    "slug",
                    models.SlugField(max_length=100, unique=True, verbose_name="Slug"),
                ),
            ],
            options={
                "verbose_name": "Governorate",
                "verbose_name_plural": "Governorates",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="City",
            fields=timestamped_fields()
            + [
                ("name", models.CharField(max_length=100, verbose_name="Name")),
                ("slug", models.SlugField(max_length=100, verbose_name="Slug")),
                (
                    "governorate",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="cities",
                        to="properties.governorate",
                        verbose_name="Governorate",
                    ),
                ),
            ],
            options={
                "verbose_name": "City",
                "verbose_name_plural": "Cities",
                "ordering": ["name"],
            },
        ),
        migrations.AddConstraint(
            model_name="city",
            constraint=models.UniqueConstraint(
                fields=("governorate", "name"),
                name="unique_city_name_per_governorate",
            ),
        ),
        migrations.AddConstraint(
            model_name="city",
            constraint=models.UniqueConstraint(
                fields=("governorate", "slug"),
                name="unique_city_slug_per_governorate",
            ),
        ),
        migrations.AddField(
            model_name="property",
            name="governorate",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="properties",
                to="properties.governorate",
                verbose_name="Governorate",
            ),
        ),
        migrations.AddField(
            model_name="property",
            name="city_relation",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="properties",
                to="properties.city",
                verbose_name="City",
            ),
        ),
        migrations.RunPython(migrate_legacy_cities, migrations.RunPython.noop),
        migrations.RemoveIndex(
            model_name="property",
            name="property_location_idx",
        ),
        migrations.RemoveField(model_name="property", name="city"),
        migrations.RenameField(
            model_name="property", old_name="city_relation", new_name="city"
        ),
        migrations.AlterField(
            model_name="property",
            name="governorate",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="properties",
                to="properties.governorate",
                verbose_name="Governorate",
            ),
        ),
        migrations.AlterField(
            model_name="property",
            name="city",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="properties",
                to="properties.city",
                verbose_name="City",
            ),
        ),
        migrations.AddIndex(
            model_name="property",
            index=models.Index(
                fields=["governorate", "city", "district"],
                name="property_location_idx",
            ),
        ),
    ]
