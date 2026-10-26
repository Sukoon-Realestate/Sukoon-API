"""Authorized copy for the existing durable planning notification outbox."""

from django.utils.translation import override
from rest_framework.exceptions import NotFound
from .housing_request_reviews import change_payload, require_history_access


def notification_copy(event):
    from ..planning_housing_views_parts.housing_requests import get_request
    from ..planning_housing_views_parts.housing_request_action import get_offer

    data = event.destination
    parent = get_request(event.recipient, data["target_id"])
    kind = data.get("event_kind", "")
    if data.get("housing_offer_id"):
        offer = get_offer(event.recipient, data["housing_offer_id"])
        if offer.request_id != parent.pk:
            raise NotFound()
    if kind == "housing_request_changed":
        require_history_access(event.recipient, parent)
        change = parent.changes.filter(id=data.get("housing_change_id")).first()
        if not change:
            raise NotFound()
        summaries = []
        for language in ("ar", "en"):
            with override(language):
                fields = change_payload(change)["fields"]
                summary = "; ".join(
                    f'{x["label"]}: {x["before_label"]} → {x["after_label"]}'
                    for x in fields
                )
                summaries.append(summary[:500])
        return {
            "title": "عدّل المستأجر طلب السكن / Housing request updated",
            "body": summaries[0]
            + ". راجع التغيير لتأكيد عرضك أو تقديم بديل. / "
            + summaries[1]
            + ". Review to confirm your offer or send a replacement.",
        }
    copy = {
        "housing_offer_source_changed": (
            "تغيّر مصدر عرض السكن / Housing offer source changed",
            "راجع تغييرات الإعلان والعرض السابق في السجل. يحتاج العرض إلى استبدال قبل متابعة جديدة. / Review the listing changes and original offer in history. A replacement is required before a new follow-up.",
        ),
        "housing_offer_received": (
            "عرض سكن جديد / New housing offer",
            "وصل عرض جديد لطلبك. / Review the new offer for your request.",
        ),
        "housing_offer_reconfirmed": (
            "أكد المالك استمرار عرضه / Offer confirmed",
            "أكد المالك عرضه بعد مراجعة تعديل الطلب. / The owner confirmed the offer against your updated request.",
        ),
        "housing_offer_replaced": (
            "عرض سكن بديل / Replacement offer",
            "قدّم المالك عرضًا بديلًا. ستجد العرض السابق في السجل. / Review the replacement; the previous offer is in history.",
        ),
        "housing_offer_withdrawn": (
            "سحب المالك عرضه / Offer withdrawn",
            "سحب المالك عرض السكن الذي قدّمه. / The owner withdrew their housing offer.",
        ),
        "housing_offer_declined": (
            "رفض المستأجر العرض / Offer declined",
            "رفض المستأجر عرض السكن. / The renter declined the offer.",
        ),
    }
    if kind == "housing_request_status" and data.get("request_status") == "closed":
        return {
            "title": "سحب المستأجر طلبه / Request withdrawn",
            "body": "سحب المستأجر طلب السكن. يمكنك مراجعة عروضك في السجل. / The renter withdrew the request. Your offers remain in history.",
        }
    title, body = copy.get(
        kind,
        (
            "تحديث طلب السكن / Housing update",
            "افتح الطلب لمراجعة حالته الحالية. / Open the request to review its current state.",
        ),
    )
    return {"title": title, "body": body}
