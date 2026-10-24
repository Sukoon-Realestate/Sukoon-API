"""Repeatable sample prices, not a production commercial policy."""

import uuid

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core_apps.features.models import (
    CommerceFeature,
    PlanBenefit,
    StoreProduct,
    SubscriptionPlan,
)


TEST_PLANS = (
    (
        "tenant-plus",
        "Tenant Plus",
        "المستأجر Plus",
        "tenant",
        "personal",
        4900,
        "priority_alerts",
        5,
    ),
    (
        "owner-pro",
        "Owner Pro",
        "المالك Pro",
        "owner",
        "personal",
        9900,
        "advanced_analytics",
        None,
    ),
    (
        "owner-business",
        "Owner Business",
        "أعمال المالك",
        "owner",
        "personal",
        19900,
        "advanced_analytics",
        None,
    ),
    (
        "company-business",
        "Company Business",
        "أعمال الشركات",
        "tenant",
        "organization",
        49900,
        None,
        None,
    ),
)

FEATURE_DEFAULTS = {
    "priority_alerts": {
        "workspace": "tenant",
        "label_en": "Priority search alerts",
        "label_ar": "تنبيهات البحث المتقدمة",
        "description_en": "Active instant search alerts for testing.",
        "description_ar": "تنبيهات بحث فورية نشطة للاختبار.",
        "unit_label_en": "active instant alerts",
        "unit_label_ar": "تنبيهات فورية نشطة",
    },
    "advanced_analytics": {
        "workspace": "owner",
        "label_en": "Analytics and CSV export",
        "label_ar": "التحليلات وتصدير CSV",
        "description_en": "Analytics and CSV export for properties you may access; no numeric quota is configured.",
        "description_ar": "التحليلات وتصدير CSV للعقارات المصرح لك بها؛ لم تُحدد حصة رقمية.",
    },
}


class Command(BaseCommand):
    help = "Seed eight clearly labeled monthly/yearly sample plans in local/test environments."

    @transaction.atomic
    def handle(self, *args, **options):
        if getattr(settings, "RENTAL_RUNTIME_ENVIRONMENT", "production") not in {
            "development",
            "test",
        } or not getattr(settings, "OWNER_TENANT_QA_ENABLED", False):
            raise CommandError("Sample prices require explicit local/test QA settings.")
        if getattr(settings, "COMMERCE_STORE_PURCHASES_ENABLED", False):
            raise CommandError(
                "Disable new store purchases before seeding sample prices."
            )
        features = {}
        for code, defaults in FEATURE_DEFAULTS.items():
            # Preserve existing availability, free access, rollout and grants.
            feature, _ = CommerceFeature.objects.get_or_create(
                code=code, defaults={**defaults, "available": True, "enforced": False}
            )
            for key, value in defaults.items():
                if not getattr(feature, key):
                    setattr(feature, key, value)
            feature.save()
            features[code] = feature
        for order, (
            slug,
            en,
            ar,
            workspace,
            audience,
            monthly,
            feature_code,
            limit,
        ) in enumerate(TEST_PLANS):
            for months, period in ((1, "monthly"), (12, "yearly")):
                identity = uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"sukoon:commerce-test-catalog:v1:{slug}:{period}",
                )
                description_en = "TEST VALUES ONLY. " + (
                    "Organization-owned billing preview; no paid company features or extra authority are granted."
                    if audience == "organization"
                    else (
                        "Analytics and CSV export access; this preview has the same implemented benefits as Owner Pro."
                        if slug == "owner-business"
                        else (
                            "Five active instant search alerts. Daily alerts remain free."
                            if feature_code == "priority_alerts"
                            else "Analytics and CSV export access; no numeric quota is configured."
                        )
                    )
                )
                description_ar = "قيم اختبار فقط. " + (
                    "معاينة فوترة مملوكة للشركة؛ لا تمنح مزايا مدفوعة أو تفويضًا إضافيًا."
                    if audience == "organization"
                    else (
                        "التحليلات وتصدير CSV؛ نفس المزايا المنفذة في باقة المالك Pro لهذه المعاينة."
                        if slug == "owner-business"
                        else (
                            "خمسة تنبيهات بحث فورية نشطة. التنبيهات اليومية مجانية."
                            if feature_code == "priority_alerts"
                            else "التحليلات وتصدير CSV؛ لم تُحدد حصة رقمية."
                        )
                    )
                )
                values = dict(
                    name_en=f"[TEST] {en} — {period}",
                    name_ar=f"[اختبار] {ar} — {'شهري' if months == 1 else 'سنوي'}",
                    description_en=description_en,
                    description_ar=description_ar,
                    workspace=workspace,
                    audience=audience,
                    tier=slug,
                    period_months=months,
                    amount_minor=monthly * months,
                    currency="EGP",
                    exponent=2,
                    active=True,
                    sort_order=1000 + order * 2 + (months == 12),
                )
                (
                    plan,
                    created,
                ) = SubscriptionPlan.objects.select_for_update().get_or_create(
                    id=identity, defaults=values
                )
                expected_benefits = (
                    {features[feature_code].pk: limit} if feature_code else {}
                )
                current_benefits = {
                    benefit.feature_id: benefit.limit
                    for benefit in plan.benefits.filter(included=True)
                }
                if not created and (
                    any(getattr(plan, key) != value for key, value in values.items())
                    or current_benefits != expected_benefits
                ):
                    for key, value in values.items():
                        setattr(plan, key, value)
                    plan.revision += 1
                    plan.save()
                plan.benefits.exclude(feature_id__in=expected_benefits).delete()
                for feature_id, quota in expected_benefits.items():
                    PlanBenefit.objects.update_or_create(
                        plan=plan,
                        feature_id=feature_id,
                        defaults={"included": True, "limit": quota},
                    )
                for platform in ("ios", "android"):
                    StoreProduct.objects.update_or_create(
                        plan=plan,
                        platform=platform,
                        environment="sandbox",
                        defaults={
                            "product_id": f"test.sokoun.{slug.replace('-', '_')}.{period}",
                            "active": False,
                            "amount_minor": values["amount_minor"],
                            "currency": "EGP",
                            "exponent": 2,
                            "period_months": months,
                        },
                    )
                self.stdout.write(
                    f"{plan.name_en}: EGP {plan.amount_minor // 100} ({plan.id})"
                )
        self.stdout.write(
            self.style.SUCCESS(
                "Eight test plans seeded; sandbox SKU placeholders are inactive. No purchases or entitlements were created."
            )
        )
