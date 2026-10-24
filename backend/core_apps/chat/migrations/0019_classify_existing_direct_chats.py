"""Put existing direct conversations in the ordinary individual/owner inboxes."""

import hashlib

from django.db import migrations
from django.db.models import F, Q


def classify_existing_chats(apps, schema_editor):
    db = schema_editor.connection.alias
    Conversation = apps.get_model("chat", "Conversation")
    Participant = apps.get_model("chat", "ConversationParticipant")
    Workspace = apps.get_model("chat", "ConversationWorkspace")
    RentalContext = apps.get_model("chat", "RentalChatContext")
    ChatList = apps.get_model("chat", "ChatList")
    ListEntry = ChatList.conversations.through
    Property = apps.get_model("properties", "Property")
    Visit = apps.get_model("properties", "PropertyVisit")

    # An explicit context created by the current app already has its own
    # workspace. Keep student chats, groups and company discussions intact.
    candidates = Conversation.objects.using(db).filter(kind="direct").filter(
        Q(direct_context_key__isnull=True) | Q(direct_pair_key__isnull=False)
    )
    ids = list(candidates.order_by("created_at", "pk").values_list("pk", flat=True))
    # Release old keys first: reclassification can change a pair's context key.
    Conversation.objects.using(db).filter(pk__in=ids).update(
        direct_context_key=None, workspace_archived=False,
    )
    for identity in ids:
        conversation = Conversation.objects.using(db).get(pk=identity)
        people = [p.user for p in Participant.objects.using(db).filter(
            conversation_id=identity,
        ).select_related("user").order_by("user_id")]
        people_ids = {person.pk for person in people}
        previous = dict(Workspace.objects.using(db).filter(
            conversation_id=identity, user_id__in=people_ids,
        ).values_list("user_id", "workspace"))
        owner = RentalContext.objects.using(db).filter(
            conversation_id=identity, owner_id__in=people_ids,
        ).values_list("owner_id", flat=True).first()
        if owner is None:
            visit_owners = set(Visit.objects.using(db).filter(
                tenant_id__in=people_ids, property__owner_id__in=people_ids,
            ).exclude(tenant_id=F("property__owner_id")).values_list(
                "property__owner_id", flat=True,
            ))
            if len(visit_owners) == 1:
                owner = visit_owners.pop()
        owners = set(Property.objects.using(db).filter(
            owner_id__in=people_ids,
        ).values_list("owner_id", flat=True))
        scopes = {}
        for person in people:
            if owner is not None:
                scope = "owner" if person.pk == owner else "individual"
            elif person.pk in previous:
                scope = "owner" if previous[person.pk] == "owner" else "individual"
            else:
                scope = "owner" if person.pk in owners else "individual"
            scopes[person.pk] = scope
            Workspace.objects.using(db).update_or_create(
                conversation_id=identity, user_id=person.pk,
                defaults={"workspace": scope},
            )
            # Keep private organization without moving other chats in a list.
            for old_list in list(ChatList.objects.using(db).filter(
                conversations__pk=identity, user_id=person.pk,
            ).exclude(workspace=scope)):
                target, _ = ChatList.objects.using(db).get_or_create(
                    user_id=person.pk, workspace=scope, organization="",
                    name=old_list.name,
                )
                ListEntry.objects.using(db).get_or_create(
                    chatlist_id=target.pk, conversation_id=identity,
                )
                ListEntry.objects.using(db).filter(
                    chatlist_id=old_list.pk, conversation_id=identity,
                ).delete()
        if len(people) == 2:
            contexts = sorted((str(person.id), scopes[person.pk]) for person in people)
            key = hashlib.sha256(repr(contexts).encode()).hexdigest()
            if not Conversation.objects.using(db).filter(direct_context_key=key).exists():
                conversation.direct_context_key = key
                conversation.save(using=db, update_fields=["direct_context_key"])
        # Multiple existing threads remain ordinary, usable threads. Do not
        # merge/delete messages, attachments, receipts, or per-viewer history.


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0018_conversation_consent_revision"),
        ("properties", "0030_propertyvisit_renter_workspace"),
    ]

    operations = [
        migrations.RunPython(classify_existing_chats, migrations.RunPython.noop),
        # Keep the unused column while old processes can still select it.
    ]
