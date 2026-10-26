"""Author edits preserve reviewed versions; accepted contracts remain immutable."""
from copy import deepcopy
from datetime import time
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from ..models import RentalChange, RentalChangeVersion, RentalTimelineEvent, RentalConsentRecord
from .rental_phase2 import RentalConflict
from .rental_lifecycle.common import require_revision, audit
from .rental_lifecycle.consents import record_consent
from .rental_phase3 import cairo_instant
from .change_terms import validate_changed_terms

EDITABLE = {RentalChange.Kind.AMENDMENT, RentalChange.Kind.RENEWAL, RentalChange.Kind.PAYMENT_EXTENSION}


class ChangeEditBody(serializers.Serializer):
    expected_revision = serializers.IntegerField(min_value=1)
    lease_revision = serializers.IntegerField(min_value=1)
    request_key = serializers.UUIDField()
    reason = serializers.CharField(max_length=4000, allow_blank=True)
    terms = serializers.JSONField(required=False)
    requested_date = serializers.DateField(required=False, allow_null=True)
    effective_on = serializers.DateField(required=False, allow_null=True)
    evidence_ids = serializers.ListField(child=serializers.UUIDField(), default=list)
    invoice_id = serializers.UUIDField(required=False, allow_null=True)


def can_edit(item, actor):
    return (not item.lease.legacy_read_only and item.kind in EDITABLE and item.requester_id == actor.pk
            and item.status in {'proposed', 'changes_requested'}
            and not item.document_id and not item.signed_by and not item.applied_at)


def snapshot(item):
    return {
        'terms': deepcopy(item.terms), 'previous_terms': deepcopy(item.previous_terms),
        'reason': item.reason, 'requested_date': str(item.requested_date) if item.requested_date else None,
        'effective_on': str(item.effective_on) if item.effective_on else None,
        'invoice_id': str(item.invoice.id) if item.invoice_id else None,
        'invoice_revision': item.invoice.revision if item.invoice_id else None,
        'evidence_ids': [str(value) for value in item.evidence.values_list('id', flat=True)],
        'content_version': item.content_revision,
    }


def freeze(item, *, baseline=False):
    return RentalChangeVersion.objects.get_or_create(
        change=item, version=item.content_revision,
        defaults={'author_id': item.requester_id, 'lease_revision': item.lease.revision,
                  'snapshot': snapshot(item), 'baseline': baseline},
    )[0]


def revise(item, actor, data, evidence):
    require_revision(item, data['expected_revision'])
    require_revision(item.lease, data['lease_revision'])
    if not can_edit(item, actor):
        raise PermissionDenied('Only the proposal author can edit it before acceptance.')
    if data.get('invoice_id') and str(data['invoice_id']) != (str(item.invoice.id) if item.invoice_id else ''):
        raise ValidationError({'invoice_id': 'Keep the original invoice.'})
    proposed = data.get('terms')
    effective = data.get('effective_on')
    if item.kind in {'amendment', 'renewal'}:
        if not isinstance(proposed, dict):
            raise ValidationError({'terms': 'Full proposed terms are required.'})
        from .rental_lifecycle.terms import _json_safe
        proposed = _json_safe(validate_changed_terms(proposed))
        if item.kind == 'renewal':
            from .planning_transitions import require_no_departure
            require_no_departure(item.lease)
            start, end = parse_date(proposed['starts_on']), parse_date(proposed['ends_on_exclusive'])
            if start != item.lease.end_date or end <= start or (effective and effective != start):
                raise ValidationError({'effective_on': 'A continuous renewal starts at the current end date.'})
            if proposed['monthly_rent']['amount_minor'] <= 0:
                raise ValidationError({'terms': 'Renewal rent must be positive.'})
            effective = start
        from .platform_rent_payments import reviewed_terms
        proposed = reviewed_terms(proposed)
    elif item.kind == 'payment_extension':
        if not data.get('requested_date'):
            raise ValidationError({'requested_date': 'A valid date is required.'})
        if item.invoice.status in {'paid', 'settled', 'cancelled', 'written_off'}:
            raise RentalConflict('This invoice no longer needs a payment extension.', code='invoice_changed')
    freeze(item, baseline=not item.versions.exists())
    if item.kind in {'amendment', 'renewal'}:
        item.terms = proposed
        item.previous_terms = deepcopy(item.lease.terms)
        item.effective_on = effective
    else:
        item.requested_date = data['requested_date']
        item.original_due_at = item.invoice.due_at
        item.deferred_until = cairo_instant(item.requested_date, time.max)
    item.reason = data['reason']
    item.status = 'proposed'
    item.approvals = [str(actor.id)]
    item.content_revision += 1
    item.revision += 1
    item.save()
    item.evidence.set(evidence)
    freeze(item)
    record_consent(item, actor, 'propose', snapshot(item))
    audit(item, actor, 'change.version_proposed')
    from .planning_notifications import record_event
    record_event(item, actor, 'rental_change.version_proposed')
    return item


def history(item):
    return [{'version': row.version, 'author_id': str(row.author.id), 'author_name': row.author.get_full_name,
             'lease_revision': row.lease_revision, 'snapshot': row.snapshot, 'baseline': row.baseline,
             'created_at': row.created_at.isoformat()}
            for row in item.versions.select_related('author').order_by('version')]


def comments(item):
    decisions = RentalConsentRecord.objects.filter(subject_kind="rentalchange", subject_id=item.id).select_related("actor").order_by("created_at")
    first = decisions.first()
    legacy = RentalTimelineEvent.objects.filter(
        lease=item.lease, resource_id=item.id, kind__startswith="change_", kind__endswith="_note",
    ).select_related("actor").order_by("created_at")
    if first:
        legacy = legacy.filter(created_at__lt=first.created_at)
    return [
        {"action": row.kind.removeprefix("change_").removesuffix("_note"),
         "actor_name": row.actor.get_full_name if row.actor_id else "", "note": row.description,
         "content_version": None, "created_at": row.created_at.isoformat()}
        for row in legacy
    ] + [
        {"action": row.decision, "actor_name": row.actor.get_full_name, "note": row.snapshot["note"],
         "content_version": row.snapshot.get("content_version"), "created_at": row.created_at.isoformat()}
        for row in decisions if row.snapshot.get("note")
    ]
