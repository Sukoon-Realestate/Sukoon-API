"""Stream complete read membership into SQL rows instead of giant JSON objects."""

from django.db import transaction
from django.db.models import Case, CharField, F, OuterRef, Q, Subquery, Value, When
from django.utils import timezone

from ..models import SavedSearchReadItem, SavedSearchRead, SavedSearchVisit

BATCH_SIZE = 500


def baseline_read(visit):
    value = visit.acknowledged_read
    return (
        value
        if (
            value
            and value.itemized
            and value.items_ready
            and value.acknowledged_at
            and value.base_revision + 1 == visit.revision
            and value.definition_hash == visit.definition_hash
        )
        else None
    )


def versions(read):
    if not read.itemized:
        return read.versions
    return {
        str(identity): [revision, modified.isoformat()]
        for identity, revision, modified in read.items.values_list(
            "property_identity", "review_revision", "modified_at"
        ).iterator(chunk_size=BATCH_SIZE)
    }


def write_items(snapshot, queryset, *, previous_read=None, previous=None):
    from .saved_search_reads import SearchReadExpired

    previous = previous or {}
    compare = snapshot.baseline_state == "available"
    if compare and previous_read is not None:
        prior = SavedSearchReadItem.objects.filter(read_id=previous_read, property_identity=OuterRef("id"))
        queryset = queryset.annotate(
            baseline_revision=Subquery(prior.values("review_revision")[:1]),
            baseline_modified=Subquery(prior.values("modified_at")[:1]),
        ).annotate(
            delta=Case(
                When(baseline_revision__isnull=True, then=Value("new")),
                When(Q(baseline_revision=F("review_revision")) & Q(baseline_modified=F("updated_at")), then=Value("")),
                default=Value("updated"),
                output_field=CharField(),
            )
        )
    else:
        queryset = queryset.annotate(delta=Value("", output_field=CharField()))
    batch = []

    def commit():
        # A receipt-local lock prevents a drained/retired format from receiving
        # late items. No account or listing lock is held during these batches.
        with transaction.atomic():
            try:
                current = (
                    SavedSearchRead.objects.select_for_update()
                    .only("pk", "itemized", "items_ready", "expires_at")
                    .get(pk=snapshot.pk)
                )
            except SavedSearchRead.DoesNotExist:
                raise SearchReadExpired()
            if not current.itemized or current.items_ready or current.expires_at <= timezone.now():
                raise SearchReadExpired()
            SavedSearchReadItem.objects.bulk_create(batch, batch_size=BATCH_SIZE)
        batch.clear()

    for identity, revision, modified, delta in (
        queryset.values_list("id", "review_revision", "updated_at", "delta").distinct().iterator(chunk_size=BATCH_SIZE)
    ):
        if compare and previous_read is None:
            old = previous.get(str(identity))
            delta = "new" if old is None else "updated" if old != [revision, modified.isoformat()] else ""
        batch.append(
            SavedSearchReadItem(
                read=snapshot, property_identity=identity, review_revision=revision, modified_at=modified, change=delta
            )
        )
        if len(batch) == BATCH_SIZE:
            commit()
    if batch:
        commit()


def materialize_legacy_baseline(visit, *, apply=False):
    """Rollback adapter: preserve the old JSON reader after itemized creation stops."""
    from datetime import timedelta
    from django.db import transaction
    from core_apps.users.models import User
    from ..models import SavedSearchVisit

    prior = baseline_read(visit)
    expired = visit.last_read_at is None or visit.last_read_at < timezone.now() - timedelta(days=30)
    if not prior and not expired:
        return "source_changed"
    if not apply:
        return "eligible"
    # The legacy representation intrinsically requires a full dictionary. Build
    # it outside shared locks; this explicit rollback command is not a read API.
    data = {} if expired else versions(prior)
    with transaction.atomic():
        actor = User.objects.select_for_update().get(pk=visit.user_id)
        if actor.closed_at:
            data = {}
        current = (
            SavedSearchVisit.objects.select_for_update()
            .only("pk", "revision", "definition_hash", "acknowledged_read_id")
            .get(pk=visit.pk)
        )
        if (
            current.revision != visit.revision
            or current.definition_hash != visit.definition_hash
            or current.acknowledged_read_id != visit.acknowledged_read_id
        ):
            return "source_changed"
        current.versions, current.acknowledged_read_id = data, None
        current.save(update_fields=["versions", "acknowledged_read", "updated_at"])
    return "closed_erased" if actor.closed_at else "materialized"


def retire_expired_itemized_reads(batch_size=100):
    """Rollback adapter: keep expired receipt identities, remove unknown children."""
    from django.conf import settings
    from django.db.models import Exists

    if getattr(settings, "SAVED_SEARCH_ITEMIZED_READS", False):
        raise ValueError("Disable itemized creation before retiring its receipts.")
    if not 1 <= batch_size <= 100:
        raise ValueError("Use a receipt batch size from 1 to 100.")
    active = SavedSearchVisit.objects.filter(acknowledged_read_id=OuterRef("pk"))
    with transaction.atomic():
        targets = list(
            SavedSearchRead.objects.select_for_update(of=("self",))
            .filter(itemized=True, expires_at__lte=timezone.now())
            .annotate(active_baseline=Exists(active))
            .filter(active_baseline=False)
            .order_by("expires_at", "pk")[:batch_size]
        )
        ids = [row.pk for row in targets]
        items = list(
            SavedSearchReadItem.objects.filter(read_id__in=ids)
            .order_by("read_id", "property_identity")
            .values_list("pk", flat=True)[:BATCH_SIZE]
        )
        if items:
            SavedSearchReadItem.objects.filter(pk__in=items).delete()
        children = SavedSearchReadItem.objects.filter(read_id=OuterRef("pk"))
        return (
            SavedSearchRead.objects.filter(pk__in=ids)
            .annotate(has_items=Exists(children))
            .filter(has_items=False)
            .update(itemized=False, items_ready=True, versions={}, changes={})
        )
