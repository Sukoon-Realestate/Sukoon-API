"""Provider-independent reminders from existing rent obligations; no financial writes."""

from datetime import datetime, time, timedelta, timezone as datetime_timezone
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound
from ..models import RentInvoice
from ..planning_models import PlanningEvent
from .rental_phase3_parts.issue_invoice import CAIRO
from .rental_phase3_parts.payment_attempt_payload import invoice_balance_minor
from .rent_payment_recipients import recipients

EVENT_KINDS = ("rent_payment_reminder", "rent_initial_payment_due")


def effective_due(invoice):
    if not invoice.due_at:
        return None
    return max(invoice.due_at, invoice.deferred_until or invoice.due_at).astimezone(
        datetime_timezone.utc
    )


def eligibility(invoice, now):
    due = effective_due(invoice)
    if (
        invoice.purpose != "rent"
        or not invoice.lease_id
        or invoice.lease.legacy_read_only
        or invoice.status not in {"due", "partially_paid", "overdue"}
        or invoice_balance_minor(invoice) <= 0
        or not due
        or due <= now
    ):
        return None
    lease = invoice.lease
    if lease.status == "signed":
        if not lease.hold_expires_at or lease.hold_expires_at <= now:
            return None
    elif lease.status not in {"active", "termination_pending"}:
        if (
            lease.status not in {"ended", "cancelled"}
            or getattr(getattr(lease, "final_settlement", None), "status", "")
            != "accepted"
        ):
            return None
    initial = bool(invoice.billing_period_id and invoice.billing_period.sequence == 1)
    kind = EVENT_KINDS[1] if initial else EVENT_KINDS[0]
    # Civil-day subtraction, then zone conversion: not a device-clock/72h timer.
    opens = datetime.combine(
        due.astimezone(CAIRO).date() - timedelta(days=3), time(9), tzinfo=CAIRO
    )
    if not initial and now < opens:
        return None
    return kind, due


def candidates():
    return (
        RentInvoice.objects.filter(
            purpose="rent",
            lease__isnull=False,
            status__in=["due", "partially_paid", "overdue"],
        )
        .select_related("lease__owner", "lease__tenant", "billing_period")
        .order_by("due_at", "id")
    )


def event_data(invoice, kind, due, role):
    return {
        "action_type": "open_rent_invoice",
        "target_id": str(invoice.id),
        "invoice_id": str(invoice.id),
        "lease_id": str(invoice.lease.id),
        "company_id": (
            str(invoice.lease.renter_company.id)
            if invoice.lease.renter_company_id
            else ""
        ),
        "schema_version": "1",
        "workspace": "company" if invoice.lease.renter_company_id else "tenant",
        **({"company_role": "payer"} if invoice.lease.renter_company_id else {}),
        "event_kind": kind,
        "effective_due_at": due.isoformat(),
        "recipient_role": role,
    }


def record_invoice(invoice, *, now=None):
    """Called inside invoice creation, or with a locked fresh invoice by the job."""
    now = now or timezone.now()
    window = eligibility(invoice, now)
    if not window:
        return 0
    kind, due = window
    count = 0
    for user, role in recipients(invoice):
        _, created = PlanningEvent.objects.get_or_create(
            recipient=user,
            event_key=f"{kind}:v1:{invoice.id}:{due.isoformat()}",
            defaults={"destination": event_data(invoice, kind, due, role)},
        )
        count += int(created)
    return count


def record_reminders(*, now=None, dry_run=False):
    now = now or timezone.now()
    rows, created = [], 0
    for candidate in candidates().iterator(chunk_size=100):
        if dry_run:
            window = eligibility(candidate, now)
            if window:
                kind, due = window
                rows.extend(
                    {
                        "invoice_id": str(candidate.id),
                        "recipient_id": str(user.id),
                        "role": role,
                        "kind": kind,
                        "effective_due_at": due.isoformat(),
                    }
                    for user, role in recipients(candidate)
                )
            continue
        with transaction.atomic():
            from .rental_lifecycle.locks import lock_financial_lease

            lock_financial_lease(candidate.lease)
            invoice = (
                candidates()
                .select_for_update(of=("self",))
                .filter(pk=candidate.pk)
                .first()
            )
            if invoice:
                created += record_invoice(invoice, now=now)
    return {"created": created, "candidates": rows} if dry_run else {"created": created}


def authorize(event):
    """Recheck current authority, due date and balance before every dispatch."""
    invoice = candidates().filter(id=event.destination.get("invoice_id")).first()
    if not invoice:
        raise NotFound()
    window = eligibility(invoice, timezone.now())
    if not window:
        raise NotFound()
    kind, due = window
    if (
        str(invoice.id) != event.destination.get("target_id")
        or str(invoice.lease.id) != event.destination.get("lease_id")
        or due.isoformat() != event.destination.get("effective_due_at")
        or kind != event.destination.get("event_kind")
    ):
        raise NotFound()
    roles = {user.pk: role for user, role in recipients(invoice)}
    if event.recipient_id not in roles:
        raise NotFound()
    return invoice, roles[event.recipient_id]


def notification_copy(event):
    invoice, role = authorize(event)
    pending = invoice.payment_attempts.filter(
        payment_status__in=["created", "pending", "authorized"]
    ).exists()
    title = (
        "فاتورة الإيجار الأولى / First rent invoice"
        if event.destination["event_kind"] == EVENT_KINDS[1]
        else "تذكير بموعد الإيجار / Rent due reminder"
    )
    if pending:
        body = "راجع حالة عملية الدفع الأصلية قبل أي محاولة جديدة. / Check the original payment before retrying."
    elif role == "authority_required":
        body = "راجع مسؤولية سداد الشركة وصلاحية التفويض. / Review the company's payment responsibility and authority."
    elif role == "coordinator":
        body = "تابع الفاتورة مع الدافع المفوّض. / Follow up on this invoice with the authorized payer."
    else:
        body = "راجع الفاتورة وموعدها والمبلغ المتبقي داخل سكون. / Review the invoice, due date and remaining amount in Sokoun."
    return {
        "title": title,
        "body": body,
        "notification_type": event.destination["event_kind"],
        "category": "rent_payments",
    }
