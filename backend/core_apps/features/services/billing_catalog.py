from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from ..models import AccountSubscription
from .purchase_routing import routing_v1 as routing


def workspace_for(value):
    if value not in {"tenant", "owner"}:
        raise ValidationError({"workspace": "Choose tenant or owner."})
    return value


def plan_snapshot(plan):
    return {
        "id": str(plan.id),
        "revision": plan.revision,
        "name_en": plan.name_en,
        "name_ar": plan.name_ar,
        "description_en": plan.description_en,
        "description_ar": plan.description_ar,
        "workspace": plan.workspace,
        "tier": plan.tier,
        "audience": plan.audience,
        "benefits": [
            {
                "code": b.feature.code,
                "included": b.included,
                "limit": b.limit,
                **{
                    f"{key}_{lang}": getattr(b.feature, f"{key}_{lang}")
                    for key in ("label", "description", "unit_label")
                    for lang in ("ar", "en")
                },
            }
            for b in plan.benefits.select_related("feature").filter(
                feature__available=True
            )
        ],
        "period_months": plan.period_months,
        "amount_minor": plan.amount_minor,
        "currency": plan.currency,
        "exponent": plan.exponent,
    }


def plan_payload(plan, language, *, user=None):
    snapshot = plan_snapshot(plan)
    routes = {
        platform: routing("subscription", platform, plan=plan, user=user)
        for platform in ("ios", "android", "web")
    }
    return {
        **snapshot,
        "name": snapshot[f"name_{language}"],
        "description": snapshot[f"description_{language}"],
        "active": plan.active,
        "renewal_mode": (
            "manual"
            if any(route.get("sandbox_only") for route in routes.values())
            else "auto_renew"
        ),
        "benefits": [
            {
                **{k: v for k, v in b.items() if not k.endswith(("_ar", "_en"))},
                **{
                    k: b[f"{k}_{language}"]
                    for k in ("label", "description", "unit_label")
                },
            }
            for b in snapshot["benefits"]
        ],
        "purchase_routes": routes,
        "sort_order": plan.sort_order,
    }


def subscription_status(subscription):
    status = subscription.store_status or (
        "expired" if subscription.ends_at <= timezone.now() else "active"
    )
    access_end = (
        subscription.grace_ends_at
        if status == "grace" and subscription.grace_ends_at
        else subscription.ends_at
    )
    if access_end <= timezone.now() and status not in {"revoked", "expired"}:
        status = "expired"
    return status


def subscription_payload(subscription):
    if subscription is None:
        return None
    status = subscription_status(subscription)
    return {
        "id": str(subscription.id),
        "plan_id": subscription.plan_snapshot["id"],
        "workspace": subscription.workspace,
        "organization_id": (
            str(subscription.organization.id) if subscription.organization_id else ""
        ),
        "status": status,
        "starts_at": subscription.starts_at.isoformat(),
        "ends_at": subscription.ends_at.isoformat(),
        "grace_ends_at": (
            subscription.grace_ends_at.isoformat()
            if subscription.grace_ends_at
            else None
        ),
        "plan": subscription.plan_snapshot,
        "invoice_id": str(subscription.invoice.id),
    }


def current_subscription(user, workspace, organization=None):
    return (
        AccountSubscription.objects.filter(
            **(
                {"organization": organization}
                if organization
                else {"user": user, "organization__isnull": True}
            )
        )
        .filter(Q(workspace=workspace) | Q(workspace="both"))
        .filter(starts_at__lte=timezone.now())
        .select_related("invoice", "organization")
        .order_by("-starts_at", "-created_at")
        .first()
    )


def subscription_summary(user):
    return {
        workspace: subscription_payload(current_subscription(user, workspace))
        for workspace in ("tenant", "owner")
    }
