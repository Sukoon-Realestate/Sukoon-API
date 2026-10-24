"""One real sandbox intention, never a card charge or a production mutation."""

import json
import uuid
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.utils import timezone
from rest_framework.test import APIClient


class Command(BaseCommand):
    help = "Create a synthetic approved maintenance invoice and one real Paymob TEST checkout in the isolated commerce sandbox DB."

    def handle(self, *args, **options):
        from core_apps.features.services import paymob_client

        if (
            str(connection.settings_dict["NAME"])
            != str(settings.BASE_DIR / "commerce_sandbox.sqlite3")
            or not paymob_client.checkout_ready()
        ):
            raise CommandError(
                "Use the isolated commerce_sandbox settings, test keys and PAYMOB_INVOICE_CHECKOUT_ENABLED=true."
            )
        from core_apps.features.models import Lease, MaintenanceRequest, PaymobPayment
        from core_apps.properties.models import (
            Property,
            Governorate,
            City,
            PropertyType,
        )

        suffix = uuid.uuid4().hex[:12]
        owner, tenant = [
            get_user_model().objects.create_user(
                email=f"paymob-{suffix}-{role}@example.test",
                first_name="Sandbox",
                last_name=role,
                is_verified=True,
            )
            for role in ("owner", "tenant")
        ]
        tenant.profile.phone_number = "+201010101010"
        tenant.profile.save(update_fields=["phone_number"])
        governorate, _ = Governorate.objects.get_or_create(
            name="Paymob synthetic sandbox"
        )
        city, _ = City.objects.get_or_create(
            name="Paymob synthetic sandbox", governorate=governorate
        )
        category, _ = PropertyType.objects.get_or_create(
            slug="paymob-sandbox", defaults={"name": "Synthetic sandbox"}
        )
        prop = Property.objects.create(
            owner=owner,
            title="Synthetic Paymob sandbox",
            price=100,
            property_type=category,
            governorate=governorate,
            city=city,
            status="verified",
            is_verified=True,
            is_ownership_verified=True,
        )
        start = timezone.localdate()
        lease = Lease.objects.create(
            property=prop,
            owner=owner,
            tenant=tenant,
            template_id="synthetic-paymob-sandbox",
            template_version="1",
            start_date=start,
            end_date=start + timedelta(days=30),
            rent_amount_minor=10000,
            status="active",
            occupancy_status="occupied",
            legacy_read_only=False,
            offer_id=str(uuid.uuid4()),
        )
        item = MaintenanceRequest.objects.create(
            lease=lease,
            reporter=tenant,
            title="Synthetic sandbox cost",
            description="Local test prerequisite, not a real service.",
            category="plumbing",
            priority="normal",
            status="appointment_proposed",
            cost_payer="tenant",
            cost_version=1,
            proposed_cost_minor=1000,
        )
        client = APIClient(raise_request_exception=False)
        client.force_authenticate(tenant)
        root = "/api/v1/features/v1/"
        approval = client.post(
            root + f"maintenance-requests/{item.id}/actions/",
            {
                "action": "approve_cost",
                "expected_revision": 1,
                "cost_version": 1,
                "request_key": str(uuid.uuid4()),
            },
            format="json",
        )
        if approval.status_code != 200:
            raise CommandError(
                f"Synthetic cost approval failed with HTTP {approval.status_code}."
            )
        invoice_id = approval.json()["data"]["resource"]["billing_invoices"][0]["id"]
        quote = client.post(
            root + f"billing/invoices/{invoice_id}/quote/?platform=android",
            {"expected_revision": 1, "request_key": str(uuid.uuid4())},
            format="json",
        )
        if quote.status_code != 201:
            raise CommandError(f"Synthetic quote failed with HTTP {quote.status_code}.")
        response = client.post(
            root + f"billing/invoices/{invoice_id}/checkout/",
            {
                "expected_revision": 1,
                "quote_id": quote.json()["data"]["id"],
                "request_key": str(uuid.uuid4()),
            },
            format="json",
        )
        payment = PaymobPayment.objects.filter(attempt__invoice__id=invoice_id).first()
        # Never print hosted URLs, client secrets, billing details or raw responses.
        self.stdout.write(
            json.dumps(
                {
                    "sandbox_only": True,
                    "invoice_id": invoice_id,
                    "http_status": response.status_code,
                    "durable_attempt": bool(payment),
                    "payment_status": (
                        payment.attempt.payment_status if payment else None
                    ),
                    "provider_intention_created": bool(
                        payment and payment.intention_id
                    ),
                    "provider_order_bound": bool(payment and payment.order_id),
                    "receipt_created": bool(
                        payment and hasattr(payment.attempt, "receipt")
                    ),
                }
            )
        )
        if response.status_code != 200:
            raise CommandError(
                "The original sandbox attempt remains available for reconciliation; do not resubmit it."
            )
