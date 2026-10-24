from django.db import migrations


def backfill(apps, editor):
    from core_apps.properties.services.search_document import document
    Property = apps.get_model('properties', 'Property')
    Image = apps.get_model('properties', 'PropertyImage')
    for prop in Property.objects.select_related('city', 'governorate', 'property_type').iterator(chunk_size=200):
        Property.objects.filter(pk=prop.pk).update(search_document=document(prop))
        images = list(Image.objects.filter(property=prop).order_by('created_at', 'pkid'))
        cover = str(prop.main_image or '')
        images.sort(key=lambda image: 0 if str(image.image) == cover else 1)
        for index, image in enumerate(images):
            Image.objects.filter(pk=image.pk).update(position=index)
    if editor.connection.vendor == 'postgresql':
        editor.execute("CREATE INDEX property_search_text_fts ON properties_property USING gin (to_tsvector('simple', search_document))")
        with editor.connection.cursor() as cursor:
            cursor.execute("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname='pg_trgm')")
            if cursor.fetchone()[0]:
                editor.execute('CREATE INDEX property_search_text_trgm ON properties_property USING gin (search_document gin_trgm_ops)')


def reverse(apps, editor):
    if editor.connection.vendor == 'postgresql':
        editor.execute('DROP INDEX IF EXISTS property_search_text_fts')
        editor.execute('DROP INDEX IF EXISTS property_search_text_trgm')

class Migration(migrations.Migration):
    dependencies = [('properties', '0033_discovery_and_push')]
    operations = [migrations.RunPython(backfill, reverse)]
