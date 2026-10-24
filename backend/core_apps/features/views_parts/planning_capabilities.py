"""Views: planning capabilities."""

from ..catalog_models import PromotionOption
from datetime import timedelta
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from ..renderers import FeatureJsonRenderer
from ..services.tenancy_invitations import localized
from ..services.rental_foundation import private_no_store


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def configuration(request):
    workspace = request.query_params.get("workspace")
    lang = request.query_params.get("lang", "en")
    if workspace not in {"owner", "tenant"}:
        raise ValidationError({"workspace": "Must be owner or tenant."})
    options = []
    if workspace == "owner":
        options = [
            {
                "id": value.id,
                "title": value.title_ar if lang == "ar" else value.title_en,
                "duration_days": value.duration_days,
                "revision": value.revision,
            }
            for value in PromotionOption.objects.filter(active=True)
        ]
    return Response(
        {
            "workspace": workspace,
            "boost_options": options,
            "alert_cadences": ["instant", "daily"] if workspace == "tenant" else [],
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
@renderer_classes([FeatureJsonRenderer])
def planning_capabilities(request):
    from ..services.planning import enabled_services
    from ..services.planning_providers import ready_services, configuration
    from ..services.planning_access import planning_actions

    user = request.user
    authenticated = bool(user and user.is_authenticated)
    verified = bool(authenticated and user.is_active and user.is_verified)
    enabled = enabled_services() if verified else []
    ready = ready_services(enabled)
    capability = request.query_params.get("capability", "")
    requested_action = request.query_params.get("action", "")
    subject_id = request.query_params.get("subject_id", "")
    privacy_actions = []
    if (
        verified
        and ((capability == "shared_living_lab" and requested_action == "withdraw") or
             (capability == "shared_housing_plans" and requested_action in {"withdraw", "decline_invite", "unpublish"}))
        and subject_id
    ):
        # Turning off creation never prevents an entitled participant from
        # withdrawing their own private requirements. Scope stays exact.
        if requested_action in planning_actions(user, capability, subject_id):
            privacy_actions = [requested_action]
    allowed = (
        planning_actions(user, capability, subject_id)
        if capability in ready
        else privacy_actions
    )
    if requested_action:
        allowed = [requested_action] if requested_action in allowed else []
    reasons = []
    if not authenticated:
        reasons.append(
            localized(
                request,
                "Authentication is required for planning services.",
                "تسجيل الدخول مطلوب لخدمات التخطيط.",
            )
        )
    elif not verified:
        reasons.append(
            localized(
                request,
                "A verified active account is required.",
                "يلزم حساب نشط وموثق.",
            )
        )
    elif privacy_actions:
        pass
    elif not enabled:
        reasons.append(
            localized(
                request,
                "Planning services are disabled in this environment.",
                "خدمات التخطيط غير مفعلة في هذه البيئة.",
            )
        )
    elif capability and capability not in enabled:
        reasons.append(
            localized(
                request,
                "This planning service is disabled in this environment.",
                "هذه الخدمة غير مفعلة في هذه البيئة.",
            )
        )
    elif capability and capability not in ready:
        reasons.append(
            localized(
                request,
                "This service is awaiting setup.",
                "هذه الخدمة في انتظار استكمال الإعداد.",
            )
        )
    elif capability and not allowed:
        reasons.append(
            localized(
                request,
                "This action is not available for the current account or resource.",
                "هذا الإجراء غير متاح للحساب أو المورد الحالي.",
            )
        )
    response = Response(
        {
            "account_id": str(user.id) if authenticated else None,
            "account_verified": verified,
            "enabled_capabilities": enabled,
            "verified_services": ready,
            "configuration": configuration(),
            "policy_version": "planning-policy-v1",
            "allowed_actions": allowed,
            "privacy_actions": privacy_actions,
            "privacy_subject_id": subject_id if privacy_actions else "",
            "expires_at": (
                (timezone.now() + timedelta(minutes=5)).isoformat()
                if enabled or privacy_actions
                else None
            ),
            "blocking_reasons": reasons,
        }
    )
    response["Content-Language"] = (
        "ar" if localized(request, "en", "ar") == "ar" else "en"
    )
    response["Vary"] = "Accept-Language"
    return private_no_store(response)
