"""Thirty-day saved-search comparison with explicit successful-render receipts."""

from datetime import timedelta
from hashlib import sha256
from django.conf import settings
from django.db import transaction
from django.db.models import Case, When, Value, CharField, Exists, OuterRef, Subquery
from django.db.models.functions import NullIf
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
from ..models import SavedSearchVisit, SavedSearchRead, SavedSearchReadItem


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
    return fingerprint({key: query.getlist(key) for key in sorted(query) if key not in excluded})


def version(prop):
    return [prop.review_revision, prop.updated_at.isoformat()]


def _locked_actor(request):
    actor = User.objects.select_for_update().get(pk=request.user.pk)
    if not actor.is_active or actor.closed_at:
        raise PermissionDenied()
    if request.auth:
        from core_apps.users.services.sessions import validate_session

        validate_session(actor, request.auth)
    return actor


def snapshot_values(queryset):
    """Legacy complete snapshot; materialize outside the shared account lock."""
    return {
        str(pk): [revision, modified.isoformat()]
        for pk, revision, modified in queryset.values_list("id", "review_revision", "updated_at")
        .distinct()
        .iterator(chunk_size=500)
    }


def _create_snapshot(queryset, request, workspace, identity_hash, identity, digest, now):
    from .saved_search_items import baseline_read, versions, write_items

    itemized = getattr(settings, "SAVED_SEARCH_ITEMIZED_READS", False)
    with transaction.atomic():
        actor = _locked_actor(request)
        visit, _ = SavedSearchVisit.objects.get_or_create(
            user=actor,
            workspace=workspace,
            identity_hash=identity_hash,
            defaults={"identity": identity, "definition_hash": digest},
        )
        visit = (
            SavedSearchVisit.objects.select_for_update(of=("self",))
            .select_related("acknowledged_read")
            .only(
                "pk",
                "revision",
                "definition_hash",
                "last_read_at",
                "versions",
                "acknowledged_read",
                "acknowledged_read__pkid",
                "acknowledged_read__itemized",
                "acknowledged_read__items_ready",
                "acknowledged_read__acknowledged_at",
                "acknowledged_read__base_revision",
                "acknowledged_read__definition_hash",
            )
            .get(pk=visit.pk)
        )
        observed_revision, observed_definition = visit.revision, visit.definition_hash
        changed_definition = observed_definition != digest
        baseline = (
            "definition_changed"
            if changed_definition
            else (
                "first_visit"
                if visit.last_read_at is None
                else "window_expired" if visit.last_read_at < now - timedelta(days=30) else "available"
            )
        )
        prior = baseline_read(visit) if baseline == "available" else None
        previous = visit.versions if baseline == "available" and prior is None else {}
        visit_pk = visit.pk
        snapshot = (
            SavedSearchRead.objects.create(
                visit=visit,
                definition_hash=digest,
                base_revision=observed_revision + int(changed_definition),
                baseline_state=baseline,
                read_at=now,
                expires_at=now + timedelta(minutes=15),
                itemized=True,
                items_ready=False,
            )
            if itemized
            else None
        )
    if itemized:
        write_items(snapshot, queryset, previous_read=prior.pk if prior else None, previous=previous)
    else:
        if prior:
            previous = versions(prior)
        values = snapshot_values(queryset)
        changes = (
            {}
            if baseline != "available"
            else {
                key: "new" if key not in previous else "updated"
                for key, value in values.items()
                if previous.get(key) != value
            }
        )
    with transaction.atomic():
        _locked_actor(request)
        current = (
            SavedSearchVisit.objects.select_for_update().only("pk", "revision", "definition_hash").get(pk=visit_pk)
        )
        if current.revision != observed_revision or current.definition_hash != observed_definition:
            raise IdempotencyConflict("A newer saved-search read exists. Refresh before continuing.")
        if snapshot and snapshot.expires_at <= timezone.now():
            raise SearchReadExpired()
        if changed_definition:
            current.definition_hash, current.versions, current.last_read_at = digest, {}, None
            current.acknowledged_read_id = None
            current.revision += 1
            current.save(
                update_fields=[
                    "definition_hash",
                    "versions",
                    "last_read_at",
                    "acknowledged_read",
                    "revision",
                    "updated_at",
                ]
            )
        if snapshot:
            snapshot.items_ready = True
            snapshot.save(update_fields=["items_ready"])
            return snapshot
        return SavedSearchRead.objects.create(
            visit=current,
            definition_hash=digest,
            base_revision=current.revision,
            versions=values,
            changes=changes,
            baseline_state=baseline,
            read_at=now,
            expires_at=now + timedelta(minutes=15),
            itemized=False,
            items_ready=True,
        )


def _itemized_query(queryset, snapshot, request):
    member = SavedSearchReadItem.objects.filter(read=snapshot, property_identity=OuterRef("id"))
    queryset = queryset.filter(Exists(member)).annotate(
        saved_search_change=NullIf(Subquery(member.values("change")[:1]), Value(""))
    )
    request.saved_search_snapshot = snapshot
    request.saved_search_metadata = {
        "read_id": str(snapshot.id),
        "read_at": snapshot.read_at.isoformat(),
        "baseline_state": snapshot.baseline_state,
        "new_count": queryset.filter(saved_search_change="new").count(),
        "updated_count": queryset.filter(saved_search_change="updated").count(),
        "acknowledged": snapshot.acknowledged_at is not None,
    }
    if request.query_params.get("new_updated_only") == "true" and snapshot.baseline_state == "available":
        queryset = queryset.filter(saved_search_change__isnull=False)
    return queryset


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
            SavedSearchRead.objects.all(),
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
        snapshot = _create_snapshot(queryset, request, workspace, identity_hash, identity, digest, now)
    if snapshot.itemized:
        if not snapshot.items_ready:
            raise IdempotencyConflict("The saved-search snapshot is not complete. Refresh the search.")
        return _itemized_query(queryset, snapshot, request)
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
    if request.query_params.get("new_updated_only") == "true" and snapshot.baseline_state == "available":
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
        if snapshot.itemized:
            rows = list(page)
            facts = {
                str(item.property_identity): item
                for item in SavedSearchReadItem.objects.filter(
                    read=snapshot, property_identity__in=[row.id for row in rows]
                )
            }
            request.saved_search_page_changes = {key: item.change for key, item in facts.items() if item.change}
            for prop in rows:
                item = facts.get(str(prop.id))
                if item is None or item.review_revision != prop.review_revision or item.modified_at != prop.updated_at:
                    raise IdempotencyConflict("Listing changed during this read. Refresh the saved search.")
        else:
            for prop in page:
                if snapshot.versions.get(str(prop.id)) != version(prop):
                    raise IdempotencyConflict("Listing changed during this read. Refresh the saved search.")
    return page


def changes_for_page(request, identities):
    identities = [str(value) for value in identities]
    snapshot = request.saved_search_snapshot
    if not snapshot.itemized:
        return {key: snapshot.changes[key] for key in identities if key in snapshot.changes}
    prepared = getattr(request, "saved_search_page_changes", None)
    if prepared is not None:
        return {key: prepared[key] for key in identities if key in prepared}
    return {
        str(identity): change
        for identity, change in snapshot.items.filter(property_identity__in=identities)
        .exclude(change="")
        .values_list("property_identity", "change")
    }


@transaction.atomic
def acknowledge(user, read_id, auth_claims=None):
    actor = User.objects.select_for_update().get(pk=user.pk)
    if not actor.is_active or actor.closed_at:
        raise PermissionDenied()
    if auth_claims:
        from core_apps.users.services.sessions import validate_session

        validate_session(actor, auth_claims)
    snapshot = get_object_or_404(
        SavedSearchRead.objects.select_for_update(of=("self",)).defer("versions", "changes"),
        id=read_id,
        visit__user=user,
    )
    visit = (
        SavedSearchVisit.objects.select_for_update().only("pk", "definition_hash", "revision").get(pk=snapshot.visit_id)
    )
    if snapshot.itemized and not snapshot.items_ready:
        raise IdempotencyConflict("The saved-search snapshot is not complete. Refresh the search.")
    if snapshot.acknowledged_at is not None:
        return {"read_id": str(snapshot.id), "acknowledged": True}
    if snapshot.expires_at <= timezone.now():
        raise SearchReadExpired()
    if visit.definition_hash != snapshot.definition_hash or visit.revision != snapshot.base_revision:
        raise IdempotencyConflict("A newer saved-search read exists. Refresh before marking it read.")
    visit.versions = {} if snapshot.itemized else snapshot.versions
    visit.acknowledged_read = snapshot if snapshot.itemized else None
    visit.last_read_at = snapshot.read_at
    visit.revision += 1
    visit.save(update_fields=["versions", "acknowledged_read", "last_read_at", "revision", "updated_at"])
    snapshot.acknowledged_at = timezone.now()
    snapshot.save(update_fields=["acknowledged_at", "updated_at"])
    return {"read_id": str(snapshot.id), "acknowledged": True}
