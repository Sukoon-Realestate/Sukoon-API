"""Populate every first-party model in a dedicated offline demo database."""
import json
from pathlib import Path
from urllib.parse import urlsplit

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from core_apps.common.demo_seed.schema import SchemaFixtures, application_models


class Command(BaseCommand):
    help = "Seed all first-party models with deterministic synthetic records and bundled pictures (demo settings only)."

    def add_arguments(self, parser):
        parser.add_argument("--origin", default=getattr(settings, "DEMO_PUBLIC_ORIGIN", "http://127.0.0.1:8010"))
        parser.add_argument("--report", type=Path)

    def handle(self, *args, **options):
        expected = Path(settings.BASE_DIR) / ".demo" / "database.sqlite3"
        actual = connection.settings_dict
        if (not getattr(settings, "DEMO_SEED_ENABLED", False)
            or actual["ENGINE"] != "django.db.backends.sqlite3"
            or Path(actual["NAME"]).resolve() != expected.resolve()):
            raise CommandError("Use config.settings.demo and its isolated .demo/database.sqlite3. Other databases are refused.")
        origin = options["origin"].rstrip("/")
        parsed = urlsplit(origin)
        if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.path or parsed.query or parsed.fragment or parsed.username:
            raise CommandError("--origin must be an HTTP(S) origin without credentials, path, query or fragment.")
        assets = Path(__file__).resolve().parents[2] / "demo_seed" / "assets"
        media = Path(settings.MEDIA_ROOT) / "demo"
        media.mkdir(parents=True, exist_ok=True)
        images = []
        for path in sorted(assets.glob("*.jpg")):
            target = media / path.name
            if not target.exists():
                target.write_bytes(path.read_bytes())
            images.append(f"demo/{path.name}")
        if not images:
            raise CommandError("Bundled demo pictures are missing.")
        fixtures = SchemaFixtures(origin, images)
        try:
            with transaction.atomic():
                for model in application_models():
                    self.stdout.write(f"  {model._meta.label}")
                    fixtures.get(model._meta.label)
                from core_apps.common.demo_seed.scenarios import populate_scenarios
                accounts = populate_scenarios(fixtures)
                connection.check_constraints()
                counts = {m._meta.label: m._base_manager.count() for m in application_models()}
                empty = [label for label, count in counts.items() if not count]
                if empty:
                    raise CommandError(f"Unpopulated models: {', '.join(empty)}")
        except CommandError:
            raise
        except Exception as exc:
            raise CommandError(f"Seed rolled back: {exc}") from exc
        report = {"synthetic": True, "database": str(expected), "models": counts,
                  "model_count": len(counts), "accounts": accounts, "image_origin": origin,
                  "images": images, "scope": "All first-party concrete models; third-party auth/session infrastructure is migration-owned."}
        report_path = options["report"] or expected.parent / "seed-report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        self.stdout.write(self.style.SUCCESS(f"Populated {len(counts)} models. Report: {report_path}"))
        self.stdout.write("Synthetic fixtures only. No email, push, payments or provider jobs were dispatched.")
