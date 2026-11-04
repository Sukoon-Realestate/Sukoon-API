from rest_framework.exceptions import ValidationError, PermissionDenied
from core_apps.support.models import Ticket


def normalize_workspace(value):
    value = "tenant" if value == "individual" else str(value).lower()
    if value not in Ticket.Workspace.values:
        raise ValidationError(
            {"workspace": "Choose a supported account or workspace context."}
        )
    from core_apps.common.mvp_scope import enabled
    if enabled() and value in {'student', 'company'}:
        raise PermissionDenied('This support workspace is deferred for the MVP release.')
    return value
