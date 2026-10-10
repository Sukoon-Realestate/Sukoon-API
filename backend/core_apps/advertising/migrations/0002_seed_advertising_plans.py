from django.db import migrations


PLANS = [
    {
        "id": "weekly",
        "title_en": "Weekly",
        "title_ar": "أسبوعية",
        "duration_unit": "week",
        "duration_count": 1,
        "amount_minor": 100000,
        "sort_order": 10,
    },
    {
        "id": "monthly",
        "title_en": "Monthly",
        "title_ar": "شهرية",
        "duration_unit": "calendar_month",
        "duration_count": 1,
        "amount_minor": 300000,
        "sort_order": 20,
    },
    {
        "id": "yearly",
        "title_en": "Yearly",
        "title_ar": "سنوية",
        "duration_unit": "calendar_year",
        "duration_count": 1,
        "amount_minor": 3000000,
        "sort_order": 30,
    },
]


def seed_plans(apps, schema_editor):
    AdvertisingPlan = apps.get_model("advertising", "AdvertisingPlan")
    for plan in PLANS:
        defaults = {key: value for key, value in plan.items() if key != "id"}
        AdvertisingPlan.objects.update_or_create(
            id=plan["id"],
            defaults={
                **defaults,
                "currency": "EGP",
                "exponent": 2,
                "revision": "1",
                "active": True,
            },
        )


def remove_seeded_plans(apps, schema_editor):
    AdvertisingPlan = apps.get_model("advertising", "AdvertisingPlan")
    AdvertisingPlan.objects.filter(id__in=[plan["id"] for plan in PLANS]).delete()


class Migration(migrations.Migration):
    dependencies = [("advertising", "0001_initial")]

    operations = [migrations.RunPython(seed_plans, remove_seeded_plans)]
