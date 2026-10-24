"""Server access decisions; existing actions remain open until explicit rollout."""

from datetime import timedelta
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from ..models import CommerceFeature, EntitlementGrant, SearchAlert
from .billing_catalog import current_subscription, workspace_for
from .rental_phase2 import RentalConflict


def decision(user, feature_code, workspace, organization=None):
    workspace_for(workspace)
    feature = CommerceFeature.objects.filter(
        code=feature_code, workspace=workspace
    ).first()
    now = timezone.now()
    result = {
        "contract_version": 1,
        "account_id": str(user.id),
        "workspace": workspace,
        "organization_id": str(organization.id) if organization else "",
        "feature": feature_code,
        "allowed": False,
        "source": "",
        "used": 0,
        "limit": None,
        "message": "",
        "valid_until": (now + timedelta(minutes=5)).isoformat(),
    }
    if feature is None:
        raise ValidationError({"feature": "Unknown feature for this workspace."})
    if not user.is_active or not feature.available:
        result["message"] = "This feature is unavailable."
        return result
    candidates = []
    if feature.free:
        candidates.append(("free", feature.free_limit, None))
    subject = (
        {"organization": organization}
        if organization
        else {"user": user, "organization__isnull": True}
    )
    for grant in EntitlementGrant.objects.filter(
        feature=feature, starts_at__lte=now, revoked_at__isnull=True, **subject
    ).filter(Q(ends_at__isnull=True) | Q(ends_at__gt=now)):
        candidates.append((grant.source, grant.limit, grant.ends_at))
    subscription = current_subscription(user, workspace, organization)
    access_end = (
        subscription.grace_ends_at
        if subscription
        and subscription.store_status == "grace"
        and subscription.grace_ends_at
        else subscription.ends_at if subscription else None
    )
    if (
        subscription
        and subscription.starts_at <= now < access_end
        and subscription.store_status
        not in {"expired", "revoked", "hold", "billing_retry"}
    ):
        for benefit in subscription.plan_snapshot.get("benefits", []):
            if benefit["code"] == feature_code and benefit["included"]:
                candidates.append(("subscription", benefit.get("limit"), access_end))
    if candidates:
        source, limit, end = max(
            candidates, key=lambda x: float("inf") if x[1] is None else x[1]
        )
        result.update(allowed=True, source=source, limit=limit)
        if end:
            result["valid_until"] = min(now + timedelta(minutes=5), end).isoformat()
    if feature_code == "priority_alerts" and organization is None:
        result["used"] = SearchAlert.objects.filter(
            user=user, cadence="instant", enabled=True, deleted_at__isnull=True
        ).count()
    if result["limit"] is not None and result["used"] >= result["limit"]:
        result.update(allowed=False, message="The feature quota is exhausted.")
    if not result["allowed"] and not result["message"]:
        result["message"] = "An entitlement is required."
    return result


def enforce(user, code, workspace):
    feature = CommerceFeature.objects.filter(code=code, enforced=True).first()
    if not getattr(settings, "COMMERCE_ENTITLEMENTS_ENABLED", False) or feature is None:
        return
    value = decision(user, code, workspace)
    if not value["allowed"]:
        if (
            value["source"]
            and value["limit"] is not None
            and value["used"] >= value["limit"]
        ):
            raise RentalConflict(
                "The feature quota is exhausted.", code="quota_exceeded"
            )
        raise PermissionDenied(
            {"message": value["message"], "code": "entitlement_required"}
        )
