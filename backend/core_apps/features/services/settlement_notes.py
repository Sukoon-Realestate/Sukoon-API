"""Revision-bound settlement comments stored alongside existing history."""

from django.utils import timezone
from .rental_notes import validated_note


def remember_note(item, user, action, note, request_key):
    if not note:
        return
    # Preserve the existing history row shape and financial snapshots. Notes
    # extend the current proposal's history row rather than rewriting its lines.
    history = list(item.history)
    if not history:
        history.append(
            {
                "revision": item.revision,
                "status": item.status,
                "lines": item.lines,
                "accepted_by": item.accepted_by,
                "disputed_item_ids": item.disputed_item_ids,
            }
        )
    current = dict(history[-1])
    current["notes"] = [
        *current.get("notes", []),
        {
            "id": request_key,
            "revision": item.revision,
            "action": action,
            "actor_id": str(user.id),
            "actor_role": "owner" if user.pk == item.lease.owner_id else "tenant",
            "note": note,
            "created_at": timezone.now().isoformat(),
        },
    ]
    history[-1] = current
    item.history = history


def notes_payload(item):
    # Actor identity is retained in history for auditing; the detail view needs
    # only the participant role. Old histories simply yield an empty list.
    return [
        {key: value for key, value in note.items() if key != "actor_id"}
        for revision in item.history
        if isinstance(revision, dict)
        for note in revision.get("notes", [])
        if isinstance(note, dict)
    ]


def history_payload(item):
    # Preserve the established public financial history shape. The new notes
    # live in their own projection; actor IDs remain in stored audit metadata.
    return [
        (
            {key: value for key, value in revision.items() if key != "notes"}
            if isinstance(revision, dict)
            else revision
        )
        for revision in item.history
    ]
