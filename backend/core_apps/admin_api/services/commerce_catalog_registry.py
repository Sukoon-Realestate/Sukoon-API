"""Existing purchasable catalogs; execution policies and grants are not editable."""

from rest_framework.exceptions import ValidationError
from core_apps.advertising.models import AdvertisingPlan
from core_apps.features.models import (
    SubscriptionPlan,
    PromotionOption,
    CommerceFeature,
    PlanBenefit,
)

KINDS = {
    "subscription_plans",
    "advertising_plans",
    "promotion_options",
    "commerce_features",
    "plan_benefits",
}
RELATIONS = {"plan": "subscription_plans", "feature": "commerce_features"}
LABELS = {
    "id": "المعرف الثابت",
    "description_ar": "الوصف بالعربية",
    "description_en": "الوصف بالإنجليزية",
    "period_months": "المدة بالشهور",
    "amount_minor": "السعر بالقرش المصري — 100 قرش = جنيه واحد",
    "audience": "نوع المشترك",
    "duration_unit": "وحدة مدة الإعلان",
    "duration_count": "عدد وحدات المدة",
    "duration_days": "المدة بالأيام",
    "code": "معرف الميزة",
    "label_ar": "اسم الميزة بالعربية",
    "label_en": "اسم الميزة بالإنجليزية",
    "unit_label_ar": "وحدة الاستخدام بالعربية",
    "unit_label_en": "وحدة الاستخدام بالإنجليزية",
    "plan": "خطة الاشتراك",
    "feature": "الميزة القائمة",
    "included": "مشمولة للمشتريات الجديدة",
    "limit": "الحد المعتمد للاستخدام — اتركه فارغًا إذا كان بلا حد",
}


def catalogs(spec):
    return {
        "commerce_features": spec(
            CommerceFeature,
            "وصف المزايا القائمة",
            (
                "code",
                "workspace",
                "label_ar",
                "label_en",
                "description_ar",
                "description_en",
                "unit_label_ar",
                "unit_label_en",
            ),
            ("code", "workspace"),
            "id",
            allow_create=False,
        ),
        "plan_benefits": spec(
            PlanBenefit,
            "مزايا خطط الاشتراك",
            ("plan", "feature", "included", "limit"),
            ("plan", "feature"),
            "id",
        ),
        "subscription_plans": spec(
            SubscriptionPlan,
            "خطط الاشتراك",
            (
                "name_ar",
                "name_en",
                "description_ar",
                "description_en",
                "workspace",
                "audience",
                "period_months",
                "amount_minor",
                "active",
                "sort_order",
            ),
            ("workspace", "audience"),
            "id",
        ),
        "advertising_plans": spec(
            AdvertisingPlan,
            "خطط البانر",
            (
                "id",
                "title_ar",
                "title_en",
                "duration_unit",
                "duration_count",
                "amount_minor",
                "active",
                "sort_order",
            ),
            ("id",),
            "pk",
            opaque_revision=True,
        ),
        "promotion_options": spec(
            PromotionOption,
            "خيارات ترويج العقار",
            (
                "id",
                "title_ar",
                "title_en",
                "duration_days",
                "amount_minor",
                "active",
                "sort_order",
            ),
            ("id",),
            "pk",
        ),
    }


def validate(kind, values, instance):
    if kind not in KINDS:
        return
    if kind == "plan_benefits":
        plan = values.get("plan") or instance.plan
        feature = values.get("feature") or instance.feature
        feature = CommerceFeature.objects.select_for_update().get(pk=feature.pk)
        if plan.audience != "personal":
            raise ValidationError(
                {
                    "plan": "Company subscriptions are for billing tests without paid feature benefits."
                }
            )
        if plan.workspace not in {feature.workspace, "both"}:
            raise ValidationError(
                {"feature": "Choose a feature in this plan's workspace."}
            )
        if instance is None and not plan.active:
            raise ValidationError({"plan": "Choose an active plan."})
        if not feature.available and (
            instance is None or values.get("included", instance.included)
        ):
            raise ValidationError(
                {"feature": "This feature is unavailable for new purchases."}
            )
    if kind == "promotion_options":
        for name in ("title_ar", "title_en"):
            if name in values and not values[name].strip():
                raise ValidationError({name: "Supply the approved localized title."})
        if (
            instance
            and instance.amount_minor == 0
            and values.get("amount_minor", 0) != 0
        ):
            raise ValidationError(
                {"amount_minor": "An existing free promotion remains free."}
            )
    if "id" in values:
        import re

        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,40}", values["id"]):
            raise ValidationError({"id": "Use a stable catalog code."})


def guidance(kind):
    if kind not in KINDS:
        return ""
    if kind == "commerce_features":
        return "عدّل وصف المزايا القائمة وترجمتها. لا تُنشأ ميزة جديدة من هذه الشاشة، ولا يتغير تفعيلها أو كونها مجانية أو قواعد استخدامها."
    return (
        "أدخل المنتجات والأسعار المعتمدة فقط. العملة جنيه مصري، والسعر بالقرش. "
        "تحتفظ المشتريات السابقة بالسعر والمدة المحفوظين. الإيقاف يمنع الاختيار الجديد "
        "ولا يلغي خدمة قائمة. اشتراك الشركة لاختبار دورة الفوترة الحالية؛ "
        "لا يمنح حفظ الكتالوج مزايا مدفوعة أو يغيّر صلاحيات أو سياسات التنفيذ."
    )
