import importlib

import pytest
from django.apps import apps
from django.db import connection


@pytest.mark.django_db
def test_search_migration_does_not_require_installing_postgres_extensions():
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL extension permissions")
    assert connection.settings_dict["NAME"].startswith("test_")
    migration = importlib.import_module(
        "core_apps.chat.migrations.0015_search_document"
    )
    # The test transaction restores the original index/extension afterwards.
    with connection.cursor() as cursor:
        cursor.execute("DROP INDEX IF EXISTS chat_search_body_trgm")
        cursor.execute("DROP EXTENSION IF EXISTS pg_trgm")
    with connection.schema_editor() as editor:
        migration.indexes(apps, editor)
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname='pg_trgm')"
        )
        assert cursor.fetchone()[0] is False
        cursor.execute("SELECT count(*) FROM chat_chatsearchdocument")
        assert cursor.fetchone()[0] >= 0
