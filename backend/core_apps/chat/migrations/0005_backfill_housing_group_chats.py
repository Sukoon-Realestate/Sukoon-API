import uuid
from django.db import migrations


def backfill(apps, schema_editor):
    Group = apps.get_model("features", "HousingGroup")
    Conversation = apps.get_model("chat", "Conversation")
    Participant = apps.get_model("chat", "ConversationParticipant")
    alias = schema_editor.connection.alias
    for group in Group.objects.using(alias).filter(status="active").iterator():
        conversation, _ = Conversation.objects.using(alias).get_or_create(
            housing_group=group,
            defaults={"kind": "housing_group"},
        )
        for member in group.memberships.using(alias).filter(status="active"):
            Participant.objects.using(alias).get_or_create(
                conversation=conversation,
                user_id=member.user_id,
                defaults={
                    "membership_id": member.pk,
                    "membership_revision": member.joined_revision,
                    "membership_period": uuid.uuid4(),
                    "visible_from_sequence": 1,
                },
            )


class Migration(migrations.Migration):
    dependencies = [("chat", "0004_group_chat_media_events")]
    # Reversing must not destroy conversations or history.
    operations = [migrations.RunPython(backfill, migrations.RunPython.noop)]
