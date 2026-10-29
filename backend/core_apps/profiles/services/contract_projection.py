"""Read-only personal contract rows shared by profile counts and paginated lists.

Legacy registry rows retain their status/date semantics and independent identity.
Canonical legal periods use Cairo civil dates and exclusive end dates. Neither
company membership nor possession/financial closure establishes a personal party.
"""

from zoneinfo import ZoneInfo

from django.db.models import (
    BooleanField, Case, CharField, Exists, F, IntegerField, JSONField,
    OuterRef, Q, UUIDField, Value, When,
)
from django.utils import timezone

from core_apps.features.models import Lease, RentalChange, RentalTimelineEvent, SigningSession
from core_apps.profiles.models import Contract


CAIRO = ZoneInfo("Africa/Cairo")
CURRENT_STATUSES = (Lease.Status.ACTIVE, Lease.Status.TERMINATION_PENDING)
COLUMNS = (
    "_row_id", "_source", "_property_title", "_status", "_start_date", "_end_date",
    "_document_url", "_lease_id", "_revision", "_is_current", "_exclusive",
    "_lease_status", "_tenancy_root_id", "_offer_id", "_offer_snapshot",
)


def civil_day():
    return timezone.localdate(timezone=CAIRO)


def _canonical(user, as_of):
    signed_event = RentalTimelineEvent.objects.filter(lease_id=OuterRef("pk"), kind="signed")
    signed_sessions = SigningSession.objects.filter(
        lease_id=OuterRef("pk"), status="completed", completed_at__isnull=False,
        document_id=OuterRef("document_id"), document_hash=OuterRef("document_hash"),
    ).exclude(document_id__isnull=True).exclude(document_hash="")
    # Cancellation/expiry alone is not evidence of a contract: inventory hold
    # expiry also marks unsigned drafts expired. Preserve explicit activation or
    # bilateral signature evidence for these terminal states.
    eligible = Lease.objects.filter(tenant=user, renter_company__isnull=True).exclude(
        private_access_revocations__user=user
    ).annotate(
        _signed_event=Exists(signed_event),
        _owner_signed=Exists(signed_sessions.filter(signer_id=OuterRef("owner_id"))),
        _tenant_signed=Exists(signed_sessions.filter(signer_id=OuterRef("tenant_id"))),
    ).filter(
        Q(status__in=(*CURRENT_STATUSES, Lease.Status.SIGNED, Lease.Status.ENDED))
        | (Q(status__in=(Lease.Status.CANCELLED, Lease.Status.EXPIRED)) & (
            Q(activated_at__isnull=False) | Q(_signed_event=True)
            | (Q(_owner_signed=True) & Q(_tenant_signed=True))
        ))
    )
    replacement = RentalChange.objects.filter(
        lease_id=OuterRef("pk"), kind=RentalChange.Kind.RENEWAL, status=RentalChange.Status.APPLIED,
        result_lease__tenant=user, result_lease__renter_company__isnull=True,
        result_lease__owner_id=OuterRef("owner_id"),
        result_lease__property_id=OuterRef("property_id"),
        result_lease__offer_id=OuterRef("offer_id"),
        result_lease__tenancy_root_id=OuterRef("tenancy_root_id"),
        result_lease__status__in=CURRENT_STATUSES,
        result_lease__start_date__lte=as_of, result_lease__end_date__gt=as_of,
    ).exclude(result_lease_id=OuterRef("pk")).exclude(
        result_lease__private_access_revocations__user=user
    )
    return eligible.annotate(_replaced=Exists(replacement)).annotate(
        _row_id=F("id"), _source=Value("canonical_lease", output_field=CharField()),
        _property_title=F("property__title"),
        _status=Case(
            When(_replaced=True, status__in=CURRENT_STATUSES, then=Value("ended")),
            When(status=Lease.Status.ACTIVE, end_date__lte=as_of, then=Value("expired")),
            When(status=Lease.Status.TERMINATION_PENDING, end_date__lte=as_of, then=Value("ended")),
            default=F("status"), output_field=CharField(),
        ),
        _start_date=F("start_date"), _end_date=F("end_date"),
        # Protected document links are obtained on demand via the exact lease.
        _document_url=Value("", output_field=CharField()),
        _lease_id=F("id"), _revision=F("revision"),
        _is_current=Case(
            When(status__in=CURRENT_STATUSES, start_date__lte=as_of, end_date__gt=as_of,
                 _replaced=False, then=Value(True)),
            default=Value(False), output_field=BooleanField(),
        ),
        _exclusive=Value(True, output_field=BooleanField()), _lease_status=F("status"),
        _tenancy_root_id=F("tenancy_root_id"), _offer_id=F("offer_id"),
        _offer_snapshot=F("offer_snapshot"),
    )


def _legacy(user):
    return Contract.objects.filter(tenant=user).annotate(
        _row_id=F("id"), _source=Value("legacy_registry", output_field=CharField()),
        _property_title=F("property_title"), _status=F("status"),
        _start_date=F("start_date"), _end_date=F("end_date"), _document_url=F("document_url"),
        _lease_id=Value(None, output_field=UUIDField()),
        _revision=Value(None, output_field=IntegerField()),
        _is_current=Case(When(status=Contract.Status.ACTIVE, then=Value(True)),
                         default=Value(False), output_field=BooleanField()),
        # The legacy model does not define an inclusive/exclusive date contract.
        _exclusive=Value(None, output_field=BooleanField()),
        _lease_status=Value(None, output_field=CharField()),
        _tenancy_root_id=Value(None, output_field=UUIDField()),
        _offer_id=Value("", output_field=CharField()),
        _offer_snapshot=Value(None, output_field=JSONField()),
    )


def rows(user, *, bucket="all", as_of=None):
    """One DB UNION ALL; the normal DRF paginator counts/slices before hydration."""
    if bucket not in {"current", "all"}:
        raise ValueError("Unsupported contract bucket")
    as_of = as_of if as_of is not None else civil_day()
    canonical, legacy = _canonical(user, as_of), _legacy(user)
    if bucket == "current":
        canonical, legacy = canonical.filter(_is_current=True), legacy.filter(_is_current=True)
    return canonical.order_by().values(*COLUMNS).union(
        legacy.order_by().values(*COLUMNS), all=True,
    ).order_by("-_is_current", "-_start_date", "_source", "_row_id")


def count_current(user, *, as_of=None):
    return rows(user, bucket="current", as_of=as_of).count()


def representation(row):
    """Map only a selected page row; do not load a model or generate documents."""
    canonical = row["_source"] == "canonical_lease"
    return {
        "id": f"lease:{row['_row_id']}" if canonical else str(row["_row_id"]),
        "source": row["_source"], "party_role": "tenant",
        "property_title": row["_property_title"], "status": row["_status"],
        "start_date": row["_start_date"], "end_date": row["_end_date"],
        "document_url": row["_document_url"], "lease_id": row["_lease_id"],
        "revision": row["_revision"], "is_current": row["_is_current"],
        "end_date_is_exclusive": row["_exclusive"], "lease_status": row["_lease_status"],
        "tenancy_root_id": row["_tenancy_root_id"], "offer_id": row["_offer_id"],
        "offer_snapshot": row["_offer_snapshot"],
    }
