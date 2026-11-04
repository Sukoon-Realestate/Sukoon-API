"""Thirty-day saved-search comparison with explicit successful-render receipts."""

from datetime import timedelta
from hashlib import sha256
from django.db import transaction
from django.db.models import Case, When, Value, CharField
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import (
    ValidationError,
    NotAuthenticated,
    APIException,
    PermissionDenied,
)
from core_apps.common.idempotency import fingerprint, IdempotencyConflict
from core_apps.users.models import User
from ..models import SavedSearchVisit, SavedSearchRead


class SearchReadExpired(APIException):
    status_code = 410
    default_detail = "Search snapshot expired. Refresh the saved search."
    default_code = "saved_search_read_expired"


def definition(query):
    excluded = {
        "page",
        "page_size",
        "ordering",
        "saved_search_id",
        "saved_search_workspace",
        "saved_search_read_id",
        "new_updated_only",
        "saved_search_name",
        "name",
    }
    return fingerprint(
        {key: query.getlist(key) for key in sorted(query) if key not in excluded}
    )


def version(prop):
    return [prop.review_revision, prop.updated_at.isoformat()]


def apply_saved_search_read(queryset, request):
    identity = request.query_params.get("saved_search_id")
    if not identity:
        return queryset
    if not request.user.is_authenticated:
        raise NotAuthenticated()
    workspace = request.query_params.get("saved_search_workspace", "individual")
    if workspace not in {"individual", "owner"} or len(identity) > 4096:
        raise ValidationError("Choose an individual or owner saved search.")
    digest = definition(request.query_params)
    identity_hash = sha256(identity.encode()).hexdigest()
    now = timezone.now()
    read_id = request.query_params.get("saved_search_read_id")
    if read_id:
        from rest_framework import serializers

        read_id = serializers.UUIDField().run_validation(read_id)
        snapshot = get_object_or_404(
            SavedSearchRead.objects.select_related("visit"),
            id=read_id,
            visit__user=request.user,
            visit__workspace=workspace,
            visit__identity_hash=identity_hash,
        )
        if snapshot.expires_at <= now:
            raise SearchReadExpired()
        if snapshot.definition_hash != digest:
            raise IdempotencyConflict("Search definition changed. Refresh the search.")
    else:
        with transaction.atomic():
            actor = User.objects.select_for_update().get(pk=request.user.pk)
            if not actor.is_active or actor.closed_at:
                raise PermissionDenied()
            if request.auth:
                from core_apps.users.services.sessions import validate_session

                validate_session(actor, request.auth)
            visit, _ = SavedSearchVisit.objects.get_or_create(
                user=request.user,
                workspace=workspace,
                identity_hash=identity_hash,
                defaults={"identity": identity, "definition_hash": digest},
            )
            visit = SavedSearchVisit.objects.select_for_update().get(pk=visit.pk)
            baseline = "available"
            if visit.definition_hash != digest:
                visit.definition_hash = digest
                visit.versions = {}
                visit.last_read_at = None
                visit.revision += 1
                visit.save(
                    update_fields=[
                        "definition_hash",
                        "versions",
                        "last_read_at",
                        "revision",
                        "updated_at",
                    ]
                )
                baseline = "definition_changed"
            elif visit.last_read_at is None:
                baseline = "first_visit"
            elif visit.last_read_at < now - timedelta(days=30):
                baseline = "window_expired"
            values = {
                str(pk): [revision, modified.isoformat()]
                for pk, revision, modified in queryset.values_list(
                    "id", "review_revision", "updated_at"
                )
                .distinct()
                .iterator(chunk_size=500)
            }
            changes = (
                {}
                if baseline != "available"
                else {
                    key: "new" if key not in visit.versions else "updated"
                    for key, value in values.items()
                    if visit.versions.get(key) != value
                }
            )
            snapshot = SavedSearchRead.objects.create(
                visit=visit,
                definition_hash=digest,
                base_revision=visit.revision,
                versions=values,
                changes=changes,
                baseline_state=baseline,
                read_at=now,
                expires_at=now + timedelta(minutes=15),
            )
    # A snapshot never bypasses present filters, hidden preferences or access.
    queryset = queryset.filter(id__in=snapshot.versions)
    new = [key for key, kind in snapshot.changes.items() if kind == "new"]
    updated = [key for key, kind in snapshot.changes.items() if kind == "updated"]
    request.saved_search_metadata = {
        "read_id": str(snapshot.id),
        "read_at": snapshot.read_at.isoformat(),
        "baseline_state": snapshot.baseline_state,
        "new_count": queryset.filter(id__in=new).count(),
        "updated_count": queryset.filter(id__in=updated).count(),
        "acknowledged": snapshot.acknowledged_at is not None,
    }
    request.saved_search_snapshot = snapshot
    if (
        request.query_params.get("new_updated_only") == "true"
        and snapshot.baseline_state == "available"
    ):
        queryset = queryset.filter(id__in=snapshot.changes)
    return queryset.annotate(
        saved_search_change=Case(
            When(id__in=new, then=Value("new")),
            When(id__in=updated, then=Value("updated")),
            default=Value(None),
            output_field=CharField(),
        )
    )


def validate_page(page, request):
    snapshot = getattr(request, "saved_search_snapshot", None)
    if snapshot is not None:
        for prop in page:
            if snapshot.versions.get(str(prop.id)) != version(prop):
                raise IdempotencyConflict(
                    "Listing changed during this read. Refresh the saved search."
                )
    return page


@transaction.atomic
def acknowledge(user, read_id, auth_claims=None):
    actor = User.objects.select_for_update().get(pk=user.pk)
    if not actor.is_active or actor.closed_at:
        raise PermissionDenied()
    if auth_claims:
        from core_apps.users.services.sessions import validate_session

        validate_session(actor, auth_claims)
    snapshot = get_object_or_404(
        SavedSearchRead.objects.select_for_update().select_related("visit"),
        id=read_id,
        visit__user=user,
    )
    visit = SavedSearchVisit.objects.select_for_update().get(pk=snapshot.visit_id)
    if snapshot.acknowledged_at is not None:
        return {"read_id": str(snapshot.id), "acknowledged": True}
    if snapshot.expires_at <= timezone.now():
        raise SearchReadExpired()
    if (
        visit.definition_hash != snapshot.definition_hash
        or visit.revision != snapshot.base_revision
    ):
        raise IdempotencyConflict(
            "A newer saved-search read exists. Refresh before marking it read."
        )
    visit.versions = snapshot.versions
    visit.last_read_at = snapshot.read_at
    visit.revision += 1
    visit.save(update_fields=["versions", "last_read_at", "revision", "updated_at"])
    snapshot.acknowledged_at = timezone.now()
    snapshot.save(update_fields=["acknowledged_at", "updated_at"])
    return {"read_id": str(snapshot.id), "acknowledged": True}
