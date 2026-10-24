"""Invoices originate in accepted workflows, never a client-supplied amount."""

import uuid
from django.utils import timezone
from ..models import BillingSourceLink, InvoiceLine, RentInvoice
from .rental_phase2 import RentalConflict


def source_invoices(kind, identity):
    return [
        {
            "id": str(link.invoice.id),
            "reference": link.invoice.reference,
            "family": "rental" if link.invoice.purpose == "rent" else "billing",
        }
        for link in BillingSourceLink.objects.filter(
            source_kind=kind, source_id=identity
        ).select_related("invoice")
    ]


def invalidate_maintenance_cost(item):
    links = BillingSourceLink.objects.filter(
        source_kind="maintenance", source_id=item.id
    ).select_related("invoice")
    for link in links:
        invoice = RentInvoice.objects.select_for_update().get(pk=link.invoice_id)
        if invoice.status == "cancelled":
            continue
        if invoice.applied_minor or invoice.payment_attempts.exists():
            raise RentalConflict(
                "Resolve the billed cost before changing it; a paid cost requires an approved correction.",
                code="payment_in_progress",
            )
        invoice.status = "cancelled"
        invoice.revision += 1
        invoice.save(update_fields=["status", "revision", "updated_at"])


def maintenance_invoice(item, actor):
    # Caller holds the canonical lease/maintenance locks and has accepted the
    # exact cost version using the current responsible payer's authority.
    if item.approved_cost_version != item.cost_version or not item.proposed_cost_minor:
        raise RentalConflict(
            "Accept the current cost before invoicing it.", code="invoice_changed"
        )
    existing = BillingSourceLink.objects.filter(
        source_kind="maintenance", source_id=item.id, source_version=item.cost_version
    ).first()
    if existing:
        return existing.invoice
    organization = item.lease.renter_company if item.cost_payer == "company" else None
    payer = (
        item.lease.owner
        if item.cost_payer == "owner"
        else actor if organization else item.lease.tenant
    )
    invoice = RentInvoice.objects.create(
        purpose="maintenance",
        payer=payer,
        organization=organization,
        workspace="owner" if item.cost_payer == "owner" else "tenant",
        business_reference=f"maintenance:{item.id}:{item.cost_version}",
        reference=f"INV-{uuid.uuid4().hex[:20].upper()}",
        due_date=timezone.localdate(),
        amount_minor=item.proposed_cost_minor,
        charges_minor=item.proposed_cost_minor,
        purchase_snapshot={
            "subject_id": str(item.id),
            "lease_id": str(item.lease.id),
            "cost_version": item.cost_version,
            "name_en": item.title,
            "name_ar": item.title,
            "cost_payer": item.cost_payer,
        },
    )
    InvoiceLine.objects.create(
        invoice=invoice,
        line_type="maintenance",
        description=item.title,
        amount_minor=item.proposed_cost_minor,
        source={
            "maintenance_id": str(item.id),
            "cost_version": item.cost_version,
            "quantity": 1,
        },
    )
    BillingSourceLink.objects.create(
        invoice=invoice,
        source_kind="maintenance",
        source_id=item.id,
        source_version=item.cost_version,
    )
    return invoice


def validate_maintenance_invoice(invoice):
    from ..models import MaintenanceRequest

    item = MaintenanceRequest.objects.filter(
        id=invoice.purchase_snapshot.get("subject_id")
    ).first()
    if (
        not item
        or item.status == "cancelled"
        or item.cost_version != invoice.purchase_snapshot.get("cost_version")
        or item.approved_cost_version != item.cost_version
        or item.proposed_cost_minor != invoice.amount_minor
    ):
        raise RentalConflict(
            "The accepted maintenance cost changed.", code="invoice_changed"
        )


def promotion_invoice(campaign, option):
    invoice = RentInvoice.objects.create(
        purpose="promotion",
        payer=campaign.owner,
        workspace="owner",
        business_reference=f"promotion:{campaign.id}",
        reference=f"INV-{uuid.uuid4().hex[:20].upper()}",
        due_date=timezone.localdate(),
        amount_minor=option.amount_minor,
        charges_minor=option.amount_minor,
        currency=option.currency,
        exponent=option.exponent,
        purchase_snapshot={
            "subject_id": str(campaign.id),
            "option_id": option.id,
            "option_revision": option.revision,
            "duration_days": option.duration_days,
            "name_en": option.title_en,
            "name_ar": option.title_ar,
        },
    )
    InvoiceLine.objects.create(
        invoice=invoice,
        line_type="promotion",
        description=option.title_en,
        amount_minor=invoice.amount_minor,
        currency=invoice.currency,
        exponent=invoice.exponent,
        source={"description_ar": option.title_ar, "quantity": 1},
    )
    BillingSourceLink.objects.create(
        invoice=invoice, source_kind="promotion", source_id=campaign.id
    )
    return invoice


def validate_promotion(invoice):
    from ..models import BoostCampaign
    from ..catalog_models import PromotionOption
    from core_apps.properties.models import Property

    campaign = BoostCampaign.objects.select_related("property").get(
        id=invoice.purchase_snapshot["subject_id"]
    )
    if (
        campaign.owner_id != invoice.payer_id
        or campaign.property.owner_id != invoice.payer_id
        or campaign.status != "pending"
        or campaign.property.status != Property.Status.VERIFIED
        or not campaign.property.is_verified
        or not PromotionOption.objects.filter(
            id=campaign.option_id, active=True
        ).exists()
    ):
        raise RentalConflict(
            "The promotion is no longer eligible.", code="fulfillment_pending"
        )
    return campaign


def activate_promotion(invoice):
    from datetime import timedelta

    campaign = validate_promotion(invoice)
    campaign.status = "active"
    campaign.starts_at = timezone.now()
    campaign.ends_at = campaign.starts_at + timedelta(
        days=invoice.purchase_snapshot["duration_days"]
    )
    campaign.save(update_fields=["status", "starts_at", "ends_at", "updated_at"])
