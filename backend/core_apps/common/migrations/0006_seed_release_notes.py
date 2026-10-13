from django.db import migrations


def seed_notes(apps, schema_editor):
    # Preserve the existing bundled 1.0.7 notes; do not invent current-version claims.
    apps.get_model("common", "ReleaseNote").objects.get_or_create(
        version="1.0.7", workspace="both", defaults={
            "items_en": "Improved chat experience and faster messaging\nPerformance improvements and bug fixes",
            "items_ar": "تحسين تجربة المحادثة وسرعة الرسائل\nتحسينات في الأداء وإصلاح الأخطاء",
        })


class Migration(migrations.Migration):
    dependencies = [("common", "0005_releasenote_and_more")]
    operations = [migrations.RunPython(seed_notes, migrations.RunPython.noop)]
