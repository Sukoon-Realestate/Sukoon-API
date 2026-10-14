"""Retire manual archiving without abandoning groups that still have members."""

from django.db import migrations
from django.db.models import F
from django.utils import timezone


def restore_populated_groups(apps, schema_editor):
    Group = apps.get_model("features", "HousingGroup")
    Membership = apps.get_model("features", "GroupMembership")
    alias = schema_editor.connection.alias
    populated = (
        Membership.objects.using(alias).filter(status="active").values("group_id")
    )
    # Keep revoked invitations and invalidated consents/processes unchanged.
    # Empty groups remain closed after their final member leaves.
    Group.objects.using(alias).filter(status="archived", pk__in=populated).update(
        status="active",
        revision=F("revision") + 1,
        roster_revision=F("roster_revision") + 1,
        updated_at=timezone.now(),
    )


class Migration(migrations.Migration):
    dependencies = [("features", "0019_dashboard_promotion_catalog")]
    operations = [
        migrations.RunPython(restore_populated_groups, migrations.RunPython.noop)
    ]
