import json
import uuid
from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core_apps.advertising.models import (
    Advertisement,
    AdvertisementMedia,
    AdvertisementOperation,
    AdvertisingPlan,
)
from core_apps.advertising.services import ensure_media_persisted
from core_apps.advertising.audit_asset import (
    AUDIT_AD_BYTE_LEN,
    AUDIT_AD_ID,
    AUDIT_AD_SHA256,
    get_audit_banner_bytes,
)
from core_apps.features.models import OwnerPaymentProfile
from core_apps.features.views import LEASE_TEMPLATES
from core_apps.profiles.models import Profile
from core_apps.properties.models import (
    City,
    Governorate,
    OwnerAvailabilitySlot,
    Property,
    PropertyType,
    PropertyVisit,
)

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Idempotently prepare staging accounts, objects, permissions, and fixtures "
        "required for full owner-tenant cycle test enablement."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            type=str,
            default="",
            help="Optional file path to write runner-compatible fixtures.json",
        )
        parser.add_argument(
            "--print-extended",
            action="store_true",
            help="Print extended QA manifest with secondary actors and scenario mappings.",
        )

    def handle(self, *args, **options):
        # 1. Primary Actors
        owner_a_id = uuid.UUID("3b6d5dd4-2077-4bad-9c59-32717915035e")
        tenant_a_id = uuid.UUID("9eef4201-0ca4-4fc1-b91f-9ef27551c0ea")

        # 2. Secondary Isolation Actors
        owner_b_id = uuid.UUID("4c7e6ee5-3188-5cbe-815a-43828a26146f")
        tenant_b_id = uuid.UUID("af0a5312-1db5-502a-9f20-800a688221fb")

        # 3. Property & Visits
        property_a_id = uuid.UUID("13954644-cc37-49d9-a772-f1a88be81401")
        property_b_id = uuid.UUID("24b94f65-5122-4a0b-99d7-82a87401c102")
        cancelled_visit_id = uuid.UUID("ff1b94d2-3255-43a8-9a99-68735c6c7c6c")
        new_source_visit_id = uuid.UUID("e11a71e0-410a-42b7-a367-9c98867a5412")

        # 4. Advertisement
        ad_id = uuid.UUID(AUDIT_AD_ID)
        op_id = "74682688-4428-413c-a1ae-c4b87222c687"
        mock_payment_op_id = f"{op_id}-payment"

        with transaction.atomic():
            # Ensure Location & PropertyType exist for property creation
            gov, _ = Governorate.objects.get_or_create(
                name="Cairo", defaults={"slug": "cairo"}
            )
            city, _ = City.objects.get_or_create(
                name="Cairo", governorate=gov, defaults={"slug": "cairo-city"}
            )
            prop_type, _ = PropertyType.objects.get_or_create(
                slug="apartment",
                defaults={"name": "Apartment", "description": "Apartment unit"},
            )

            # Owner A
            owner_a, _ = User.objects.get_or_create(
                id=owner_a_id,
                defaults={
                    "email": "owner_a@sokoun.com",
                    "first_name": "Owner",
                    "last_name": "A",
                },
            )
            owner_a.is_active = True
            owner_a.is_verified = True
            owner_a.save(update_fields=["is_active", "is_verified"])
            Profile.objects.get_or_create(
                user=owner_a,
                defaults={
                    "phone_number": "+201000000001",
                    "national_id": "29001011234567",
                    "city": city,
                },
            )
            owner_a_payment_profile, _ = OwnerPaymentProfile.objects.get_or_create(
                owner=owner_a,
                defaults={
                    "status": OwnerPaymentProfile.Status.READY,
                    "payout_ready": True,
                    "accepted_policy_versions": ["rental-policy-v1"],
                    "provider": "mock",
                },
            )
            if (
                owner_a_payment_profile.status != OwnerPaymentProfile.Status.READY
                or not owner_a_payment_profile.payout_ready
            ):
                owner_a_payment_profile.status = OwnerPaymentProfile.Status.READY
                owner_a_payment_profile.payout_ready = True
                owner_a_payment_profile.accepted_policy_versions = ["rental-policy-v1"]
                owner_a_payment_profile.save(
                    update_fields=["status", "payout_ready", "accepted_policy_versions"]
                )

            # Tenant A
            tenant_a, _ = User.objects.get_or_create(
                id=tenant_a_id,
                defaults={
                    "email": "tenant_a@sokoun.com",
                    "first_name": "Tenant",
                    "last_name": "A",
                },
            )
            tenant_a.is_active = True
            tenant_a.is_verified = True
            tenant_a.save(update_fields=["is_active", "is_verified"])
            Profile.objects.get_or_create(
                user=tenant_a,
                defaults={
                    "phone_number": "+201000000002",
                    "national_id": "29501011234568",
                    "city": city,
                },
            )

            # Owner B (Secondary actor)
            owner_b, _ = User.objects.get_or_create(
                id=owner_b_id,
                defaults={
                    "email": "owner_b@sokoun.com",
                    "first_name": "Owner",
                    "last_name": "B",
                },
            )
            owner_b.is_active = True
            owner_b.is_verified = True
            owner_b.save(update_fields=["is_active", "is_verified"])
            Profile.objects.get_or_create(
                user=owner_b,
                defaults={
                    "phone_number": "+201000000003",
                    "national_id": "29001011234569",
                    "city": city,
                },
            )
            OwnerPaymentProfile.objects.get_or_create(
                owner=owner_b,
                defaults={
                    "status": OwnerPaymentProfile.Status.READY,
                    "payout_ready": True,
                    "accepted_policy_versions": ["rental-policy-v1"],
                    "provider": "mock",
                },
            )

            # Tenant B (Secondary actor)
            tenant_b, _ = User.objects.get_or_create(
                id=tenant_b_id,
                defaults={
                    "email": "tenant_b@sokoun.com",
                    "first_name": "Tenant",
                    "last_name": "B",
                },
            )
            tenant_b.is_active = True
            tenant_b.is_verified = True
            tenant_b.save(update_fields=["is_active", "is_verified"])
            Profile.objects.get_or_create(
                user=tenant_b,
                defaults={
                    "phone_number": "+201000000004",
                    "national_id": "29501011234570",
                    "city": city,
                },
            )

            # Property A
            offer_bed_id = "e0000001-0000-0000-0000-000000000001"
            offer_room_id = "e0000002-0000-0000-0000-000000000002"
            room_1_id = "r0000001-0000-0000-0000-000000000001"
            bed_1_id = "b0000001-0000-0000-0000-000000000001"

            rental_inventory = {
                "schema_version": 1,
                "revision": 1,
                "mode": "partial",
                "rooms": [
                    {
                        "id": room_1_id,
                        "name": "Master Room",
                        "capacity": 2,
                        "beds": [{"id": bed_1_id, "name": "Single Bed 1"}],
                    }
                ],
                "offers": [
                    {
                        "id": offer_bed_id,
                        "revision": 1,
                        "rental_scope": "bed",
                        "name": "Bed Space Offer",
                        "room_ids": [room_1_id],
                        "bed_id": bed_1_id,
                        "availability": "available",
                        "archived": False,
                        "terms": {"price": "1500.00", "price_period": "monthly"},
                    },
                    {
                        "id": offer_room_id,
                        "revision": 1,
                        "rental_scope": "room",
                        "name": "Private Room Offer",
                        "room_ids": [room_1_id],
                        "availability": "available",
                        "archived": False,
                        "terms": {"price": "3000.00", "price_period": "monthly"},
                    },
                ],
            }

            prop_a, _ = Property.objects.get_or_create(
                id=property_a_id,
                defaults={
                    "owner": owner_a,
                    "title": "Zamalek Residence Luxury Suite",
                    "description": "Premium serviced flat for full cycle verification.",
                    "price": 15000.00,
                    "price_period": Property.PricePeriod.MONTHLY,
                    "property_type": prop_type,
                    "city": city,
                    "governorate": gov,
                    "district": "Zamalek",
                    "status": Property.Status.VERIFIED,
                    "is_verified": True,
                    "bedrooms": 2,
                    "bathrooms": 1,
                    "rental_inventory": rental_inventory,
                },
            )
            # Ensure owner and verified flags are intact
            prop_a.owner = owner_a
            prop_a.status = Property.Status.VERIFIED
            prop_a.is_verified = True
            if not prop_a.rental_inventory:
                prop_a.rental_inventory = rental_inventory
            prop_a.save()

            # Property B (Owned by Owner B)
            prop_b, _ = Property.objects.get_or_create(
                id=property_b_id,
                defaults={
                    "owner": owner_b,
                    "title": "Maadi Garden View Apartment",
                    "description": "Secondary isolation test property.",
                    "price": 12000.00,
                    "price_period": Property.PricePeriod.MONTHLY,
                    "property_type": prop_type,
                    "city": city,
                    "governorate": gov,
                    "district": "Maadi",
                    "status": Property.Status.VERIFIED,
                    "is_verified": True,
                    "bedrooms": 1,
                    "bathrooms": 1,
                },
            )
            prop_b.owner = owner_b
            prop_b.status = Property.Status.VERIFIED
            prop_b.is_verified = True
            prop_b.save()

            # Future Availability Slots for Property A (next 14 days)
            today = timezone.localdate()
            for day_offset in range(1, 15):
                slot_date = today + timedelta(days=day_offset)
                for slot_time in [time(10, 0), time(14, 0), time(16, 0)]:
                    OwnerAvailabilitySlot.objects.get_or_create(
                        property=prop_a,
                        owner=owner_a,
                        date=slot_date,
                        time=slot_time,
                        defaults={"is_enabled": True},
                    )

            # Ineligible Cancelled Visit (preserved denial fixture)
            PropertyVisit.objects.get_or_create(
                id=cancelled_visit_id,
                defaults={
                    "property": prop_a,
                    "tenant": tenant_a,
                    "visit_date": today - timedelta(days=2),
                    "visit_time": time(12, 0),
                    "status": PropertyVisit.Status.CANCELED,
                    "note": "Preserved negative cancellation fixture",
                },
            )

            # Fresh Eligible Source Visit for C03 positive path
            fresh_visit_date = today + timedelta(days=1)
            fresh_visit_time = time(11, 0)
            fresh_visit, _ = PropertyVisit.objects.get_or_create(
                id=new_source_visit_id,
                defaults={
                    "property": prop_a,
                    "tenant": tenant_a,
                    "visit_date": fresh_visit_date,
                    "visit_time": fresh_visit_time,
                    "status": PropertyVisit.Status.CONFIRMED,
                    "note": "Prepared eligible source visit for C03 QA regression",
                },
            )
            if fresh_visit.status != PropertyVisit.Status.CONFIRMED:
                fresh_visit.status = PropertyVisit.Status.CONFIRMED
                fresh_visit.save(update_fields=["status"])

            # Original Banner Advertisement (OPEN-01)
            ad_plan, _ = AdvertisingPlan.objects.get_or_create(
                id="plan_tenant_home_1w",
                defaults={
                    "title_en": "Tenant Home 1 Week",
                    "title_ar": "الصفحة الرئيسية للمستأجر أسبوع واحد",
                    "duration_unit": AdvertisingPlan.DurationUnit.WEEK,
                    "duration_count": 1,
                    "amount_minor": 50000,
                    "currency": "EGP",
                    "exponent": 2,
                    "active": True,
                },
            )
            ad_op, _ = AdvertisementOperation.objects.get_or_create(
                owner=owner_a,
                operation_id=op_id,
                defaults={
                    "state": AdvertisementOperation.State.FOUND,
                    "retry_allowed": True,
                },
            )
            ad, _ = Advertisement.objects.get_or_create(
                id=ad_id,
                defaults={
                    "owner": owner_a,
                    "operation": ad_op,
                    "property": prop_a,
                    "title": "Audit Original Banner Advertisement",
                    "description": "Persisted brand banner for full cycle verification",
                    "placement": Advertisement.PLACEMENT_TENANT_HOME,
                    "plan_snapshot": {
                        "id": ad_plan.id,
                        "title_en": ad_plan.title_en,
                        "title_ar": ad_plan.title_ar,
                        "amount_minor": ad_plan.amount_minor,
                        "currency": ad_plan.currency,
                        "exponent": ad_plan.exponent,
                    },
                    "status": Advertisement.Status.PENDING_PAYMENT,
                },
            )
            media, _ = AdvertisementMedia.objects.get_or_create(
                advertisement=ad,
                defaults={
                    "sha256": AUDIT_AD_SHA256,
                    "size_bytes": AUDIT_AD_BYTE_LEN,
                    "content_type": "image/png",
                },
            )
            if not media.banner:
                from django.core.files.base import ContentFile

                media.banner.save(
                    "original_audit_logo.png",
                    ContentFile(get_audit_banner_bytes()),
                    save=False,
                )
                media.sha256 = AUDIT_AD_SHA256
                media.size_bytes = AUDIT_AD_BYTE_LEN
                media.content_type = "image/png"
                media.save()
            ensure_media_persisted(media)

        # Build runner-compatible fixtures.json
        start_date = (today + timedelta(days=2)).isoformat()
        end_date = (today + timedelta(days=367)).isoformat()
        template_id = LEASE_TEMPLATES[0]["id"]
        template_version = LEASE_TEMPLATES[0]["version"]

        fixtures_data = {
            "legacy": {
                "property_id": str(property_a_id),
                "source_visit_id": str(new_source_visit_id),
                "draft": {
                    "template_id": template_id,
                    "template_version": template_version,
                    "start_date": start_date,
                    "end_date": end_date,
                    "rent": {
                        "amount_minor": 150000,
                        "currency": "EGP",
                        "exponent": 2,
                    },
                },
            },
            "banner": {
                "advertisement_id": str(ad_id),
                "operation_id": op_id,
                "mock_operation_id": mock_payment_op_id,
                "artwork_sha256": AUDIT_AD_SHA256,
            },
        }

        output_path = options.get("output")
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(fixtures_data, f, indent=2)
            self.stdout.write(
                self.style.SUCCESS(f"Saved runner fixtures to {output_path}")
            )

        self.stdout.write(json.dumps(fixtures_data, indent=2))

        if options.get("print_extended"):
            extended_manifest = {
                "primary_actors": {
                    "owner_a": {
                        "id": str(owner_a_id),
                        "email": owner_a.email,
                        "verified": owner_a.is_verified,
                        "payment_profile_ready": True,
                    },
                    "tenant_a": {
                        "id": str(tenant_a_id),
                        "email": tenant_a.email,
                        "verified": tenant_a.is_verified,
                    },
                },
                "secondary_actors": {
                    "owner_b": {
                        "id": str(owner_b_id),
                        "email": owner_b.email,
                        "verified": owner_b.is_verified,
                    },
                    "tenant_b": {
                        "id": str(tenant_b_id),
                        "email": tenant_b.email,
                        "verified": tenant_b.is_verified,
                    },
                },
                "properties": {
                    "property_a": {
                        "id": str(property_a_id),
                        "owner_id": str(owner_a_id),
                        "status": prop_a.status,
                        "verified": prop_a.is_verified,
                        "structured_inventory": {
                            "offer_bed_id": offer_bed_id,
                            "offer_room_id": offer_room_id,
                            "room_id": room_1_id,
                            "bed_id": bed_1_id,
                        },
                    },
                    "property_b": {
                        "id": str(property_b_id),
                        "owner_id": str(owner_b_id),
                        "status": prop_b.status,
                        "verified": prop_b.is_verified,
                    },
                },
                "visits": {
                    "cancelled_negative_fixture": str(cancelled_visit_id),
                    "eligible_source_visit": str(new_source_visit_id),
                },
                "banner": {
                    "advertisement_id": str(ad_id),
                    "operation_id": op_id,
                    "mock_payment_op_id": mock_payment_op_id,
                    "artwork_sha256": AUDIT_AD_SHA256,
                    "artwork_bytes": AUDIT_AD_BYTE_LEN,
                },
            }
            self.stdout.write("\n--- EXTENDED MANIFEST ---\n")
            self.stdout.write(json.dumps(extended_manifest, indent=2))
