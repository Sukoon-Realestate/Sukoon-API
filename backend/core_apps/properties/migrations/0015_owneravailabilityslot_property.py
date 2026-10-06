import django.db.models.deletion

from django.db import migrations, models


def assign_legacy_slots_to_properties(apps, schema_editor):
    """Copy legacy owner-wide slots to each property owned by that owner."""
    AvailabilitySlot = apps.get_model("properties", "OwnerAvailabilitySlot")
    Property = apps.get_model("properties", "Property")

    for slot in AvailabilitySlot.objects.all().iterator():
        properties = list(
            Property.objects.filter(owner_id=slot.owner_id).order_by("pkid")
        )
        if not properties:
            slot.delete()
            continue

        slot.property_id = properties[0].pk
        slot.save(update_fields=["property"])
        AvailabilitySlot.objects.bulk_create(
            [
                AvailabilitySlot(
                    owner_id=slot.owner_id,
                    property_id=property_obj.pk,
                    date=slot.date,
                    time=slot.time,
                    is_enabled=slot.is_enabled,
                )
                for property_obj in properties[1:]
            ]
        )


def reverse_assign_legacy_slots(apps, schema_editor):
    """The reverse migration keeps one owner-wide record per original duplicate."""
    AvailabilitySlot = apps.get_model("properties", "OwnerAvailabilitySlot")
    seen = set()
    for slot in AvailabilitySlot.objects.order_by("pkid").iterator():
        key = (slot.owner_id, slot.date, slot.time)
        if key in seen:
            slot.delete()
        else:
            seen.add(key)


class Migration(migrations.Migration):
    dependencies = [("properties", "0014_propertyvisitreview")]

    operations = [
        migrations.AddField(
            model_name="owneravailabilityslot",
            name="property",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="availability_slots",
                to="properties.property",
                verbose_name="Property",
            ),
        ),
        migrations.RemoveConstraint(
            model_name="owneravailabilityslot",
            name="unique_owner_availability_slot",
        ),
        migrations.RunPython(
            assign_legacy_slots_to_properties, reverse_assign_legacy_slots
        ),
        migrations.AlterField(
            model_name="owneravailabilityslot",
            name="property",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="availability_slots",
                to="properties.property",
                verbose_name="Property",
            ),
        ),
        migrations.AddConstraint(
            model_name="owneravailabilityslot",
            constraint=models.UniqueConstraint(
                fields=("property", "date", "time"),
                name="unique_property_availability_slot",
            ),
        ),
    ]
