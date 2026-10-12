"""A renewal's activation is its agreed start, including older empty dates."""

from datetime import date
from django.db import migrations


def backfill(apps, schema_editor):
    Change = apps.get_model("features", "RentalChange")
    for change in Change.objects.filter(
        kind="renewal", effective_on__isnull=True
    ).iterator():
        try:
            change.effective_on = date.fromisoformat(change.terms["starts_on"])
        except (KeyError, TypeError, ValueError):
            continue
        change.save(update_fields=["effective_on"])


class Migration(migrations.Migration):
    dependencies = [("features", "0016_planning_snapshot_backfill")]
    operations = [migrations.RunPython(backfill, migrations.RunPython.noop)]
