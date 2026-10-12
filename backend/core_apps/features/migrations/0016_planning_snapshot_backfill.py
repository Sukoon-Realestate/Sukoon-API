"""Preserve historical baseline contents and keep unknown deposits unknown."""

from django.db import migrations


def backfill(apps, schema_editor):
    Report = apps.get_model("features", "ConditionReport")
    Offer = apps.get_model("features", "HousingOffer")
    for report in (
        Report.objects.filter(baseline__isnull=False)
        .select_related("baseline")
        .iterator()
    ):
        if report.baseline_snapshot:
            continue
        baseline = report.baseline
        # Prefer the immutable recorded revision where one exists. Do not label
        # a later revision as the one historically reviewed by the participants.
        saved = next(
            (
                x
                for x in baseline.versions
                if x.get("revision") == report.baseline_revision
            ),
            None,
        )
        if saved is None and baseline.revision == report.baseline_revision:
            saved = {
                "revision": baseline.revision,
                "content_revision": baseline.content_revision,
                "items": baseline.items,
                "selection": baseline.selection,
                "inspected_on": str(baseline.inspected_on),
            }
        report.baseline_snapshot = saved or {
            "revision": report.baseline_revision,
            "items": [],
            "unavailable": True,
        }
        report.save(update_fields=["baseline_snapshot"])
    for offer in Offer.objects.filter(deposit_minor=0).iterator():
        if (offer.selection.get("terms") or {}).get("deposit") in (None, ""):
            offer.deposit_minor = None
            offer.save(update_fields=["deposit_minor"])


class Migration(migrations.Migration):
    dependencies = [("features", "0015_post_visit_invitation_compatibility")]
    operations = [migrations.RunPython(backfill, migrations.RunPython.noop)]
