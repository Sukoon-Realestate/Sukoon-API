"""Additive nonproduction fixtures. Seeded rows are not execution proof."""

import copy
import json
import uuid
from datetime import time, timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone

from core_apps.advertising.audit_asset import AUDIT_AD_ID, AUDIT_AD_SHA256
from core_apps.advertising.models import Advertisement
from core_apps.features.models import Lease
from core_apps.features.providers import checkout_available, fake_provider_available
from core_apps.features.services.rental_phase2 import get_or_create_owner_profile
from core_apps.features.services.planning import enabled_services
from core_apps.properties.models import (
    City,
    Governorate,
    OwnerAvailabilitySlot,
    Property,
    PropertyType,
    PropertyVisit,
)

OWNER_ID = "3b6d5dd4-2077-4bad-9c59-32717915035e"
TENANT_ID = "9eef4201-0ca4-4fc1-b91f-9ef27551c0ea"
PROPERTY_ID = "13954644-cc37-49d9-a772-f1a88be81401"
SOURCE_VISIT_ID = "e11a71e0-410a-42b7-a367-9c98867a5412"
PENDING_VISIT_ID = "a11a71e0-410a-42b7-a367-9c98867a5499"
SNAPSHOT_ONLY_LEASE_IDS = [f"c0{n}00000-0000-0000-0000-000000000001" for n in (4, 5, 6)]


def qa_id(name, owner_id):
    return uuid.uuid5(uuid.NAMESPACE_URL, f"sokoun-cycle-qa:{owner_id}:{name}")


def offer_terms(price, description):
    return {
        "price": price,
        "price_period": "monthly",
        "rental_period": 1,
        "deposit": "one_month",
        "suitable_for": "all",
        "description": description,
    }


def qa_inventory():
    room = "r0000001-0000-0000-0000-000000000001"
    bed = "b0000001-0000-0000-0000-000000000001"
    return {
        "schema_version": 1,
        "revision": 1,
        "mode": "partial",
        "rooms": [
            {
                "id": room,
                "name": "QA room",
                "capacity": 2,
                "beds": [{"id": bed, "name": "QA bed"}],
            }
        ],
        "offers": [
            {
                "id": "e0000001-0000-0000-0000-000000000001",
                "revision": 1,
                "rental_scope": "bed",
                "name": "QA bed offer",
                "room_ids": [room],
                "bed_id": bed,
                "capacity": 1,
                "availability": "available",
                "archived": False,
                "terms": offer_terms(
                    "1500.00", "A single bed for a dedicated QA rental."
                ),
            },
            {
                "id": "e0000002-0000-0000-0000-000000000002",
                "revision": 1,
                "rental_scope": "room",
                "name": "QA room offer",
                "room_ids": [room],
                "capacity": 2,
                "availability": "available",
                "archived": False,
                "terms": offer_terms(
                    "3000.00", "A private room for a dedicated QA rental."
                ),
            },
        ],
    }


class Command(BaseCommand):
    help = "Prepare resumable QA properties/visits without resetting passwords, leases, payments or receipts."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default="",
            help="Write a fresh manifest; refuses to overwrite an existing file.",
        )
        parser.add_argument("--print-extended", action="store_true")

    def _actor(self, actor_id, label):
        user, created = get_user_model().objects.get_or_create(
            id=actor_id,
            defaults={
                "email": f"cycle-{label}@example.test",
                "first_name": "QA",
                "last_name": label,
            },
        )
        if user.is_staff or user.is_superuser:
            raise CommandError(f"QA actor {actor_id} must be an ordinary account.")
        if created:
            user.set_unusable_password()
        user.is_active = user.is_verified = True
        user.save()
        return user

    def _property(self, property_id, owner, *, inventory, location, title, price):
        prop, created = Property.objects.get_or_create(
            id=property_id,
            defaults={
                "owner": owner,
                "title": title,
                "description": "Dedicated owner and tenant QA property.",
                "price": Decimal(price),
                "price_period": "monthly",
                "district": "QA",
                "status": Property.Status.VERIFIED,
                "is_verified": True,
                "is_ownership_verified": True,
                "bedrooms": 1,
                "bathrooms": 1,
                "rental_inventory": inventory,
                **location,
            },
        )
        if prop.owner_id != owner.pk:
            raise CommandError(
                f"Property {prop.id} belongs to another owner; no ownership was changed."
            )
        if not created and inventory and prop.rental_inventory:
            # Repair missing QA terms, never reset prices, availability or revisions.
            updated = copy.deepcopy(prop.rental_inventory)
            changed = False
            for offer in updated.get("offers", []):
                terms = offer.setdefault("terms", {})
                defaults = offer_terms(str(prop.price), prop.description)
                missing = {
                    key: value for key, value in defaults.items() if key not in terms
                }
                if missing:
                    terms.update(missing)
                    offer["revision"] = int(offer.get("revision", 0)) + 1
                    changed = True
            if changed:
                updated["revision"] = int(updated.get("revision", 0)) + 1
                prop.rental_inventory = updated
                prop.save(update_fields=["rental_inventory", "updated_at"])
        elif (
            not created
            and not inventory
            and prop.rental_inventory not in ({}, {"offers": []}, None)
        ):
            raise CommandError(
                "The legacy QA property has structured inventory; it was preserved."
            )
        return prop

    def _visit(self, visit_id, prop, tenant, status, date, at):
        visit, _ = PropertyVisit.objects.get_or_create(
            id=visit_id,
            defaults={
                "property": prop,
                "tenant": tenant,
                "visit_date": date,
                "visit_time": at,
                "status": status,
                "note": "Owner-tenant cycle QA fixture",
            },
        )
        if visit.property_id != prop.pk or visit.tenant_id != tenant.pk:
            raise CommandError(
                f"Visit {visit.id} has different participants; it was preserved."
            )
        return visit

    def handle(self, *args, **options):
        runtime = getattr(settings, "RENTAL_RUNTIME_ENVIRONMENT", "production")
        if runtime not in {"development", "test", "staging"} or not getattr(
            settings, "OWNER_TENANT_QA_ENABLED", False
        ):
            raise CommandError(
                "QA setup requires an explicitly enabled nonproduction settings module."
            )
        output = Path(options["output"]) if options["output"] else None
        if output and output.exists():
            raise CommandError(
                "Use a new output file; preserve existing manifests and operation journals."
            )
        today = timezone.localdate()
        with transaction.atomic():
            owner, tenant = self._actor(OWNER_ID, "owner"), self._actor(
                TENANT_ID, "tenant"
            )
            gov, _ = Governorate.objects.get_or_create(
                name="Cycle QA Cairo", defaults={"slug": "cycle-qa-cairo"}
            )
            city, _ = City.objects.get_or_create(
                name="Cycle QA City",
                governorate=gov,
                defaults={"slug": "cycle-qa-city"},
            )
            kind, _ = PropertyType.objects.get_or_create(
                slug="cycle-qa-apartment", defaults={"name": "QA apartment"}
            )
            location = {"city": city, "governorate": gov, "property_type": kind}
            prop = self._property(
                PROPERTY_ID,
                owner,
                inventory=qa_inventory(),
                location=location,
                title="Structured cycle QA property",
                price="15000.00",
            )
            legacy_prop = self._property(
                qa_id("legacy-property", owner.id),
                owner,
                inventory={},
                location=location,
                title="Legacy invitation QA property",
                price="15000.00",
            )
            # Deliberate QA verification does not grant payout/provider readiness.
            for item in (prop, legacy_prop):
                item.status = Property.Status.VERIFIED
                item.is_verified = item.is_ownership_verified = True
                item.save(
                    update_fields=[
                        "status",
                        "is_verified",
                        "is_ownership_verified",
                        "updated_at",
                    ]
                )
                for offset in range(1, 22):
                    for hour in (10, 14, 16):
                        OwnerAvailabilitySlot.objects.get_or_create(
                            property=item,
                            date=today + timedelta(days=offset),
                            time=time(hour),
                            defaults={"owner": owner, "is_enabled": True},
                        )
            profile = get_or_create_owner_profile(owner)
            source = self._visit(
                SOURCE_VISIT_ID,
                prop,
                tenant,
                "confirmed",
                today + timedelta(days=2),
                time(10),
            )
            pending = self._visit(
                PENDING_VISIT_ID,
                prop,
                tenant,
                "pending",
                today + timedelta(days=3),
                time(14),
            )
            legacy_source = self._visit(
                qa_id("legacy-source", owner.id),
                legacy_prop,
                tenant,
                "confirmed",
                today + timedelta(days=2),
                time(10),
            )

        offers = (prop.rental_inventory or {}).get("offers", [])
        selected = next(
            (
                item
                for item in offers
                if item.get("rental_scope") == "bed"
                and item.get("availability") == "available"
                and not item.get("archived")
            ),
            None,
        )
        rent = int(Decimal(str(selected["terms"]["price"])) * 100) if selected else None
        manifest = {
            "legacy": {
                "property_id": str(legacy_prop.id),
                "source_visit_id": str(legacy_source.id),
                "draft": {
                    "template_id": "eg-residential-v1",
                    "template_version": "1",
                    "start_date": str(today + timedelta(days=7)),
                    "end_date": str(today + timedelta(days=372)),
                    "rent": {
                        "amount_minor": int(legacy_prop.price * 100),
                        "currency": "EGP",
                        "exponent": 2,
                    },
                },
            },
            "structured": {
                "property_id": str(prop.id),
                "source_visit_id": str(source.id),
                "offer_id": selected["id"] if selected else None,
                "expected_offer_revision": selected["revision"] if selected else None,
                "rent": {"amount_minor": rent, "currency": "EGP", "exponent": 2},
            },
        }
        ad = Advertisement.objects.filter(id=AUDIT_AD_ID, owner=owner).first()
        if ad:
            manifest["banner"] = {
                "advertisement_id": str(ad.id),
                "operation_id": ad.operation.operation_id,
                "mock_operation_id": ad.operation.operation_id + "-payment",
                "artwork_sha256": AUDIT_AD_SHA256,
            }
        extended = {
            "execution_metadata": {
                "utc_execution_time": timezone.now().isoformat(),
                "runtime_environment": runtime,
                "database_engine": connection.vendor,
                "provider_backend": settings.RENTAL_PROVIDER_BACKEND,
                "provider_evidence": (
                    "mock-api-only" if fake_provider_available() else "unavailable"
                ),
            },
            "actors": {
                "owner_a": {
                    "id": str(owner.id),
                    "verified": owner.is_verified,
                    "has_password": owner.has_usable_password(),
                },
                "tenant_a": {
                    "id": str(tenant.id),
                    "verified": tenant.is_verified,
                    "has_password": tenant.has_usable_password(),
                },
            },
            "owner_payment_profile": {
                "id": str(profile.id),
                "status": profile.status,
                "onboarding_available": fake_provider_available()
                and profile.status != "ready",
                "payout_ready": profile.payout_ready,
            },
            "visits": {
                "legacy_source": {
                    "id": str(legacy_source.id),
                    "status": legacy_source.status,
                },
                "structured_source": {"id": str(source.id), "status": source.status},
                "rejection": {"id": str(pending.id), "status": pending.status},
            },
            "checkout_available": checkout_available(),
            "planning": {
                "enabled_capabilities": enabled_services(),
                "verified_services": enabled_services(),
                "allowed_actions": [],
            },
            "historical_snapshot_only_leases": list(
                Lease.objects.filter(id__in=SNAPSHOT_ONLY_LEASE_IDS).values_list(
                    "id", flat=True
                )
            ),
            "full_cycles_verified": False,
            "notes": [
                "Existing passwords, leases, payments, artwork and operation keys were preserved.",
                "Create/sign/pay/hand over through APIs; seeded statuses are not execution evidence.",
                "Preserved rejected/cancelled visits are not reset. Use a new fixture for another intention.",
                "Retain original journal bodies/keys; new fixtures require a separate run.",
                "Provider outcomes are mocked; planning services require explicit environment enablement.",
            ],
        }
        manifest["test_enablement"] = extended
        text = json.dumps(manifest, indent=2, default=str)
        if output:
            with output.open("x", encoding="utf-8") as target:
                target.write(text + "\n")
        self.stdout.write(text)
        if options["print_extended"]:
            self.stdout.write(
                "\n--- EXTENDED MANIFEST ---\n"
                + json.dumps(extended, indent=2, default=str)
            )
