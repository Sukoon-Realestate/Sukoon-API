"""Freeze approved signing input locally before any external request is attempted."""

import hashlib
import html
import json
from datetime import timedelta
from uuid import uuid5, NAMESPACE_URL
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.exceptions import PermissionDenied
from core_apps.users.models import User
from ..models import Lease, RentalChange, RentalSigningDocument
from ..providers import GeneratedRentalDocument, HostedProviderSession
from .rental_phase2 import RentalConflict
from . import signwell_client


def source_for(identity):
    lease = Lease.objects.filter(id=identity).first()
    change = RentalChange.objects.select_related("lease").filter(id=identity).first()
    if bool(lease) == bool(change):
        raise RentalConflict("The signing source is missing or ambiguous.")
    return (change or lease), (change.lease if change else lease), change


def recipients_for(lease, change):
    if change and lease.renter_company_id:
        from .company.tenancy_resolution import signing_role

        identities = [
            value
            for role, value in change.company_review.snapshot["required"].items()
            if signing_role(role)
        ]
    elif lease.renter_company_id:
        identities = [
            str(lease.owner.id),
            str(lease.company_tenancy.signer_mandate.membership.user.id),
        ]
    else:
        identities = [str(lease.owner.id), str(lease.tenant.id)]
    rows = list(User.objects.filter(id__in=set(identities)).order_by("id"))
    if (
        len(rows) < 2
        or len(rows) != len(set(identities))
        or any(
            not row.email or not row.is_active or not row.is_verified for row in rows
        )
    ):
        raise RentalConflict(
            "Every contract signatory must be identified and currently eligible."
        )
    return [
        {"id": str(row.id), "name": row.get_full_name or row.email, "email": row.email}
        for row in rows
    ]


LABELS = {
    "lease_id": "معرف العقد / Agreement",
    "source_id": "معرف النسخة / Source",
    "source_revision": "الإصدار / Revision",
    "template_id": "نموذج العقد / Template",
    "template_version": "إصدار النموذج / Template version",
    "property_id": "معرف العقار / Property",
    "property_title": "العقار / Property name",
    "offer_snapshot": "الوحدة والعرض المعتمدان / Reviewed accommodation",
    "terms": "الشروط المعتمدة / Approved terms",
    "starts_on": "بداية الإيجار / Start",
    "ends_on_exclusive": "نهاية الإيجار / End (exclusive)",
    "handover_on": "موعد الاستلام / Handover",
    "monthly_rent": "الإيجار الدوري / Rent",
    "deposit": "التأمين / Deposit",
    "occupants": "عدد الشاغلين / Occupants",
    "included_services": "الخدمات المشمولة / Included services",
    "excluded_services": "الخدمات غير المشمولة / Excluded services",
    "termination_policy": "شروط الإنهاء / Termination",
    "renewal_policy": "شروط التجديد / Renewal",
    "policy_version": "إصدار السياسة / Policy version",
    "renter_company": "الشركة المستأجرة / Renter company",
    "deposit_holder": "حائز التأمين / Deposit holder",
    "notice_days": "مهلة الإخطار بالأيام / Notice days",
    "automatic": "التجديد التلقائي / Automatic renewal",
    "timezone": "المنطقة الزمنية / Time zone",
    "billing_anchor_day": "يوم الفوترة الشهري / Monthly billing day",
    "commission_rate_bps": "نسبة العمولة / Commission rate",
    "renewal_commission_rate_bps": "عمولة التجديد / Renewal commission",
    "commission_payer": "مسؤول سداد العمولة / Commission payer",
    "commission_basis": "أساس احتساب العمولة / Commission basis",
    "processing_fee_payer": "مسؤول رسوم المعالجة / Processing fee payer",
    "employees_are_debtors": "الموظفون أطراف مدينة / Employees are debtors",
    "rental_scope": "نطاق الإيجار / Rental scope",
    "offer_id": "مرجع العرض / Offer reference",
    "offer_revision": "إصدار العرض / Offer version",
    "property_revision": "إصدار العقار / Property version",
    "room_ids": "مراجع الغرف / Rooms",
    "bed_ids": "مراجع الأسرة / Beds",
    "capacity": "السعة / Capacity",
    "price": "السعر / Price",
    "price_period": "فترة السعر / Price period",
    "name": "الاسم / Name",
    "id": "المرجع / Reference",
    "rent": "الإيجار / Rent",
    "currency": "العملة / Currency",
    "revision": "الإصدار / Version",
}

VALUES = {
    "platform": "سكون / Sokoun",
    "owner": "المالك / Owner",
    "tenant": "المستأجر / Tenant",
    "company": "الشركة / Company",
    "entire_property": "العقار بالكامل / Entire property",
    "room": "غرفة / Room",
    "bed": "سرير / Bed",
    "monthly": "شهري / Monthly",
    "daily": "يومي / Daily",
    "yearly": "سنوي / Yearly",
    "first_period_base_rent": "الإيجار الأساسي للفترة الأولى / First period base rent",
}


def _display(value, field=""):
    if isinstance(value, bool):
        return "نعم / Yes" if value else "لا / No"
    if field.endswith("_bps") and isinstance(value, (int, str)):
        from decimal import Decimal

        return f"{Decimal(value) / 100}%"
    if isinstance(value, dict):
        if {"amount_minor", "currency", "exponent"} <= value.keys():
            from decimal import Decimal

            return html.escape(
                f"{Decimal(value['amount_minor']).scaleb(-int(value['exponent']))} {value['currency']}"
            )
        return (
            "<table>"
            + "".join(
                f"<tr><th>{html.escape(LABELS.get(key, key))}</th><td>{_display(item, key)}</td></tr>"
                for key, item in value.items()
            )
            + "</table>"
        )
    if isinstance(value, list):
        return (
            "<ul>" + "".join(f"<li>{_display(item)}</li>" for item in value) + "</ul>"
        )
    return html.escape(
        VALUES.get(value, value)
        if isinstance(value, str)
        else str(value if value is not None else "—")
    )


def render(snapshot, recipients):
    parties = "".join(
        f"<li>{html.escape(row['name'])} — {html.escape(row['email'])}</li>"
        for row in recipients
    )
    references = {
        key: value
        for key, value in snapshot.items()
        if not isinstance(value, (dict, list))
    }
    sections = "".join(
        f"<section><h2>{html.escape(LABELS.get(key, key))}</h2>{_display(value, key)}</section>"
        for key, value in snapshot.items()
        if isinstance(value, (dict, list))
    )
    return (
        "<!doctype html><html lang='ar' dir='rtl'><meta charset='utf-8'><style>body{font-family:Arial,sans-serif;font-size:14px;line-height:1.7}table{width:100%;border-collapse:collapse}th,td{border:1px solid #ccc;padding:8px;text-align:start;overflow-wrap:anywhere}th{width:32%}tr{break-inside:avoid}</style><title>عقد الإيجار</title><h1>عقد الإيجار / Rental agreement</h1><h2>الأطراف الموقعة / Signatories</h2><ul>"
        + parties
        + "</ul>"
        + _display(references)
        + sections
        + "</html>"
    ).encode("utf-8")


@transaction.atomic
def prepare(identity, revision, terms):
    if not signwell_client.ready():
        raise RentalConflict(
            "Signing is unavailable in this environment.", code="provider_unavailable"
        )
    source, lease, change = source_for(identity)
    if source.revision != revision or source.terms != terms:
        raise RentalConflict(
            "The reviewed signing source changed.", code="stale_revision"
        )
    recipients = recipients_for(lease, change)
    snapshot = {
        "lease_id": str(lease.id),
        "source_id": str(source.id),
        "source_revision": revision,
        "template_id": lease.template_id,
        "template_version": lease.template_version,
        "property_id": str(lease.property.id),
        "property_title": lease.property.title,
        "offer_snapshot": lease.offer_snapshot,
        "terms": terms,
    }
    if lease.renter_company_id:
        snapshot["renter_company"] = {
            "id": str(lease.renter_company.id),
            "name": lease.renter_company.name,
        }
    snapshot = json.loads(json.dumps(snapshot, default=str))
    content = render(snapshot, recipients)
    digest = hashlib.sha256(content).hexdigest()
    document, created = RentalSigningDocument.objects.get_or_create(
        lease=lease,
        change=change,
        source_revision=revision,
        defaults={
            "source_hash": digest,
            "snapshot": snapshot,
            "source_content": content,
            "recipients": recipients,
        },
    )
    if not created and document.source_hash != digest:
        raise RentalConflict(
            "The existing signing input cannot be replaced.", code="document_changed"
        )
    return GeneratedRentalDocument(document_id=document.id, digest=document.source_hash)


def hosted_session(identity, signer_id, request_key):
    source, _, _ = source_for(identity)
    document = RentalSigningDocument.objects.filter(id=source.document_id).first()
    if document is None or document.source_hash != source.document_hash:
        raise RentalConflict(
            "The exact signing document is unavailable.", code="document_changed"
        )
    if str(signer_id) not in {row["id"] for row in document.recipients}:
        raise PermissionDenied("Only a named signatory can open this document.")
    if not current_provider_read(document):
        raise RentalConflict(
            "The original document is being prepared or reconciled. Refresh its status.",
            code="signing_reconciliation_pending",
        )
    rows = document.provider_result.get("recipients", [])
    url = next(
        (
            row.get("embedded_signing_url")
            for row in rows
            if str(row["id"]) == str(signer_id)
        ),
        None,
    )
    if not url:
        raise RentalConflict(
            "Refresh the original signing session.",
            code="signing_reconciliation_pending",
        )
    return HostedProviderSession(
        provider_session_id=str(
            uuid5(NAMESPACE_URL, f"signwell:{document.id}:{signer_id}:{request_key}")
        ),
        hosted_url=url,
    )


def current_provider_read(document):
    checked = parse_datetime(document.provider_result.get("checked_at", ""))
    return bool(
        document.status == "pending"
        and checked
        and checked
        > timezone.now() - timedelta(minutes=settings.RENTAL_SIGNING_TTL_MINUTES)
    )


def renewable_session(source, user):
    document = RentalSigningDocument.objects.filter(id=source.document_id).first()
    return bool(
        document
        and current_provider_read(document)
        and source.signing_sessions.filter(
            signer=user,
            document_id=document.id,
            document_hash=document.source_hash,
            status="pending",
            expires_at__lte=timezone.now(),
        ).exists()
    )


def projection(source, user=None):
    if not source.document_id:
        return None
    document = RentalSigningDocument.objects.filter(id=source.document_id).first()
    return document_projection(document, user) if document else None


def document_projection(document, user=None):
    can_retry = bool(
        user
        and user.is_active
        and user.is_verified
        and str(user.id) in {row["id"] for row in document.recipients}
        and (
            (
                document.status == "failed"
                and not document.provider_document_id
                and signwell_client.ready()
            )
            or (document.status == "review_required" and document.completed_content)
        )
    )
    return {
        "id": str(document.id),
        "status": document.status,
        "failure_code": document.failure_code,
        "source_hash": document.source_hash,
        "signed_original_ready": bool(document.completed_content),
        "can_open": signwell_client.ready() and current_provider_read(document),
        "can_retry": can_retry,
        "completed_at": (
            document.completed_at.isoformat() if document.completed_at else None
        ),
    }


def unresolved(lease):
    # A lost create response or completed PDF can outlive the local session.
    return (
        lease.signing_documents.filter(change__isnull=True)
        .exclude(status__in=["prepared", "failed", "closed", "applied"])
        .exists()
    )
