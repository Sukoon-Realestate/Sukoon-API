from django.db import migrations, models
import django.db.models.deletion
import uuid


PROPERTY_TYPE_MAP = {
    "apartment": "Apartment",
    "house": "House",
    "villa": "Villa",
    "studio": "Studio",
    "penthouse": "Penthouse",
}


def migrate_property_types(apps, schema_editor):
    PropertyType = apps.get_model("properties", "PropertyType")
    Property = apps.get_model("properties", "Property")

    for slug, name in PROPERTY_TYPE_MAP.items():
        pt = PropertyType.objects.create(name=name, slug=slug)
        Property.objects.filter(property_type_old=slug).update(property_type=pt)


class Migration(migrations.Migration):

    dependencies = [
        ("properties", "0008_property_status"),
    ]

    operations = [
        migrations.CreateModel(
            name="PropertyType",
            fields=[
                (
                    "pkid",
                    models.BigAutoField(
                        editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "id",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "name",
                    models.CharField(max_length=50, unique=True, verbose_name="Name"),
                ),
                (
                    "slug",
                    models.SlugField(
                        help_text="Used in API queries, e.g. ?property_type=apartment",
                        unique=True,
                        verbose_name="Slug",
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True, default="", verbose_name="Description"
                    ),
                ),
            ],
            options={
                "verbose_name": "Property Type",
                "verbose_name_plural": "Property Types",
                "ordering": ["name"],
            },
        ),
        migrations.RemoveIndex(
            model_name="property",
            name="property_type_price_idx",
        ),
        migrations.RenameField(
            model_name="property",
            old_name="property_type",
            new_name="property_type_old",
        ),
        migrations.AddField(
            model_name="property",
            name="property_type",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="properties",
                to="properties.propertytype",
                verbose_name="Property Type",
            ),
        ),
        migrations.RunPython(migrate_property_types, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="property",
            name="property_type_old",
        ),
        migrations.AlterField(
            model_name="property",
            name="property_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="properties",
                to="properties.propertytype",
                verbose_name="Property Type",
            ),
        ),
        migrations.AddIndex(
            model_name="property",
            index=models.Index(
                fields=["property_type", "price"],
                name="property_type_price_idx",
            ),
        ),
    ]
