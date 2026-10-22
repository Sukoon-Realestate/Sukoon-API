"""Apply reviewed forward migrations before admitting a replacement process."""

from contextlib import contextmanager

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, connection

LOCK_KEY = 7200606221501


@contextmanager
def release_lock(timeout_seconds):
    if connection.vendor != "postgresql":
        # Local SQLite development has one process. Production uses PostgreSQL.
        yield
        return
    acquired = False
    with connection.cursor() as cursor:
        cursor.execute("SHOW lock_timeout")
        previous = cursor.fetchone()[0]
        try:
            cursor.execute(
                "SELECT set_config('lock_timeout', %s, false)",
                [f"{int(timeout_seconds * 1000)}ms"],
            )
            cursor.execute("SELECT pg_advisory_lock(%s)", [LOCK_KEY])
            acquired = True
            yield
        finally:
            if acquired:
                cursor.execute("SELECT pg_advisory_unlock(%s)", [LOCK_KEY])
            cursor.execute("SELECT set_config('lock_timeout', %s, false)", [previous])


class Command(BaseCommand):
    help = "Serialize forward migrations and verify completeness before API startup."

    def add_arguments(self, parser):
        parser.add_argument("--lock-timeout", type=float, default=30)

    def handle(self, *args, **options):
        timeout = options["lock_timeout"]
        if not 0 < timeout <= 120:
            raise CommandError("Use a migration lock timeout between 0 and 120 seconds.")
        try:
            with release_lock(timeout):
                call_command("migrate", interactive=False, verbosity=options["verbosity"])
                call_command("migrate", check_unapplied=True, verbosity=0)
        except DatabaseError:
            # Database errors can contain host or connection information.
            raise CommandError(
                "Release schema could not be applied or locked; API startup is stopped."
            ) from None
