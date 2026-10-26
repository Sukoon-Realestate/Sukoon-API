"""One service follow-up for a paid invoice; never retries collection or grants finance."""

from django.db.models import Q
from django.http import Http404
from rest_framework.exceptions import PermissionDenied, NotFound
from ..models import PaymentFulfillment, RentalOperationalCase
from ..planning_models import PlanningEvent

KIND = "service_activation"
PENDING = "Payment confirmed. Service activation requires follow-up."
NEXT = "Review the original invoice and activation attempt. Retry activation only; do not collect payment again."
RECOVERED = "The service is active. Review the original receipt and record the follow-up outcome."


def follow_up(job):
    from .rental_lifecycle.cases import open_system_case, notify_case_participants
    from .rental_lifecycle.common import audit

    if job.status != "fulfilled":
        if job.case_id:
            return
        case = open_system_case(
            kind=KIND,
            source_key=f"service_activation:{job.invoice.id}",
            reason=PENDING,
            next_action=NEXT,
            attempt=job.attempt,
            actor=job.attempt.payer,
            notify=False,
        )
        job.case = case
        job.save(update_fields=["case", "updated_at"])
        notify_case_participants(case, "case.opened")
    elif job.case_id:
        case = job.case
        case.next_action = RECOVERED
        case.revision += 1
        case.save(update_fields=["next_action", "revision", "updated_at"])
        audit(case, None, "case.activation_recovered")
        notify_case_participants(case, "case.activation_recovered")


def can_read_invoice(case, user):
    from .billing_invoices import authorized_invoice

    if not case.payment_attempt_id:
        return False
    try:
        authorized_invoice(user, case.payment_attempt.invoice.id)
        return True
    except (Http404, PermissionDenied, NotFound):
        return False


def visible_company_cases(user):
    from ..models import CompanyMembership

    organizations = (
        CompanyMembership.objects.filter(user=user, is_active=True)
        .filter(Q(is_admin=True) | Q(can_execute_payments=True))
        .values("company_id")
    )
    return RentalOperationalCase.objects.filter(
        kind=KIND, payment_attempt__invoice__organization_id__in=organizations
    )


def restrict_visibility(queryset, user):
    from .rental_lifecycle.cases import independent_case_operator

    denied = [
        item.pk
        for item in queryset.filter(kind=KIND).select_related(
            "payment_attempt__invoice__organization"
        )
        if not independent_case_operator(item, user)
        and not can_read_invoice(item, user)
    ]
    return queryset.exclude(pk__in=denied)


def blocker(case):
    if not PaymentFulfillment.objects.filter(
        case=case,
        status="fulfilled",
        invoice__status="paid",
        attempt__payment_status="captured",
    ).exists():
        return PENDING
    return None


def context(case, user):
    if case.kind != KIND or not case.payment_attempt_id:
        return {}
    invoice = case.payment_attempt.invoice
    return {
        "service_activation": {
            "invoice_id": str(invoice.id),
            "invoice_reference": invoice.reference,
            "payment_attempt_id": str(case.payment_attempt.id),
            "workspace": "company" if invoice.organization_id else invoice.workspace,
            "status": getattr(
                getattr(invoice, "fulfillment", None), "status", "pending"
            ),
            "can_open_invoice": can_read_invoice(case, user),
        }
    }


def notify(case, action):
    if not case.payment_attempt_id:
        return
    invoice = case.payment_attempt.invoice
    recipients = [case.payment_attempt.payer]
    if invoice.organization_id:
        recipients = [
            member.user
            for member in invoice.organization.memberships.filter(
                is_active=True, user__is_active=True
            )
            .filter(Q(is_admin=True) | Q(can_execute_payments=True))
            .select_related("user")
        ]
    for recipient in recipients:
        if not recipient.is_active or not can_read_invoice(case, recipient):
            continue
        PlanningEvent.objects.get_or_create(
            recipient=recipient,
            event_key=f"{action}:{case.id}:{case.revision}",
            defaults={
                "destination": {
                    "action_type": "open_rental_case",
                    "target_id": str(case.id),
                    "case_id": str(case.id),
                    "invoice_id": str(invoice.id),
                    "revision": case.revision,
                    "event_kind": "service_activation_update",
                    "workspace": (
                        "company"
                        if invoice.organization_id
                        else (
                            "individual"
                            if invoice.workspace == "tenant"
                            else invoice.workspace
                        )
                    ),
                }
            },
        )
