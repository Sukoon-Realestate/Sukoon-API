"""One database snapshot for multi-record management reads, without writes."""

from contextlib import contextmanager
from django.db import connection, transaction


@contextmanager
def consistent_read():
    # Normal HTTP reads start outside a transaction (ATOMIC_REQUESTS is off).
    # An explicit outer transaction owns its own isolation, e.g. test fixtures.
    outer = connection.in_atomic_block
    with transaction.atomic():
        if not outer and connection.vendor == "postgresql":
            with connection.cursor() as cursor:
                cursor.execute(
                    "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY"
                )
        yield
