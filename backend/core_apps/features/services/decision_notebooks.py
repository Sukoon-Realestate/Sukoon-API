"""Three-way private sync: independent edits merge, conflicting copies survive."""

import copy
import hashlib
import json

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from core_apps.users.models import User
from ..decision_models import (
    DecisionNotebook, DecisionNotebookVersion, DecisionNotebookConflict,
    DecisionNotebookOperation,
)
from .rental_phase2 import RentalConflict


def empty():
    return {"properties": [], "searches": [], "comparison_targets": []}


def record_key(kind, row):
    identity = [row["property_id"], row.get("offer_id", "")] if kind == "properties" else row["id"]
    return kind + ":" + json.dumps(identity, ensure_ascii=False, separators=(",", ":"))


def records(content):
    return {
        **{record_key(kind, row): row for kind in ("properties", "searches")
           for row in content.get(kind, [])},
        "comparison_targets": content.get("comparison_targets", []),
    }


def document(values):
    result = empty()
    for key, value in sorted(values.items()):
        if value is None:
            continue
        if key == "comparison_targets":
            result[key] = value
        else:
            result[key.split(":", 1)[0]].append(value)
    return result


def validate_content(content):
    # Protocol bounds only, not a paid plan or a new feature entitlement.
    if not isinstance(content, dict) or set(content) != set(empty()):
        raise ValidationError("A complete notebook is required.")
    if len(json.dumps(content).encode()) > 512_000:
        raise ValidationError("The notebook exceeds the sync request limit.")
    for kind in ("properties", "searches"):
        rows = content[kind]
        if not isinstance(rows, list) or len(rows) > 1000:
            raise ValidationError("Invalid notebook collection.")
        keys = set()
        for row in rows:
            identity = "property_id" if kind == "properties" else "id"
            if not isinstance(row, dict) or not isinstance(row.get(identity), str) or not row[identity]:
                raise ValidationError("A stable note or search identity is required.")
            allowed = ({"property_id", "offer_id", "title", "list", "note", "checked_items", "selection"}
                       if kind == "properties" else {"id", "name", "filters"})
            if set(row) - allowed:
                raise ValidationError("Unknown notebook fields.")
            for field in (allowed - {"checked_items", "selection", "filters"}):
                if field in row and not isinstance(row[field], str):
                    raise ValidationError("Notebook text must be a string.")
            if kind == "properties":
                checks = row.get("checked_items", [])
                if not isinstance(checks, list) or any(not isinstance(v, str) for v in checks):
                    raise ValidationError("Invalid checklist.")
                if row.get("selection") is not None and not isinstance(row["selection"], dict):
                    raise ValidationError("Invalid accommodation snapshot.")
            elif not isinstance(row.get("filters"), dict):
                raise ValidationError("Invalid saved search.")
            key = record_key(kind, row)
            if key in keys:
                raise ValidationError("Duplicate notebook identity.")
            keys.add(key)
    targets = content["comparison_targets"]
    if not isinstance(targets, list) or len(targets) > 3:
        raise ValidationError("Select at most three comparison targets.")
    for target in targets:
        if (not isinstance(target, dict) or set(target) - {"property_id", "offer_id"}
                or not isinstance(target.get("property_id"), str) or not target["property_id"]
                or not isinstance(target.get("offer_id", ""), str)):
            raise ValidationError("Invalid comparison target.")
    return content


def authorize(user, workspace, company_context, *, lock=False):
    if not user.is_active or user.closed_at or not user.is_verified:
        raise PermissionDenied("A verified active account is required.")
    if workspace not in {"individual", "owner", "student", "company"}:
        raise ValidationError("Unknown notebook workspace.")
    if workspace == "company":
        from .company.access import company_for
        if not company_context:
            raise ValidationError("Choose a company first.")
        company_for(user, company_context, lock=lock)
    elif company_context:
        raise ValidationError("Company context does not match this workspace.")


def payload(notebook):
    return {
        "workspace": notebook.workspace,
        "company_id": notebook.company_context,
        "revision": notebook.revision,
        "content": notebook.content or empty(),
        "conflicts": [{
            "id": str(row.id), "record_key": row.record_key,
            "base": row.base, "current": row.current, "incoming": row.incoming,
            "fields": row.fields, "revision": row.revision,
            "resolved": row.resolved_at is not None, "resolution": row.resolution,
        } for row in DecisionNotebookConflict.objects.filter(notebook=notebook).order_by("created_at", "pk")],
    }


def read(user, workspace, company_context):
    authorize(user, workspace, company_context)
    notebook = DecisionNotebook.objects.filter(
        user=user, workspace=workspace, company_context=company_context,
    ).first()
    return payload(notebook) if notebook else {
        "workspace": workspace, "company_id": company_context,
        "revision": 0, "content": empty(), "conflicts": [],
    }


def merge(notebook, base, incoming, base_revision):
    base, incoming, current = records(base), records(incoming), records(notebook.content)
    result = copy.deepcopy(current)
    for key in sorted(set(base) | set(incoming)):
        old, new, now = base.get(key), incoming.get(key), current.get(key)
        if new == old:
            continue
        conflicts = []
        deleted_revision = notebook.tombstones.get(key, 0)
        if new is None:
            result.pop(key, None)
            notebook.tombstones[key] = notebook.revision + 1
            if now not in (old, None):
                conflicts = ["deleted"]
        elif deleted_revision > base_revision:
            # Even an old device that missed the entire item lifetime cannot
            # resurrect it. Keep its text as a conflict copy for the owner.
            conflicts = ["deleted"]
        elif now == old or new == now:
            result[key] = new
        elif isinstance(old, dict) and isinstance(now, dict) and isinstance(new, dict):
            merged = copy.deepcopy(now)
            for field in sorted(set(old) | set(new)):
                if new.get(field) == old.get(field):
                    continue
                if now.get(field) in (old.get(field), new.get(field)):
                    if field in new:
                        merged[field] = new[field]
                    else:
                        merged.pop(field, None)
                else:
                    conflicts.append(field)
            result[key] = merged
        else:
            conflicts = ["content"]
        if conflicts:
            DecisionNotebookConflict.objects.create(
                notebook=notebook, record_key=key, base=old,
                current=now, incoming=new, fields=conflicts,
                revision=notebook.revision + 1,
            )
    return document(result)


@transaction.atomic
def write(user, workspace, company_context, operation):
    # Account closure takes this same root before erasing private notes.
    user = User.objects.select_for_update().get(pk=user.pk)
    authorize(user, workspace, company_context, lock=True)
    notebook, _ = DecisionNotebook.objects.get_or_create(
        user=user, workspace=workspace, company_context=company_context,
        defaults={"content": empty()},
    )
    fingerprint = hashlib.sha256(json.dumps(operation, sort_keys=True, default=str).encode()).hexdigest()
    receipt = DecisionNotebookOperation.objects.filter(
        notebook=notebook, operation_id=operation["operation_id"],
    ).first()
    if receipt:
        if receipt.fingerprint != fingerprint:
            raise RentalConflict("This sync identity has different content.", code="idempotency_conflict")
        return {**payload(notebook), "operation_id": str(receipt.operation_id)}
    base_revision = operation["base_revision"]
    if base_revision > notebook.revision:
        raise RentalConflict("Reload the current notebook.", code="revision_conflict")
    if operation.get("conflict_id"):
        if base_revision != notebook.revision:
            raise RentalConflict("Review the current notebook before resolving.", code="revision_conflict")
        conflict = get_object_or_404(DecisionNotebookConflict, notebook=notebook, id=operation["conflict_id"])
        if conflict.resolved_at:
            raise RentalConflict("This conflict has already been reviewed.", code="revision_conflict")
        if operation["resolution"] == "incoming":
            if "deleted" in conflict.fields or notebook.tombstones.get(conflict.record_key, 0) > conflict.revision:
                raise RentalConflict("Deleted notes cannot be restored by stale sync.", code="note_deleted")
            values = records(notebook.content)
            current = values.get(conflict.record_key)
            if isinstance(current, dict) and isinstance(conflict.incoming, dict) and "content" not in conflict.fields:
                for field in conflict.fields:
                    if field in conflict.incoming:
                        current[field] = conflict.incoming[field]
                    else:
                        current.pop(field, None)
            else:
                values[conflict.record_key] = conflict.incoming
            notebook.content = validate_content(document(values))
        conflict.resolved_at = timezone.now()
        conflict.resolution = operation["resolution"]
        conflict.save(update_fields=["resolved_at", "resolution"])
    else:
        incoming = validate_content(operation["content"])
        base = empty() if base_revision == 0 else get_object_or_404(
            DecisionNotebookVersion, notebook=notebook, revision=base_revision,
        ).content
        notebook.content = merge(notebook, base, incoming, base_revision)
    notebook.revision += 1
    notebook.save(update_fields=["revision", "content", "tombstones"])
    DecisionNotebookVersion.objects.create(
        notebook=notebook, revision=notebook.revision, content=notebook.content,
    )
    DecisionNotebookOperation.objects.create(
        notebook=notebook, operation_id=operation["operation_id"],
        fingerprint=fingerprint, revision=notebook.revision,
    )
    return {**payload(notebook), "operation_id": str(operation["operation_id"])}
