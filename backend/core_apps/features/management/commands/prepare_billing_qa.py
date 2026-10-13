"""Create isolated local actors; seeded records are not execution evidence."""
import secrets
import uuid
from pathlib import Path
from urllib.parse import urlsplit
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core_apps.features.management.cycle_qa import write_private_json
from core_apps.features.models import SubscriptionPlan


class Command(BaseCommand):
    help = "Prepare fresh billing actors and a mode-0600 device fixture."

    def add_arguments(self, parser):
        parser.add_argument("--output", required=True)
        parser.add_argument("--base-url", default="http://127.0.0.1:8000/api/v1/")

    @transaction.atomic
    def handle(self, *args, **options):
        runtime = getattr(settings, "RENTAL_RUNTIME_ENVIRONMENT", "production")
        if runtime not in {"development", "test"} or not getattr(settings, "OWNER_TENANT_QA_ENABLED", False):
            raise CommandError("Explicit local/test QA settings are required.")
        base = urlsplit(options["base_url"])
        if base.hostname != "127.0.0.1" or base.path != "/api/v1/" or base.username or base.query:
            raise CommandError("Only the local loopback API is supported.")
        output = Path(options["output"])
        if output.exists() or output.is_symlink():
            raise CommandError("Use a fresh output file; existing identities are preserved.")
        run = uuid.uuid4().hex[:12]
        actors = {}
        for role in ("owner", "tenant"):
            password = secrets.token_urlsafe(24)
            user = get_user_model().objects.create_user(email=f"billing-{run}-{role}@example.test",
                password=password, first_name="Local", last_name=role, is_verified=True)
            actors[role] = {"email": user.email, "password": password, "id": str(user.id)}
        plan = SubscriptionPlan.objects.create(name_en=f"Local billing plan {run}",
            name_ar=f"خطة اختبار محلية {run}", workspace="both", period_months=1,
            amount_minor=12500, sort_order=0)
        fixture = {"base_url": options["base_url"], "actors": actors, "plan_id": str(plan.id)}
        write_private_json(output, fixture)
        self.stdout.write("Created fresh local billing actors. Credentials are only in the private output file.")
