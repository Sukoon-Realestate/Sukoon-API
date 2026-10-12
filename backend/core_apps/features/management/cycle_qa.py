"""Run-scoped, additive fixtures; all business transitions still run via APIs."""

import json
import os
import re
import secrets
import uuid
from datetime import datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

from django.core.management.base import CommandError
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from core_apps.admin_api.models import StaffProfile
from core_apps.features.services.planning import selection_payload
from core_apps.features.services.rental_phase2 import get_or_create_owner_profile
from core_apps.features.services.tenancy_invitations import (
    InvitationConflict,
    resolve_offer_snapshot,
)
from core_apps.properties.models import (
    City,
    Governorate,
    OwnerAvailabilitySlot,
    Property,
    PropertyType,
    PropertyVisit,
)
from core_apps.users.models import User


ACTORS = {
    "owner_a": None,
    "owner_b": None,
    "tenant_a": None,
    "tenant_b": None,
    "group_member": None,
    "replacement_candidate": None,
    "payout_operator": StaffProfile.RoleName.PAYOUT_OPERATOR,
    "refund_operator": StaffProfile.RoleName.REFUND_OPERATOR,
    "dispute_operator": StaffProfile.RoleName.DISPUTE_RESOLVER,
    "property_reviewer": StaffProfile.RoleName.PROPERTY_REVIEWER,
}
BRANCHES = (
    "structured",
    "visits",
    "group",
    "housing_request",
    "discovery_property",
    "renewal",
    "replacement",
    "exit",
    "cancellations",
    "secondary_owner",
    "room",
    "room_group",
    "bed",
    "legacy",
)


def resource_id(run_id, name):
    return uuid.uuid5(uuid.NAMESPACE_URL, f"sokoun-cycle-run:{run_id}:{name}")


def money(amount):
    return {"amount_minor": amount, "currency": "EGP", "exponent": 2}


def agreement_terms(start, end, rent=1_000_000):
    return {
        "starts_on": str(start),
        "ends_on_exclusive": str(end),
        "handover_on": str(start),
        "monthly_rent": money(rent),
        "deposit": money(rent),
        "deposit_holder": "platform",
        "included_services": [],
        "excluded_services": [],
        "termination_policy": {"notice_days": 30},
        "renewal_policy": {"automatic": False},
        "policy_version": "rental-policy-v1",
        "template_id": "eg-residential-v1",
        "template_version": "1",
        "timezone": "Africa/Cairo",
        "occupants": 1,
        "billing_anchor_day": start.day,
        "commission_rate_bps": 1000,
        "commission_payer": "owner",
        "commission_basis": "first_period_base_rent",
        "processing_fee_payer": "platform",
        "renewal_commission_rate_bps": 0,
    }


def inventory_for(run_id, branch):
    if branch == "legacy":
        return {}
    scope = branch if branch in {"room", "room_group", "bed"} else "entire_property"
    rooms = [
        {
            "id": str(resource_id(run_id, f"{branch}:room:{index}")),
            "name": f"QA room {index}",
            "capacity": 2,
            "beds": [
                {
                    "id": str(resource_id(run_id, f"{branch}:bed:{index}")),
                    "name": f"QA bed {index}",
                }
            ],
        }
        for index in (1, 2)
    ]
    room_ids = [room["id"] for room in rooms]
    if scope in {"room", "bed"}:
        room_ids = room_ids[:1]
    if scope == "entire_property":
        rooms, room_ids = [], []
    offer = {
        "id": str(resource_id(run_id, f"{branch}:offer")),
        "revision": 1,
        "rental_scope": scope,
        "name": f"QA {branch} offer",
        "room_ids": room_ids,
        "capacity": 1 if scope == "bed" else 2,
        "availability": "available",
        "archived": False,
        "terms": {
            "price": "10000.00",
            "price_period": "monthly",
            "rental_period": 1,
            "deposit": "one_month",
            "suitable_for": "all",
            "description": "Isolated owner and tenant connected cycle accommodation.",
            "smoking_allowed": False,
            "rules": [],
        },
    }
    if scope == "bed":
        offer["bed_id"] = rooms[0]["beds"][0]["id"]
    return {
        "schema_version": 1,
        "revision": 1,
        "mode": "whole" if scope == "entire_property" else "partial",
        "rooms": rooms,
        "offers": [offer],
    }


def write_private_json(path, value):
    """Exclusive creation prevents overwriting journals or following symlinks."""
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as target:
        json.dump(value, target, indent=2, default=str)
        target.write("\n")


def prepare_cycle_run(run_id, credentials_output=""):
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,39}", run_id):
        raise CommandError(
            "run-id must be 1-40 lowercase letters, digits, underscores or hyphens."
        )
    credentials_path = Path(credentials_output) if credentials_output else None
    if credentials_path and (
        credentials_path.exists() or credentials_path.is_symlink()
    ):
        raise CommandError(
            "Use a new credentials output file; existing secrets were preserved."
        )
    actor_ids = [resource_id(run_id, f"actor:{alias}") for alias in ACTORS]
    missing = User.objects.filter(id__in=actor_ids).count() != len(actor_ids)
    if missing and not credentials_path:
        raise CommandError(
            "A new run requires --credentials-output for private generated credentials."
        )

    credentials = {}
    created_credential_file = False
    try:
        with transaction.atomic():
            actors = {}
            for alias, role in ACTORS.items():
                email = f"cycle-{run_id}-{alias.replace('_', '-')}@example.test"
                actor, created = User.objects.get_or_create(
                    id=resource_id(run_id, f"actor:{alias}"),
                    defaults={
                        "email": email,
                        "first_name": "Cycle QA",
                        "last_name": alias,
                        "is_active": True,
                        "is_verified": True,
                    },
                )
                if actor.email != email or actor.is_staff or actor.is_superuser:
                    raise CommandError(
                        f"Run actor {alias} does not match this isolated fixture; preserved."
                    )
                if created:
                    password = secrets.token_urlsafe(24)
                    actor.set_password(password)
                    actor.save(update_fields=["password"])
                    credentials[alias] = {
                        "id": str(actor.id),
                        "email": email,
                        "password": password,
                    }
                    if role:
                        StaffProfile.objects.create(user=actor, role_name=role)
                elif role:
                    profile = StaffProfile.objects.filter(user=actor).first()
                    if not profile or profile.role_name != role:
                        raise CommandError(
                            f"Run operator {alias} changed roles; no permissions were modified."
                        )
                elif StaffProfile.objects.filter(user=actor).exists():
                    raise CommandError(
                        f"Ordinary run actor {alias} has an operations role; preserved."
                    )
                actors[alias] = actor

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
            manifest = {
                "fixture_version": 2,
                "run_id": run_id,
                "actors": {
                    alias: {"id": str(actor.id), "email": actor.email}
                    for alias, actor in actors.items()
                },
                "test_enablement": {
                    "actors": {
                        alias: {
                            "id": str(actor.id),
                            "email": actor.email,
                            "verified": actor.is_verified,
                            "active": actor.is_active,
                            "has_password": actor.has_usable_password(),
                        }
                        for alias, actor in actors.items()
                    },
                    "full_cycles_verified": False,
                    "notes": [
                        "Only fresh accounts, property inventory and availability are seeded.",
                        "Legacy/structured source visits are eligibility fixtures, not completed-journey evidence.",
                        "Reruns preserve passwords, account flags, permissions and all existing business records.",
                        "Execute onboarding, moderation, consent, signatures, payment and closure through APIs.",
                    ],
                },
            }
            for branch in BRANCHES:
                owner = actors["owner_b" if branch == "secondary_owner" else "owner_a"]
                prop, _ = Property.objects.get_or_create(
                    id=resource_id(run_id, f"property:{branch}"),
                    defaults={
                        "owner": owner,
                        "title": f"QA {run_id} {branch}",
                        "description": "Isolated owner and tenant connected cycle accommodation.",
                        "price": Decimal("10000.00"),
                        "price_period": "monthly",
                        "governorate": gov,
                        "city": city,
                        "property_type": kind,
                        "district": "QA",
                        "latitude": Decimal("30.040000"),
                        "longitude": Decimal("31.230000"),
                        "status": Property.Status.VERIFIED,
                        "is_verified": True,
                        "is_ownership_verified": True,
                        "bedrooms": 2,
                        "bathrooms": 1,
                        "rental_inventory": inventory_for(run_id, branch),
                    },
                )
                if prop.owner_id != owner.pk:
                    raise CommandError(
                        f"Run property {branch} has a different owner; preserved."
                    )
                # A fixture's original dates survive a midnight rerun.
                today = timezone.localtime(prop.created_at).date()
                start = today if branch == "exit" else today + timedelta(days=1)
                end = start + timedelta(days=31)
                appointment_date = today + timedelta(days=1)
                for offset in range(1, 8):
                    for hour in (10, 14, 16):
                        OwnerAvailabilitySlot.objects.get_or_create(
                            property=prop,
                            date=today + timedelta(days=offset),
                            time=time(hour),
                            defaults={"owner": owner, "is_enabled": True},
                        )
                item = {
                    "property_id": str(prop.id),
                    "owner_alias": (
                        "owner_b" if branch == "secondary_owner" else "owner_a"
                    ),
                    "tenant_alias": "tenant_a",
                    "start_date": str(start),
                    "end_date": str(end),
                    "rent": money(int(prop.price * 100)),
                    "terms": agreement_terms(start, end, int(prop.price * 100)),
                    "appointment_date": str(appointment_date),
                    "times": ["10:00", "14:00", "16:00"],
                    "appointment_at": timezone.make_aware(
                        datetime.combine(appointment_date, time(14))
                    ).isoformat(),
                    "effective_on": str(
                        start if branch == "exit" else start + timedelta(days=20)
                    ),
                }
                if branch == "legacy":
                    item["draft"] = {
                        "template_id": "eg-residential-v1",
                        "template_version": "1",
                        "start_date": str(start),
                        "end_date": str(end),
                        "rent": item["rent"],
                    }
                else:
                    # Preserve changed availability/terms and expose them rather than resetting a used run.
                    expected_offer = str(resource_id(run_id, f"{branch}:offer"))
                    offer = next(
                        (
                            value
                            for value in prop.rental_inventory.get("offers", [])
                            if str(value.get("id")) == expected_offer
                        ),
                        None,
                    )
                    if not offer:
                        raise CommandError(
                            f"Run offer {branch} was removed; no replacement accommodation was selected."
                        )
                    item.update(
                        offer_id=offer["id"],
                        expected_offer_revision=offer["revision"],
                    )
                    try:
                        _, snapshot = resolve_offer_snapshot(
                            prop, offer["id"], offer["revision"]
                        )
                        item["selection"] = selection_payload(snapshot)
                    except (InvitationConflict, ValidationError) as exc:
                        item["selection"] = None
                        item["blocked_reason"] = str(exc.detail)
                    rent = int(Decimal(str(offer["terms"]["price"])) * 100)
                    item["rent"] = money(rent)
                    item["terms"] = agreement_terms(start, end, rent)
                    item["criteria"] = {
                        "city_id": str(city.id),
                        "district_ids": [],
                        "rental_scope": offer["rental_scope"],
                        "property_type": kind.slug,
                        "budget_min": money(100_000),
                        "budget_max": money(2_000_000),
                        "price_period": "monthly",
                        "start_on": str(start),
                        "end_on": None,
                        "people": 1 if branch == "bed" else 2,
                        "amenities": [],
                        "furnished": None,
                    }
                if branch in {"legacy", "structured"}:
                    visit, _ = PropertyVisit.objects.get_or_create(
                        id=resource_id(run_id, f"source-visit:{branch}"),
                        defaults={
                            "property": prop,
                            "tenant": actors["tenant_a"],
                            "status": "confirmed",
                            "visit_date": appointment_date,
                            "visit_time": time(10),
                            "note": "QA eligibility fixture",
                        },
                    )
                    if (
                        visit.property_id != prop.pk
                        or visit.tenant_id != actors["tenant_a"].pk
                    ):
                        raise CommandError(
                            f"Run source visit {branch} has different participants; preserved."
                        )
                    item["source_visit_id"] = str(visit.id)
                if branch == "exit":
                    item["settlement_lines"] = [
                        {
                            "type": "deposit_deduction",
                            "description": "QA replacement key agreed by both participants",
                            "amount": money(200_000),
                            "evidence_ids": [],
                        }
                    ]
                manifest[branch] = item
                get_or_create_owner_profile(owner)
            manifest["discovery"] = {
                "selection": manifest["discovery_property"]["selection"],
                "property_id": manifest["discovery_property"]["property_id"],
                "offer_id": manifest["discovery_property"]["offer_id"],
                "expected_offer_revision": manifest["discovery_property"][
                    "expected_offer_revision"
                ],
                "desired_start": manifest["discovery_property"]["start_date"],
                "commute": {
                    "destinations": [
                        {
                            "label": "QA workplace",
                            "location": {"latitude": 30.04, "longitude": 31.23},
                            "mode": "walking",
                            "limit_minutes": 60,
                        }
                    ],
                    "local_time": f"{start}T08:30",
                    "time_kind": "arrive_by",
                    "timezone": "Africa/Cairo",
                    "balance": False,
                    "hard_limits": True,
                    "filters": {
                        "city": str(city.id),
                        "price_max": "15000",
                        "price_period": "monthly",
                    },
                },
                "assistant": {
                    "session_id": str(resource_id(run_id, "assistant-session")),
                    "previous_turn_id": "",
                    "language": "en",
                    "text": f"An apartment in {city.name} under 15000 monthly near my workplace",
                    "retain_history": False,
                },
            }
            if credentials_path:
                write_private_json(
                    credentials_path, {"run_id": run_id, "actors": credentials}
                )
                created_credential_file = True
        return manifest
    except Exception:
        if created_credential_file:
            credentials_path.unlink()
        raise
