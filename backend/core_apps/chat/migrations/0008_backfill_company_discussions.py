import uuid
from django.db import migrations
from django.db.models import Q


def forwards(apps, schema_editor):
    Request = apps.get_model("features", "CompanyHousingRequest")
    Member = apps.get_model("features", "CompanyMembership")
    Conversation = apps.get_model("chat", "Conversation")
    Participant = apps.get_model("chat", "ConversationParticipant")
    alias = schema_editor.connection.alias
    for request in Request.objects.using(alias).iterator(chunk_size=100):
        conversation, _ = Conversation.objects.using(alias).get_or_create(
            company_request=request, defaults={"kind": "company_request"}
        )
        members = (
            Member.objects.using(alias)
            .filter(
                company_id=request.company_id,
                is_active=True,
                user__is_active=True,
                user__is_verified=True,
            )
            .filter(
                Q(is_coordinator=True, user_id=request.coordinator_id)
                | Q(is_approver=True, assigned_packages__request=request)
            )
            .distinct()
        )
        for member in members:
            Participant.objects.using(alias).get_or_create(
                conversation=conversation,
                user_id=member.user_id,
                defaults={
                    "company_membership": member,
                    "membership_revision": member.revision,
                    "membership_period": uuid.uuid4(),
                    "visible_from_sequence": 1,
                },
            )


class Migration(migrations.Migration):
    dependencies = [("chat", "0007_company_request_discussions")]
    # Never delete business messages when reversing the data step. Rollback of
    # the schema requires handling retained company conversations explicitly.
    operations = [migrations.RunPython(forwards)]
