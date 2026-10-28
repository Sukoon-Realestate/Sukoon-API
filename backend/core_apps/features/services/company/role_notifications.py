"""Role-bound destinations and generic device copy for company work."""

from django.core.exceptions import ValidationError
from .role_context import available, system_context


def audience_current(user, data):
    from ...company_models import CompanyMembership

    try:
        member = (
            CompanyMembership.objects.filter(
                company__id=data.get("company_id"), user=user, is_active=True
            )
            .select_related("user", "company")
            .first()
        )
        return bool(member and data.get("company_role") in available(member))
    except (ValidationError, ValueError, TypeError):
        return False


def record(*, user, company, role, key, destination):
    from ...planning_models import PlanningEvent

    data = {**destination, "company_id": str(company.id), "company_role": role}
    with system_context():
        if data.get("workspace") == "company" and not audience_current(user, data):
            return
        PlanningEvent.objects.get_or_create(
            recipient=user, event_key=f"{key}:{role}", defaults={"destination": data}
        )


def push_content(notification):
    data = notification.data or {}
    if notification.scope != "company" and not (
        data.get("company_id") and notification.scope != "owner"
    ):
        return notification.title, notification.body, data
    # Never put amounts, document contents, or another person's details on the
    # lock screen. The destination revalidates current authority when opened.
    keys = {
        "action_type",
        "target_id",
        "company_id",
        "company_role",
        "schema_version",
        "workspace",
        "notification_id",
        "event_id",
    }
    return (
        "تحديث مهمة الشركة / Company task update",
        "افتح سكون لمراجعة مهمتك / Open Sukoon to review your task",
        {key: value for key, value in data.items() if key in keys},
    )
