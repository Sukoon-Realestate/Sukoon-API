"""Backfill normalized listing search and provision indexes after deployment."""

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from core_apps.properties.models import Property
from core_apps.properties.search import trigram_available
from core_apps.properties.services.search_document import document


class Command(BaseCommand):
    help = "Rebuild listing search text and indexes. Provision pg_trgm separately or explicitly opt in."

    def add_arguments(self, parser):
        parser.add_argument(
            "--create-extension",
            action="store_true",
            help="Requires a database role allowed to install pg_trgm.",
        )

    def handle(self, *args, **options):
        if connection.vendor == "postgresql":
            with connection.cursor() as cursor:
                if options["create_extension"]:
                    cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
                cursor.execute(
                    "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname='pg_trgm')"
                )
                if not cursor.fetchone()[0]:
                    raise CommandError(
                        "An authorized database administrator must install pg_trgm before enabling typo-tolerant search."
                    )
                cursor.execute(
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS property_search_text_trgm ON properties_property USING gin (search_document gin_trgm_ops)"
                )
                cursor.execute(
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS property_search_text_fts ON properties_property USING gin (to_tsvector('simple', search_document))"
                )
        count = 0
        for prop in Property.objects.select_related(
            "city", "governorate", "property_type"
        ).iterator(chunk_size=200):
            Property.objects.filter(pk=prop.pk).update(search_document=document(prop))
            count += 1
        trigram_available.cache_clear()
        self.stdout.write(self.style.SUCCESS(f"Rebuilt search for {count} listings."))
