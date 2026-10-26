"""One persisted recipient scope per receipt, independent of account type."""

from rest_framework.exceptions import ValidationError

WORKSPACES = frozenset({"individual", "owner", "student", "company"})
SCOPES = WORKSPACES | {"account"}


def canonical_scope(data, notification_type="general"):
    data = data or {}
    if data.get("scope") == "account" or notification_type in {
        "security_alert",
        "account_verification",
    }:
        return "account"
    for key in ("workspace", "presentation_workspace", "scope"):
        value = data.get(key)
        if value == "tenant":
            return "individual"
        if value in WORKSPACES:
            return value
    if data.get("academic_plan_id") or data.get("student_plan_id"):
        return "student"
    if str(data.get("action_type", "")).startswith("open_company_"):
        return "company"
    # These types identify the recipient role, unlike general property changes.
    if notification_type in {
        "property_verified",
        "property_views",
        "daily_bump",
        "visit_request",
    }:
        return "owner"
    if notification_type == "new_property":
        return "individual"
    # Preserve an old receipt with missing context in account history. Never
    # duplicate it into every workspace or infer authority from account type.
    return "account"


def request_scope(request):
    value = request.query_params.get("scope", "workspace")
    if value == "workspace":
        value = request.query_params.get("workspace", "individual")
    if value == "tenant":
        value = "individual"
    if value not in SCOPES:
        raise ValidationError({"scope": "Choose account or a supported workspace."})
    return value


def filter_scope(queryset, scope):
    return queryset.filter(scope=scope) if scope else queryset


def is_account_event(notification):
    return notification.scope == "account"


def receipt_data(notification):
    data = dict(notification.data or {})
    if notification.scope == "account":
        data["scope"] = "account"
        data.pop("workspace", None)
        data.pop("presentation_workspace", None)
    else:
        data.update(
            scope="workspace",
            workspace=notification.scope,
            presentation_workspace=notification.scope,
        )
    return data
