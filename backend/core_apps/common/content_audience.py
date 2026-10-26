"""The old 'both' audience keeps its original two-space meaning."""

from django.db.models import Q
from rest_framework.exceptions import ValidationError


def workspace(value):
    value = "tenant" if value == "individual" else value
    if value not in {"tenant", "owner", "student", "company"}:
        raise ValidationError("Choose a supported application workspace.")
    return value


def audience(value):
    value = workspace(value)
    values = [value, "all"]
    if value in {"tenant", "owner"}:
        values.append("both")
    return Q(workspace__in=values)
