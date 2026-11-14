"""Advanced Tender command steps; typed adapters retain the HTTP boundary."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound, PermissionDenied
from core_apps.features.advanced_tender_models import OwnerBid
from core_apps.features.services.housing_tenders import commands
from core_apps.features.services.housing_tenders.access import get_tender


def tender_action_post_apply(item, revision, *, action, actor, receipt_data):
    if action == "requirements":
        return commands.respond(actor, item, receipt_data)
    if action == "publish":
        return commands.publish(actor, item)
    if action == "amend":
        return commands.amend(actor, item, receipt_data)
    if action == "withdraw":
        commands.require_action(actor, item, action)
        item.status = "withdrawn"
        item.revision += 1
        item.save()
        return item
    raise NotFound()


def withdraw_bid_post_load(*, actor, bid_id):
    item = get_object_or_404(OwnerBid, id=bid_id, owner=actor)
    get_tender(actor, item.tender.id, lock=True)
    return OwnerBid.objects.select_for_update().get(pk=item.pk)


def withdraw_bid_post_apply(item, revision):
    if item.status != "submitted":
        raise PermissionDenied("This quote can no longer be withdrawn.")
    item.status = "withdrawn"
    item.revision += 1
    item.save()
    return item


def construction_retry_post_apply(item, _, *, enqueue, transaction):
    if item.status != "queued":
        raise PermissionDenied("Only a queued package search can be dispatched again.")
    item.revision += 1
    item.save(update_fields=["revision", "updated_at"])
    transaction.on_commit(lambda: enqueue(str(item.id)))
    return item


def clarifications_get_serialize(item):
    return {
        "id": str(item.id),
        "revision": 1,
        "bid_id": str(item.bid.id),
        "bid_revision": item.bid_revision,
        "text": item.text,
        "author_role": (
            "owner" if item.author_id == item.bid.owner_id else "coordinator"
        ),
        "created_at": item.created_at.isoformat(),
        "amends_terms": False,
    }


def clarifications_get_load(*, actor, bid_id, subject):
    item = get_object_or_404(OwnerBid.objects.select_related("tender"), id=bid_id)
    subject(actor, item.id)
    return item


def clarifications_post_serialize(item):
    return {
        "id": str(item.id),
        "revision": 1,
        "bid_id": str(item.bid.id),
        "bid_revision": item.bid_revision,
        "text": item.text,
        "author_role": (
            "owner" if item.author_id == item.bid.owner_id else "coordinator"
        ),
        "created_at": item.created_at.isoformat(),
        "amends_terms": False,
    }


def clarifications_post_load(*, actor, bid_id, subject):
    item = get_object_or_404(OwnerBid.objects.select_related("tender"), id=bid_id)
    subject(actor, item.id)
    return item


def clarifications_post_apply(
    item, _, *, TenderBidClarification, actor, check_revision, receipt_data, text_field
):
    check_revision(item.revision, receipt_data.get("bid_revision"))
    return TenderBidClarification.objects.create(
        bid=item,
        author=actor,
        bid_revision=item.revision,
        text=text_field(receipt_data, "text", required=True, limit=1600),
    )
