from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("properties", "0039_managed_property_types")]
    operations = [migrations.AddField(
        model_name="propertyimage", name="room_category",
        field=models.CharField(max_length=24, default="other", choices=[
            ("bedroom", "Bedroom"), ("living", "Living room"), ("kitchen", "Kitchen"),
            ("bathroom", "Bathroom"), ("exterior", "Exterior"), ("other", "Other"),
        ]),
    )]
