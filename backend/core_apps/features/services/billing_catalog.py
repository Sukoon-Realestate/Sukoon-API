from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from ..models import AccountSubscription
from .purchase_routing import routing


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
        "period_months": plan.period_months,
        "amount_minor": plan.amount_minor,
        "currency": plan.currency,
        "exponent": plan.exponent,
    }


def plan_payload(plan, language):
    snapshot = plan_snapshot(plan)
    return {
        **snapshot,
        "name": snapshot[f"name_{language}"],
        "description": snapshot[f"description_{language}"],
        "active": plan.active,
        "purchase_routes": {
            platform: routing("subscription", platform, product_id=str(plan.id))
            for platform in ("ios", "android", "web")
        },
        "sort_order": plan.sort_order,
    }


def subscription_payload(subscription):
    if subscription is None:
        return None
    status = (
        "cancelled"
        if subscription.cancelled_at
        else "expired" if subscription.ends_at <= timezone.now() else "active"
    )
    return {
        "id": str(subscription.id),
        "plan_id": subscription.plan_snapshot["id"],
        "workspace": subscription.workspace,
        "status": status,
        "starts_at": subscription.starts_at.isoformat(),
        "ends_at": subscription.ends_at.isoformat(),
        "plan": subscription.plan_snapshot,
        "invoice_id": str(subscription.invoice.id),
    }


def current_subscription(user, workspace):
    return (
        AccountSubscription.objects.filter(user=user)
        .filter(Q(workspace=workspace) | Q(workspace="both"))
        .select_related("invoice")
        .order_by("-starts_at", "-created_at")
        .first()
    )


def subscription_summary(user):
    return {
        workspace: subscription_payload(current_subscription(user, workspace))
        for workspace in ("tenant", "owner")
    }
