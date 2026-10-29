from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("features", "0092_staff_setup_and_beneficiary_details")]
    operations = [
        migrations.AddField(
            model_name="rentalchange",
            name="termination_notice_snapshot",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
