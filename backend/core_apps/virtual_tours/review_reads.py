"""Prepare a review page with batched identity/security facts and cached histories."""

from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from .models import TourRevision, TourReviewEvent
from .review_access import reviewer
from .services import revision_payload
from .errors import require
from core_apps.users.totp_models import StaffSecurityIdentity
from core_apps.users.services.totp import pending_recovery


def queryset():
    return (
        TourRevision.objects.select_related(
            "tour__property", "tour__building", "tour__complex"
        )
        .select_related("capture_job")
        .prefetch_related(
            "variants",
            "assets",
            Prefetch(
                "reviews",
                queryset=TourReviewEvent.objects.order_by("created_at", "pk"),
                to_attr="prepared_reviews",
            ),
        )
        .order_by("-submitted_at", "-created_at")
    )


def projection(item, user, facts):
    target = item.tour.target
    can_review = (
        user.has_perm("virtual_tours.change_tourrevision")
        and facts["independent"][item.pk]
        and (item.review_state == "pending")
        and (item.processing_state == "ready")
        and (not item.tour.deleted)
        and (not user.sensitive_actions_frozen)
    )
    can_review = can_review and (not facts["pending_recovery"])
    return {
        **revision_payload(item),
        "asset_kind": item.tour.target_kind,
        "asset_id": str(target.id),
        "title": getattr(target, "title", getattr(target, "name", "")),
        "kind": item.tour.kind,
        "submitted_at": item.submitted_at,
        "can_review": can_review,
        "review_blocker": (
            ""
            if can_review
            else "يلزم مراجع مستقل بصلاحية حالية وإصدار جاهز بانتظار المراجعة وأمان حساب يسمح بالإجراء."
        ),
        "history": [
            {
                "decision": e.decision,
                "reason": e.reason,
                "public_reason": e.public_reason,
                "source_hash": e.source_hash,
                "created_at": e.created_at,
            }
            for e in item.prepared_reviews
        ],
    }


def prepare(items, user):
    owner_ids = {
        getattr(
            item.tour.target, "owner_id", getattr(item.tour.target, "manager_id", None)
        )
        for item in items
    }
    identities = dict(
        StaffSecurityIdentity.objects.filter(
            user_id__in=owner_ids | {user.pk}
        ).values_list("user_id", "person_reference")
    )
    facts = {"pending_recovery": pending_recovery(user), "independent": {}}
    for item in items:
        target = item.tour.target
        owner_id = getattr(target, "owner_id", getattr(target, "manager_id", None))
        facts["independent"][item.pk] = owner_id != user.pk and not (
            identities.get(owner_id)
            and identities.get(owner_id) == identities.get(user.pk)
        )
    return [projection(item, user, facts) for item in items]


def review_collection(actor, state="pending", page="1"):
    user = reviewer(actor)
    require(
        state in {"pending", "approved", "rejected", "all"},
        "invalid_state",
        "Choose a review state.",
    )
    require(
        page.isdigit() and 1 <= int(page) <= 100000,
        "invalid_page",
        "Choose a valid page.",
    )
    page = int(page)
    items = queryset().exclude(review_state="not_submitted")
    if state != "all":
        items = items.filter(review_state=state)
    count = items.count()
    start, end = (page - 1) * 20, page * 20
    return {
        "items": prepare(list(items[start:end]), user),
        "count": count,
        "page": page,
        "has_next": count > page * 20,
    }


def review_detail(actor, revision_id):
    user = reviewer(actor)
    return prepare([get_object_or_404(queryset(), id=revision_id)], user)[0]
