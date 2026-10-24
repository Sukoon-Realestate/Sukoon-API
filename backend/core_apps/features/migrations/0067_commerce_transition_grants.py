from django.conf import settings
from django.db import migrations
from django.utils import timezone


def preserve_access(apps, schema_editor):
    Feature = apps.get_model("features", "CommerceFeature")
    Grant = apps.get_model("features", "EntitlementGrant")
    User = apps.get_model(settings.AUTH_USER_MODEL)
    alias = schema_editor.connection.alias
    now = timezone.now()
    for code, workspace, en, ar in [
        (
            "priority_alerts",
            "tenant",
            "Priority search alerts",
            "تنبيهات البحث المتقدمة",
        ),
        (
            "advanced_analytics",
            "owner",
            "Advanced analytics and export",
            "التحليلات المتقدمة والتصدير",
        ),
    ]:
        feature, _ = Feature.objects.using(alias).get_or_create(
            code=code,
            defaults={
                "workspace": workspace,
                "label_en": en,
                "label_ar": ar,
                "available": True,
                "enforced": False,
            },
        )
        batch = []
        for user_id in (
            User.objects.using(alias)
            .values_list("pk", flat=True)
            .iterator(chunk_size=1000)
        ):
            batch.append(
                Grant(
                    user_id=user_id,
                    feature=feature,
                    source="grandfathered",
                    starts_at=now,
                    policy_reference="commerce-v1:preserve-existing-access:2026-10-24",
                )
            )
            if len(batch) == 1000:
                Grant.objects.using(alias).bulk_create(batch)
                batch = []
        Grant.objects.using(alias).bulk_create(batch)


class Migration(migrations.Migration):
    dependencies = [
        ("features", "0066_commercefeature_storeaccount_storeproduct_and_more")
    ]
    # Grants are historical policy records and deliberately survive reverse migration.
    operations = [migrations.RunPython(preserve_access, migrations.RunPython.noop)]
