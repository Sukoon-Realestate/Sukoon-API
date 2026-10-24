from importlib import import_module
from django.db import migrations
from django.utils import timezone


def refresh(apps, schema_editor):
    old = import_module('core_apps.common.migrations.0004_seed_public_content').CONTENT
    from core_apps.common.content.public_pages_v2 import CONTENT
    Page = apps.get_model('common', 'PublicContentPage')
    for slug, languages in CONTENT.items():
        page = Page.objects.filter(slug=slug).first()
        if page is None:
            page = Page(slug=slug)
        changes = {}
        for language, (title, body) in languages.items():
            existing = getattr(page, f'content_{language}', '')
            if existing and existing != old[slug][language]['content']:
                continue  # Preserve independently published administrator edits.
            changes[f'title_{language}'] = title
            changes[f'content_{language}'] = body
        if changes:
            for key, value in changes.items():
                setattr(page, key, value)
            page.revision = (page.revision or 0) + 1
            page.updated_at = timezone.now()
            page.save()

class Migration(migrations.Migration):
    dependencies = [('common', '0008_runtime_incidents')]
    operations = [migrations.RunPython(refresh, migrations.RunPython.noop)]
