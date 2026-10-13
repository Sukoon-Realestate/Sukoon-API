from datetime import datetime, timezone
from django.db import migrations

CONTENT = {
    "about-us": {
        "en": {
            "title": "About Us",
            "content": "Sokoun is an innovative real estate rental and discovery "
            "platform designed to streamline property discovery, booking, "
            "and communications between owners and tenants.",
        },
        "ar": {
            "title": "عن سكون",
            "content": "سكون هي منصة عقارية مبتكرة لتأجير واستكشاف العقارات، تهدف "
            "إلى تسهيل البحث عن العقارات وحجز الزيارات والتواصل المباشر "
            "بين الملاك والمستأجرين.",
        },
    },
    "privacy-policy": {
        "en": {
            "title": "Privacy Policy",
            "content": "At Sokoun, we respect your privacy and are committed "
            "to protecting your personal data. This policy explains "
            "how we collect, store, and process your information "
            "when using our application.",
        },
        "ar": {
            "title": "سياسة الخصوصية",
            "content": "في سكون، نحن نحترم خصوصيتك ونلتزم بحماية بياناتك "
            "الشخصية. توضح هذه السياسة كيفية جمع بياناتك وتخزينها "
            "ومعالجتها عند استخدامك للتطبيق.",
        },
    },
    "terms": {
        "en": {
            "title": "Terms and Conditions",
            "content": "By accessing and using Sokoun, you agree to comply with our "
            "terms of service, including fair use, accurate listings, and "
            "respectful interactions.",
        },
        "ar": {
            "title": "الشروط والأحكام",
            "content": "باستخدامك لمنصة سكون، فإنك توافق على الالتزام بشروط وأحكام "
            "الخدمة، بما يشمل الاستخدام العادل ودقة بيانات العقارات والتعامل "
            "المحترم.",
        },
    },
}


def seed_content(apps, schema_editor):
    page = apps.get_model("common", "PublicContentPage")
    for slug, translations in CONTENT.items():
        row, created = page.objects.get_or_create(
            slug=slug,
            defaults={
                f"{key}_{language}": value
                for language, content in translations.items()
                for key, value in content.items()
            },
        )
        if created:
            page.objects.filter(pk=row.pk).update(
                updated_at=datetime(2026, 9, 28, tzinfo=timezone.utc)
            )


class Migration(migrations.Migration):
    dependencies = [("common", "0003_publiccontentpage")]
    operations = [migrations.RunPython(seed_content, migrations.RunPython.noop)]
