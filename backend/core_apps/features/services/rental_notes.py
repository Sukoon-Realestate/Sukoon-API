"""Persist participant response explanations without changing financial data."""

from rest_framework.exceptions import ValidationError

from ..models import RentalTimelineEvent


def validated_note(data):
    value = data.get("note", "")
    if not isinstance(value, str) or len(value) > 4000:
        raise ValidationError({"note": "Use text of at most 4000 characters."})
    return value.strip()


def record_response_note(item, user, kind, action, note):
    if not note:
        return
    RentalTimelineEvent.objects.create(
        lease=item.lease,
        actor=user,
        kind=f"{kind}_{action}_note",
        label=f"{kind.replace('_', ' ').title()} response: {action.replace('_', ' ')}",
        description=note,
        resource_id=item.id,
    )


def response_note_label(event, language):
    if not language.lower().startswith("ar"):
        return event.label
    for prefix, subject in (
        ("handover_", "محضر التسليم"),
        ("change_", "طلب تعديل العقد"),
    ):
        if event.kind.startswith(prefix) and event.kind.endswith("_note"):
            action = event.kind[len(prefix) : -len("_note")]
            label = {
                "accept": "موافقة",
                "dispute": "اعتراض",
                "reject": "رفض",
                "request_changes": "طلب تعديلات",
            }.get(action)
            if label:
                return f"{subject}: {label}"
    return event.label
