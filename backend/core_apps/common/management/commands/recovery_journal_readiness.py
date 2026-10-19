"""Retained command name gives an explicit retired-feature response."""

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Retired: independent disaster recovery is deferred by product decision."

    def handle(self, *args, **options):
        raise CommandError(
            "Independent disaster recovery and reopening approval are deferred. No journal is consulted and no approval is granted. Account and operation recovery remain active."
        )
