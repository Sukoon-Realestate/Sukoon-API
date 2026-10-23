from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("properties", "0029_propertyvisit_stay_preferences"),
    ]

    operations = [
        migrations.CreateModel(
            name="PropertyRequest",
            fields=[],
            options={
                "verbose_name": "Property request",
                "verbose_name_plural": "Property requests",
                "proxy": True,
                "default_permissions": (),
                "indexes": [],
                "constraints": [],
            },
            bases=("properties.property",),
        ),
    ]
