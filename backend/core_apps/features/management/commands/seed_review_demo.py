"""Explicitly local synthetic review fixtures; never modify real rental records."""

from datetime import timedelta
from uuid import uuid4
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from core_apps.users.models import User
from core_apps.properties.models import Property, PropertyType, Governorate, City
from core_apps.features.models import Lease, RentalHandover, Company, CompanyMembership
from core_apps.features.services.reputation.generation import (
    generate_tenancy,
    generate_housemates,
)


class Command(BaseCommand):
    help = "Create local personal occupancy, student, housemate and gated corporate fixtures."

    def add_arguments(self, parser):
        parser.add_argument("--confirm-local", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        if not options["confirm_local"] or not (settings.DEBUG):
            raise CommandError("Requires local DEBUG settings and --confirm-local.")
        if Lease.objects.filter(template_id="rating-demo").exists():
            self.stdout.write(
                "Demo already exists; no duplicate source or notification created."
            )
            return
        users = []
        for name in [
            "owner",
            "tenant",
            "student",
            "housemate",
            "company-admin-a",
            "company-admin-b",
            "employee",
        ]:
            user, _ = User.objects.get_or_create(
                email=f"rating-demo-{name}@example.test",
                defaults={"first_name": f"Demo {name}", "is_verified": True},
            )
            user.set_unusable_password()
            user.save()
            users.append(user)
        governorate, _ = Governorate.objects.get_or_create(name="Synthetic review demo")
        city, _ = City.objects.get_or_create(
            name="Synthetic review city", governorate=governorate
        )
        property_type, _ = PropertyType.objects.get_or_create(
            slug="review-demo", defaults={"name": "Synthetic demo"}
        )
        prop = Property.objects.create(
            owner=users[0],
            title="Synthetic local review demo",
            price=1000,
            property_type=property_type,
            governorate=governorate,
            city=city,
            district="Demo",
            status="verified",
        )
        now = timezone.now()
        leases = []
        for occupant in [*users[1:4], users[-1]]:
            lease = Lease.objects.create(
                owner=users[0],
                tenant=occupant,
                property=prop,
                template_id="rating-demo",
                template_version="1",
                start_date=now.date() - timedelta(days=10),
                end_date=now.date(),
                rent_amount_minor=1000,
                status="ended",
                occupancy_status="returned",
                legacy_read_only=False,
                offer_id=str(uuid4()),
                offer_snapshot={"rental_scope": "room", "room_ids": [str(uuid4())]},
            )
            for kind, day, recorded in [
                ("move_in", lease.start_date, now - timedelta(days=10)),
                ("move_out", lease.end_date, now),
            ]:
                RentalHandover.objects.create(
                    lease=lease,
                    kind=kind,
                    possession_on=day,
                    status="accepted",
                    accepted_at=recorded,
                    approvals=[str(users[0].id), str(occupant.id)],
                )
            generate_tenancy(lease)
            leases.append(lease)
        for index, lease in enumerate(leases):
            for peer in leases[index + 1 :]:
                generate_housemates(lease, peer)
        company, _ = Company.objects.get_or_create(
            registration_number="LOCAL-RATING-DEMO",
            defaults={
                "name": "Synthetic review company",
                "contact_email": "rating-demo-company@example.test",
            },
        )
        for member in users[4:]:
            CompanyMembership.objects.get_or_create(
                company=company,
                user=member,
                defaults={
                    "is_admin": member != users[-1],
                    "is_employee": member == users[-1],
                },
            )
        self.stdout.write(
            "Created four personal stays and six co-living pairs. Student is a demo label, not an enrollment assertion. The employed occupant uses a personal lease; no corporate review opportunities are generated. Accounts have unusable passwords; no external push sent."
        )
