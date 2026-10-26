from rest_framework.exceptions import ValidationError
from core_apps.support.models import Ticket


def normalize_workspace(value):
    value = "tenant" if value == "individual" else str(value).lower()
    if value not in Ticket.Workspace.values:
        raise ValidationError(
            {"workspace": "Choose a supported account or workspace context."}
        )
    return value
