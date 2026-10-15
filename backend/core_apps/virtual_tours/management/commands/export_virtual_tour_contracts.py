import json
from pathlib import Path
from django.core.management.base import BaseCommand
from core_apps.virtual_tours.schemas import AUTHORING
from core_apps.virtual_tours.contracts import DELIVERY, BRIDGE_COMMAND, WALK_DELIVERY
from core_apps.virtual_tours.openapi import document


class Command(BaseCommand):
    help = "Export the exact executable virtual-tour JSON Schemas."

    def add_arguments(self, parser):
        parser.add_argument("directory")

    def handle(self, directory, **options):
        target = Path(directory)
        target.mkdir(parents=True, exist_ok=True)
        for name, schema in (
            ("authoring-v1", AUTHORING),
            ("walk-regions-v1", WALK_DELIVERY),
            ("delivery-v1", DELIVERY),
            ("bridge-command-v1", BRIDGE_COMMAND),
        ):
            (target / f"{name}.schema.json").write_text(
                json.dumps(schema, indent=2) + "\n"
            )
        self.stdout.write(
            "Exported authoring, delivery, walk-region and bridge command schemas."
        )
        (target / "openapi.json").write_text(json.dumps(document(), indent=2) + "\n")
