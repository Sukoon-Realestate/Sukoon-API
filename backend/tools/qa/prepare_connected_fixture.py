"""Fresh additive native fixtures in the explicitly guarded connected workspace."""

import json
from pathlib import Path
import re
import uuid
from datetime import timedelta


def prepare(run_name=None):
    from django.conf import settings
    from django.db import connection
    from django.utils import timezone

    root = Path(settings.CONNECTED_ACCEPTANCE_ROOT)
    marker = json.loads((root / "workspace.json").read_text())
    database = connection.settings_dict
    if (marker["purpose"] != "disposable_connected_acceptance" or connection.vendor != "postgresql"
            or database["NAME"] != marker["database"] or database["HOST"] != "127.0.0.1"
            or database["USER"] != "sprint4_qa" or str(database["PORT"]) != str(marker["postgres_port"])):
        raise RuntimeError("Native fixtures require the owned disposable connected workspace")
    output = root
    if run_name is not None:
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,39}", run_name):
            raise ValueError("Use a new lowercase alphanumeric run name")
        output = root / "runs" / run_name
        output.mkdir(parents=True, mode=0o700, exist_ok=False)
    if any((output / name).exists() for name in ("actors.json", "manifest.json", "native-fixture.json")):
        raise FileExistsError("Preserve the existing actors, credentials and execution state")

    from core_apps.features.management.cycle_qa import prepare_cycle_run, write_private_json
    from core_apps.properties.models import City, Property, PropertyVisit

    manifest = prepare_cycle_run("sprint4-" + uuid.uuid4().hex[:12], str(output / "actors.json"))
    actors = json.loads((output / "actors.json").read_text())["actors"]
    branch = manifest["discovery_property"]
    prop = Property.objects.get(id=branch["property_id"])
    city = City.objects.create(name="Native discovery " + uuid.uuid4().hex[:8], governorate=prop.governorate)
    prop.city = city
    prop.save(update_fields=["city"])
    branch["criteria"]["city_id"] = str(city.id)
    manifest["discovery"]["commute"]["filters"]["city"] = str(city.id)
    write_private_json(output / "manifest.json", manifest)
    visit = manifest["structured"]["source_visit_id"]
    # Eligibility fixture only; no native attendance/confirmation journey is claimed.
    PropertyVisit.objects.filter(id=visit).update(visit_date=timezone.localdate() - timedelta(days=1))
    write_private_json(output / "native-fixture.json", {
        "base_url": f"http://127.0.0.1:{marker['http_port']}/api/v1/",
        "actors": {"tenant": actors["tenant_a"], "owner": actors["owner_a"]},
        "property_id": branch["property_id"], "offer_id": branch["offer_id"],
        "city_id": branch["criteria"]["city_id"], "starts_on": branch["start_date"],
        "ends_on": branch["end_date"], "visit_id": visit,
        "release_mode": "mvp" if settings.SUKOON_MVP else "restoration",
    })
    print(f"Fresh isolated native fixture prepared: {output}")
    return output
