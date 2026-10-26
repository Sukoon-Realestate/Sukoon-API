from django.db import migrations, models


def preserve_access(apps, schema_editor):
    processes = apps.get_model("features", "GroupProcess")
    alias = schema_editor.connection.alias
    for process in processes.objects.using(alias).select_related("group").iterator():
        # An unchanged roster proves that the current group revision includes
        # precisely the same membership period. For older rosters retain the
        # previous conservative access bound, never grant a returning member.
        bound = (
            process.group.revision
            if process.group.roster_revision == process.roster_revision
            else process.roster_revision
        )
        processes.objects.using(alias).filter(pk=process.pk).update(
            access_group_revision=bound
        )


class Migration(migrations.Migration):
    dependencies = [
        ("features", "0080_rentalsigningdocument_rentalsigninghint_and_more"),
    ]
    operations = [
        migrations.AddField(
            model_name="groupprocess",
            name="access_group_revision",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.RunPython(preserve_access, migrations.RunPython.noop),
    ]
