from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("properties", "0012_alter_city_slug_alter_governorate_slug")]

    operations = [
        migrations.RemoveField(
            model_name="property",
            name="country",
        ),
    ]
