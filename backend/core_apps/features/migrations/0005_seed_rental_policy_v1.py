from django.db import migrations


def seed_policy(apps, schema_editor):
    Policy = apps.get_model("features", "RentalCommercialPolicy")
    Policy.objects.get_or_create(
        version="rental-policy-v1",
        defaults={
            "commission_rate_bps": 1000,
            "commission_payer": "owner",
            "commission_basis": "first_period_base_rent",
            "processing_fee_payer": "platform",
            "renewal_commission_rate_bps": 0,
            "timezone": "Africa/Cairo",
            "billing_cycle": "monthly",
            "currency": "EGP",
            "exponent": 2,
            "summary": {
                "commission": "10% of first-period base rent, paid by owner",
                "tenant_service_fee": "0 EGP",
                "processing_fee_payer": "platform",
                "renewal_commission": "0%",
            },
            "is_active": True,
        },
    )


def remove_policy(apps, schema_editor):
    Policy = apps.get_model("features", "RentalCommercialPolicy")
    Policy.objects.filter(version="rental-policy-v1").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("features", "0004_owneronboardingsession_ownerpaymentprofile_and_more"),
    ]

    operations = [migrations.RunPython(seed_policy, remove_policy)]
