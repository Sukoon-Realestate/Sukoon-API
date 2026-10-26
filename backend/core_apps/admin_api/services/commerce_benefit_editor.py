"""Plan-first locking keeps edited benefits atomic with purchase snapshots."""

from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from core_apps.features.models import PlanBenefit, SubscriptionPlan
from core_apps.common.content_models import ContentEditAudit


def lock_plan(kind, identity, values):
    if kind != "plan_benefits":
        return None
    if identity:
        benefit = get_object_or_404(PlanBenefit, id=identity)
        return SubscriptionPlan.objects.select_for_update().get(pk=benefit.plan_id)
    plan_id = serializers.UUIDField().run_validation(values.get("plan"))
    return get_object_or_404(SubscriptionPlan.objects.select_for_update(), id=plan_id)


def changed(plan, benefit, actor, reason):
    if plan is None:
        return
    from .content_registry import projection

    before = projection("subscription_plans", plan)
    plan.revision += 1
    plan.save(update_fields=["revision", "updated_at"])
    after = projection("subscription_plans", plan)
    after["benefit_change"] = {"id": str(benefit.id), "revision": benefit.revision}
    ContentEditAudit.objects.create(
        kind="subscription_plans",
        object_id=str(plan.id),
        revision=plan.revision,
        actor=actor,
        reason=f"مراجعة مزايا الخطة — {reason}",
        before=before,
        after=after,
    )
