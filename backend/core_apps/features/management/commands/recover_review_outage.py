import json
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from core_apps.features.services.reputation.recovery import recover


class Command(BaseCommand):
    help = "Recover one canonical review source using an authorized operator and incident evidence JSON."

    def add_arguments(self, parser):
        parser.add_argument("--operator", required=True, help="Operator user UUID")
        parser.add_argument(
            "--request-file",
            required=True,
            help="JSON body with stable request_key and outage evidence",
        )

    def handle(self, **options):
        try:
            actor = get_user_model().objects.get(id=options["operator"])
            with open(options["request_file"]) as handle:
                result = recover(actor, json.load(handle))
        except Exception as error:
            raise CommandError(str(error)) from error
        self.stdout.write(json.dumps(result))
