from core_apps.common.management.commands.seed_db import Command as SeedDbCommand


class Command(SeedDbCommand):
    help = "Alias for seed_db command"
