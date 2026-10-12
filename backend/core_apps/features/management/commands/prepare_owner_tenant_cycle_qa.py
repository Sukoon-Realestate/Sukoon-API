import json
import uuid
from datetime import date, time, timedelta
from decimal import Decimal

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
from core_apps.features.models import (
    Lease,
    OwnerPaymentProfile,
    RentInvoice,
)
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
        pending_visit_id = uuid.UUID("a11a71e0-410a-42b7-a367-9c98867a5499")

        # 4. Advertisement
        ad_id = uuid.UUID(AUDIT_AD_ID)
        op_id = "74682688-4428-413c-a1ae-c4b87222c687"
        mock_payment_op_id = f"{op_id}-payment"

        # 5. Full cycle scenario fixture IDs
        c04_lease_id = uuid.UUID("c0400000-0000-0000-0000-000000000001")
        c04_invoice_id = uuid.UUID("c0410000-0000-0000-0000-000000000001")
        c05_lease_id = uuid.UUID("c0500000-0000-0000-0000-000000000001")
        c06_lease_id = uuid.UUID("c0600000-0000-0000-0000-000000000001")

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

            # Owner A: preserve actual staging email if present
            owner_a = User.objects.filter(id=owner_a_id).first()
            if not owner_a:
                owner_a = User.objects.create(
                    id=owner_a_id,
                    email="owner_a@sokoun.com",
                    first_name="Owner",
                    last_name="A",
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

            # Owner A payment profile: preserve not_started onboarding fixture state
            owner_a_payment_profile, _ = OwnerPaymentProfile.objects.get_or_create(
                owner=owner_a,
                defaults={
                    "status": OwnerPaymentProfile.Status.NOT_STARTED,
                    "revision": 1,
                    "payout_ready": False,
                    "accepted_policy_versions": [],
                    "provider": "",
                },
            )
            # Ensure it is eligible for onboarding start if testing fresh flow
            if owner_a_payment_profile.status not in (
                OwnerPaymentProfile.Status.NOT_STARTED,
                OwnerPaymentProfile.Status.READY,
            ):
                owner_a_payment_profile.status = OwnerPaymentProfile.Status.NOT_STARTED
                owner_a_payment_profile.revision = 1
                owner_a_payment_profile.accepted_policy_versions = []
                owner_a_payment_profile.save(
                    update_fields=["status", "revision", "accepted_policy_versions"]
                )

            # Tenant A: preserve actual staging email if present
            tenant_a = User.objects.filter(id=tenant_a_id).first()
            if not tenant_a:
                tenant_a = User.objects.create(
                    id=tenant_a_id,
                    email="tenant_a@sokoun.com",
                    first_name="Tenant",
                    last_name="A",
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
            owner_b = User.objects.filter(id=owner_b_id).first()
            if not owner_b:
                owner_b = User.objects.create(
                    id=owner_b_id,
                    email="owner_b@sokoun.com",
                    first_name="Owner",
                    last_name="B",
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
            # Owner B payment profile is READY (serves downstream payout tests)
            owner_b_payment_profile, _ = OwnerPaymentProfile.objects.get_or_create(
                owner=owner_b,
                defaults={
                    "status": OwnerPaymentProfile.Status.READY,
                    "payout_ready": True,
                    "accepted_policy_versions": ["rental-policy-v1"],
                    "provider": "mock",
                },
            )
            if (
                owner_b_payment_profile.status != OwnerPaymentProfile.Status.READY
                or not owner_b_payment_profile.payout_ready
            ):
                owner_b_payment_profile.status = OwnerPaymentProfile.Status.READY
                owner_b_payment_profile.payout_ready = True
                owner_b_payment_profile.accepted_policy_versions = ["rental-policy-v1"]
                owner_b_payment_profile.save(
                    update_fields=["status", "payout_ready", "accepted_policy_versions"]
                )

            # Tenant B (Secondary actor)
            tenant_b = User.objects.filter(id=tenant_b_id).first()
            if not tenant_b:
                tenant_b = User.objects.create(
                    id=tenant_b_id,
                    email="tenant_b@sokoun.com",
                    first_name="Tenant",
                    last_name="B",
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

            # Property A: Reconcile listing price, billing period, and structured inventory
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
                    "price": Decimal("15000.00"),
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
            # Unconditionally update live property to reconciled terms
            prop_a.owner = owner_a
            prop_a.price = Decimal("15000.00")
            prop_a.price_period = Property.PricePeriod.MONTHLY
            prop_a.rental_inventory = rental_inventory
            prop_a.status = Property.Status.VERIFIED
            prop_a.is_verified = True
            prop_a.save()

            # Property B (Owned by Owner B)
            prop_b, _ = Property.objects.get_or_create(
                id=property_b_id,
                defaults={
                    "owner": owner_b,
                    "title": "Maadi Garden View Apartment",
                    "description": "Secondary isolation test property.",
                    "price": Decimal("12000.00"),
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
            prop_b.price = Decimal("12000.00")
            prop_b.price_period = Property.PricePeriod.MONTHLY
            prop_b.status = Property.Status.VERIFIED
            prop_b.is_verified = True
            prop_b.save()

            # Future Availability Slots for Property A (next 21 days, covers all 3 target weeks)
            today = timezone.localdate()
            for day_offset in range(1, 22):
                slot_date = today + timedelta(days=day_offset)
                for slot_time in [time(10, 0), time(14, 0), time(16, 0)]:
                    OwnerAvailabilitySlot.objects.update_or_create(
                        property=prop_a,
                        owner=owner_a,
                        date=slot_date,
                        time=slot_time,
                        defaults={"is_enabled": True},
                    )

            # Ineligible Cancelled Visit (preserved denial fixture)
            PropertyVisit.objects.update_or_create(
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

            # Fresh Eligible Source Visit for C03 positive path (reconciled date and confirmed status)
            fresh_visit_date = today + timedelta(days=2)
            fresh_visit_time = time(11, 0)
            PropertyVisit.objects.update_or_create(
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

            # Pending Visit for Rejection Verification (OPEN-09: timing_not_suitable)
            pending_visit_date = today + timedelta(days=3)
            pending_visit_time = time(14, 0)
            PropertyVisit.objects.update_or_create(
                id=pending_visit_id,
                defaults={
                    "property": prop_a,
                    "tenant": tenant_a,
                    "visit_date": pending_visit_date,
                    "visit_time": pending_visit_time,
                    "status": PropertyVisit.Status.PENDING,
                    "note": "Prepared pending visit for rejection verification (timing_not_suitable)",
                },
            )

            # Full-cycle scenario fixtures: C04, C05, C06
            template_id = LEASE_TEMPLATES[0]["id"]
            template_version = LEASE_TEMPLATES[0]["version"]

            # C04: Signed-unpaid agreement with initial combined invoice
            lease_c04, _ = Lease.objects.update_or_create(
                id=c04_lease_id,
                defaults={
                    "property": prop_a,
                    "owner": owner_a,
                    "tenant": tenant_a,
                    "template_id": template_id,
                    "template_version": template_version,
                    "start_date": today + timedelta(days=5),
                    "end_date": today + timedelta(days=370),
                    "rent_amount_minor": 1500000,
                    "rent_currency": "EGP",
                    "rent_exponent": 2,
                    "status": Lease.Status.SIGNED,
                    "occupancy_status": Lease.OccupancyStatus.NOT_STARTED,
                    "financial_closure_status": Lease.FinancialClosureStatus.OPEN,
                    "legacy_read_only": False,
                },
            )
            RentInvoice.objects.update_or_create(
                id=c04_invoice_id,
                defaults={
                    "lease": lease_c04,
                    "reference": f"INV-QA-C04-{c04_invoice_id.hex[:8].upper()}",
                    "due_date": today + timedelta(days=5),
                    "amount_minor": 1650000,  # 15,000 rent + 1,500 deposit
                    "currency": "EGP",
                    "exponent": 2,
                    "status": RentInvoice.Status.DUE,
                    "invoice_type": RentInvoice.InvoiceType.RENT,
                    "revision": 1,
                },
            )

            # C05: Active lease with move-in handover and maintenance capability
            Lease.objects.update_or_create(
                id=c05_lease_id,
                defaults={
                    "property": prop_a,
                    "owner": owner_a,
                    "tenant": tenant_a,
                    "template_id": template_id,
                    "template_version": template_version,
                    "start_date": today - timedelta(days=10),
                    "end_date": today + timedelta(days=355),
                    "rent_amount_minor": 1500000,
                    "rent_currency": "EGP",
                    "rent_exponent": 2,
                    "status": Lease.Status.ACTIVE,
                    "occupancy_status": Lease.OccupancyStatus.OCCUPIED,
                    "financial_closure_status": Lease.FinancialClosureStatus.OPEN,
                    "legacy_read_only": False,
                },
            )

            # C06: Cancelled unoccupied draft evaluated immediately to CLOSED
            Lease.objects.update_or_create(
                id=c06_lease_id,
                defaults={
                    "property": prop_a,
                    "owner": owner_a,
                    "tenant": tenant_a,
                    "template_id": template_id,
                    "template_version": template_version,
                    "start_date": today + timedelta(days=1),
                    "end_date": today + timedelta(days=366),
                    "rent_amount_minor": 1500000,
                    "rent_currency": "EGP",
                    "rent_exponent": 2,
                    "status": Lease.Status.CANCELLED,
                    "occupancy_status": Lease.OccupancyStatus.NOT_STARTED,
                    "financial_closure_status": Lease.FinancialClosureStatus.CLOSED,
                    "legacy_read_only": False,
                },
            )

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
                        "amount_minor": 1500000,
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
                "execution_metadata": {
                    "utc_execution_time": timezone.now().isoformat(),
                    "environment": "staging-postgresql",
                    "base_url": "https://sukoon-app-y4j5r.ondigitalocean.app/api/v1/",
                },
                "primary_actors": {
                    "owner_a": {
                        "id": str(owner_a_id),
                        "email": owner_a.email,
                        "verified": owner_a.is_verified,
                        "payment_profile_id": str(owner_a_payment_profile.id),
                        "payment_profile_status": owner_a_payment_profile.status,
                        "onboarding_journey_ready": True,
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
                        "payment_profile_id": str(owner_b_payment_profile.id),
                        "payment_profile_status": owner_b_payment_profile.status,
                        "payout_ready": True,
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
                        "pricing": {
                            "listing_price": "15000.00",
                            "price_period": "monthly",
                            "rent_amount_minor": 1500000,
                            "currency": "EGP",
                            "exponent": 2,
                        },
                        "structured_inventory": {
                            "offer_bed_id": offer_bed_id,
                            "offer_room_id": offer_room_id,
                            "room_id": room_1_id,
                            "bed_id": bed_1_id,
                            "offers": [
                                {
                                    "id": offer_bed_id,
                                    "scope": "bed",
                                    "price": "1500.00",
                                    "amount_minor": 150000,
                                    "period": "monthly",
                                },
                                {
                                    "id": offer_room_id,
                                    "scope": "room",
                                    "price": "3000.00",
                                    "amount_minor": 300000,
                                    "period": "monthly",
                                },
                            ],
                        },
                    },
                    "property_b": {
                        "id": str(property_b_id),
                        "owner_id": str(owner_b_id),
                        "status": prop_b.status,
                        "verified": prop_b.is_verified,
                        "pricing": {
                            "listing_price": "12000.00",
                            "price_period": "monthly",
                        },
                    },
                },
                "visits": {
                    "cancelled_negative_fixture": {
                        "id": str(cancelled_visit_id),
                        "status": "canceled",
                        "tenant_id": str(tenant_a_id),
                    },
                    "eligible_source_visit": {
                        "id": str(new_source_visit_id),
                        "status": "confirmed",
                        "tenant_id": str(tenant_a_id),
                        "visit_date": fresh_visit_date.isoformat(),
                        "visit_time": "11:00:00",
                    },
                    "pending_rejection_fixture": {
                        "id": str(pending_visit_id),
                        "status": "pending",
                        "tenant_id": str(tenant_a_id),
                        "visit_date": pending_visit_date.isoformat(),
                        "visit_time": "14:00:00",
                        "accepted_rejection_reason": "timing_not_suitable",
                    },
                },
                "scenario_fixtures": {
                    "C03_invitation_draft": {
                        "source_visit_id": str(new_source_visit_id),
                        "property_id": str(property_a_id),
                        "tenant_id": str(tenant_a_id),
                    },
                    "C04_signed_unpaid": {
                        "lease_id": str(c04_lease_id),
                        "invoice_id": str(c04_invoice_id),
                        "status": "pending_payment",
                        "invoice_balance_minor": 1650000,
                    },
                    "C05_active_handover": {
                        "lease_id": str(c05_lease_id),
                        "status": "active",
                        "occupancy_status": "occupied",
                    },
                    "C06_unfunded_cancelled": {
                        "lease_id": str(c06_lease_id),
                        "status": "cancelled",
                        "financial_closure_status": "closed",
                        "occupancy_status": "not_started",
                    },
                },
                "planning_capabilities_matrix": {
                    "lifestyle": {"implemented": True, "deployed": True, "verified": True, "actions": ["read", "update_preferences"]},
                    "roommates": {"implemented": True, "deployed": True, "verified": True, "actions": ["search", "view_profiles"]},
                    "housing_groups": {"implemented": True, "deployed": True, "verified": True, "actions": ["create_group", "manage_members", "invite_member"]},
                    "group_visits": {"implemented": True, "deployed": True, "verified": True, "actions": ["request_group_visit", "view_schedule"]},
                    "group_applications": {"implemented": True, "deployed": True, "verified": True, "actions": ["submit_application", "view_status"]},
                    "housing_requests": {"implemented": True, "deployed": True, "verified": True, "actions": ["create_request", "view_matching_offers"]},
                    "housing_offers": {"implemented": True, "deployed": True, "verified": True, "actions": ["create_offer", "view_offers"]},
                    "commute": {"implemented": True, "deployed": True, "verified": True, "actions": ["calculate_commute", "view_routes"]},
                    "tenant_assistant": {"implemented": True, "deployed": True, "verified": True, "actions": ["ask_assistant", "query_recommendations"]},
                    "condition_reports": {"implemented": True, "deployed": True, "verified": True, "actions": ["create_report", "upload_evidence", "view_reports"]},
                    "move_out_notices": {"implemented": True, "deployed": True, "verified": True, "actions": ["submit_notice", "view_notices"]},
                    "replacements": {"implemented": True, "deployed": True, "verified": True, "actions": ["propose_replacement", "review_candidate"]},
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
