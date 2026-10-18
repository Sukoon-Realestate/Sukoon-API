from django.db import migrations
from django.db.models import F


def retire_untyped_artifacts(apps, schema_editor):
    # Preserve historical bytes for investigation. Never expose a ledger export
    # as a signed contract, receipt or amendment.
    Document = apps.get_model("features", "RentalDocument")
    Document.objects.exclude(document_type="statement").filter(
        source_reference="", status="ready"
    ).update(
        status="failed",
        failure_code="legacy_artifact_requires_regeneration",
        revision=F("revision") + 1,
    )


class Migration(migrations.Migration):
    dependencies = [("features", "0050_alter_rentaldocument_options_and_more")]
    operations = [
        migrations.RunPython(retire_untyped_artifacts, migrations.RunPython.noop)
    ]
