import uuid
from datetime import timedelta
import pytest
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from core_apps.features.tests.test_rental_phase3 import phase3_lease
from core_apps.features.models import (
    RentalEvidence,
    PolicyDecision,
    HabitabilityRestriction,
    RentInvoice,
    RentalInventoryDayLock,
)
from core_apps.features.services.rental_lifecycle.cases import open_system_case
from core_apps.features.services.rental_lifecycle.habitability import (
    report,
    assess,
    assert_habitable,
)
from core_apps.features.services.rental_phase2 import RentalConflict
from core_apps.users.models import User

pytestmark = pytest.mark.django_db


def setup_case(phase3_lease):
    owner, tenant, lease = phase3_lease
    lease.occupancy_status = "occupied"
    lease.save()
    case = open_system_case(
        kind="habitability",
        source_key=str(uuid.uuid4()),
        lease=lease,
        actor=tenant,
        reason="Synthetic leak",
        next_action="Assessment required",
    )
    report(case, {"reported_severity": "urgent"})
    media = RentalEvidence.objects.create(
        lease=lease,
        uploader=tenant,
        request_key=uuid.uuid4(),
        original_name="synthetic.png",
        content_type="image/png",
        size_bytes=10,
        sha256="a" * 64,
        storage_key=str(uuid.uuid4()),
        malware_status="safe",
    )
    case.evidence.add(media)
    return case, media


def authorize(case):
    reviewer = User.objects.create_superuser(
        email="assessor@example.test", password="synthetic"
    )
    case.assigned_to = reviewer
    case.save()
    PolicyDecision.objects.create(
        evidence_requirements={"fixture": "synthetic only"},
        actions_and_consequences={"fixture": "no live consequence"},
        historical_treatment="No live applicability",
        audit_reason="Isolated test fixture",
        disclosure="Synthetic test only",
        code="D29",
        version="SYNTHETIC-ONLY",
        status="approved",
        owner="test",
        approver=reviewer,
        source="test fixture",
        evidence_reference="isolated assessment test",
        effective_at=timezone.now() - timedelta(seconds=1),
        scope=["habitability.restrict", "habitability.reopen"],
        rules={"assessor_roles": ["support"]},
    )
    return reviewer


def command(case, media, action="restrict"):
    return {
        "action": action,
        "expected_revision": case.revision,
        "physical_keys": case.baseline["habitability"]["physical_keys"],
        "evidence_ids": [str(media.id)],
        "assessed_severity": "major",
        "review_at": timezone.now() + timedelta(hours=1),
        "reason": "Synthetic inspection",
    }


def test_report_does_not_restrict_or_modify_money_or_occupancy(phase3_lease):
    case, _ = setup_case(phase3_lease)
    assert_habitable(case.property, case.lease.offer_snapshot)
    assert (
        not HabitabilityRestriction.objects.exists()
        and not RentInvoice.objects.exists()
    )
    case.lease.refresh_from_db()
    assert case.lease.occupancy_status == "occupied"
    assert case.baseline["habitability"]["financial_status"] == "awaiting_policy"


def test_unapproved_assessment_is_blocked(phase3_lease):
    case, media = setup_case(phase3_lease)
    with pytest.raises(RentalConflict) as error:
        assess(case.lease.owner, case, command(case, media))
    assert error.value.get_codes() == "awaiting_policy"
    assert not HabitabilityRestriction.objects.exists()


@pytest.mark.django_db(transaction=True)
def test_reservation_waits_for_concurrent_assessment_and_rechecks_restriction(
    phase3_lease,
):
    from threading import Event
    from time import monotonic, sleep
    from django.db import connection, transaction
    from core_apps.features.tests.test_cycle_concurrency import parallel_calls
    from core_apps.features.services.rental_lifecycle.inventory import reserve_lease

    if connection.vendor != "postgresql":
        pytest.skip("This test observes real PostgreSQL row-lock contention.")
    case, media = setup_case(phase3_lease)
    reviewer = authorize(case)
    staged, reservation_started = Event(), Event()
    reservation_backend = {}
    before = list(RentalInventoryDayLock.objects.values_list("pk", "kind", "stay_on"))

    def contender(index):
        if index == 0:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    assessor_pid = cursor.fetchone()[0]
                assess(reviewer, case, command(case, media))
                staged.set()
                assert reservation_started.wait(3)
                # Prove the reservation actually waits on this uncommitted
                # assessment, rather than only testing two sequential calls.
                blocked = False
                deadline = monotonic() + 3
                while monotonic() < deadline:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "SELECT %s = ANY(pg_blocking_pids(%s))",
                            [assessor_pid, reservation_backend["pid"]],
                        )
                        blocked = cursor.fetchone()[0]
                    if blocked:
                        break
                    sleep(0.01)
                assert blocked
            return "restricted"
        assert staged.wait(3)
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_backend_pid()")
            reservation_backend["pid"] = cursor.fetchone()[0]
        reservation_started.set()
        try:
            with transaction.atomic():
                reserve_lease(
                    case.lease,
                    case.lease.start_date,
                    case.lease.end_date,
                    timezone.now() + timedelta(minutes=10),
                )
        except RentalConflict as error:
            return error.get_codes()
        return "unexpected_reservation"

    assert parallel_calls(contender) == ["restricted", "habitability_restricted"]
    assert (
        list(RentalInventoryDayLock.objects.values_list("pk", "kind", "stay_on"))
        == before
    )
    case.lease.refresh_from_db()
    assert case.lease.occupancy_status == "occupied"


def test_restriction_requires_current_independent_assessor_and_never_auto_expires(
    phase3_lease,
):
    case, media = setup_case(phase3_lease)
    reviewer = authorize(case)
    with pytest.raises(PermissionDenied):
        assess(case.lease.owner, case, command(case, media))
    case = assess(reviewer, case, command(case, media))
    HabitabilityRestriction.objects.update(review_at=timezone.now() - timedelta(days=1))
    with pytest.raises(RentalConflict):
        assert_habitable(case.property, case.lease.offer_snapshot)
    case.lease.refresh_from_db()
    assert case.lease.occupancy_status == "occupied"
    case = assess(reviewer, case, command(case, media, "reopen"))
    assert_habitable(case.property, case.lease.offer_snapshot)
    assert case.baseline["habitability"]["financial_status"] == "awaiting_policy"
    assert case.baseline["habitability"]["status"] == "reopened"


def test_quarantined_inspection_cannot_clear_restriction(phase3_lease):
    case, media = setup_case(phase3_lease)
    reviewer = authorize(case)
    case = assess(reviewer, case, command(case, media))
    media.malware_status = "pending"
    media.save()
    from rest_framework.exceptions import ValidationError

    with pytest.raises(ValidationError):
        assess(reviewer, case, command(case, media, "reopen"))
    assert HabitabilityRestriction.objects.filter(cleared_at__isnull=True).exists()


def test_scope_restriction_prevents_topology_evasion_and_public_availability(
    phase3_lease,
):
    from core_apps.features.services.rental_lifecycle.inventory import (
        guard_topology_update,
    )
    from core_apps.properties.serializers.property_parts.property_detail_serializer_operations.property_detail_media import (
        PropertyDetailMediaMixin,
    )
    from types import SimpleNamespace

    prop = phase3_lease[2].property
    prop.rental_inventory = {
        "mode": "whole",
        "rooms": [],
        "offers": [
            {
                "id": str(uuid.uuid4()),
                "rental_scope": "entire_property",
                "availability": "available",
            }
        ],
    }
    prop.save()
    case, media = setup_case(phase3_lease)
    reviewer = authorize(case)
    case = assess(reviewer, case, command(case, media))
    with pytest.raises(RentalConflict):
        guard_topology_update(
            case.property, {"mode": "rooms", "rooms": [{"id": "new-room", "beds": []}]}
        )
    reader = PropertyDetailMediaMixin()
    reader.context = {"request": SimpleNamespace(user=case.lease.tenant)}
    assert reader.get_rental_inventory(case.property)["offers"] == []


def test_bed_restriction_does_not_close_other_beds_or_release_occupied_days(
    phase3_lease,
):
    from core_apps.features.services.rental_lifecycle.inventory import ensure_units

    prop = phase3_lease[2].property
    room, first, second = [str(uuid.uuid4()) for _ in range(3)]
    prop.rental_inventory = {
        "mode": "partial",
        "rooms": [
            {
                "id": room,
                "name": "Room A",
                "beds": [
                    {"id": first, "name": "Bed 1"},
                    {"id": second, "name": "Bed 2"},
                ],
            }
        ],
        "offers": [],
    }
    prop.save()
    case, media = setup_case(phase3_lease)
    reviewer = authorize(case)
    for unit in ensure_units(prop, case.lease.offer_snapshot):
        RentalInventoryDayLock.objects.create(
            property=prop,
            unit=unit,
            lease=case.lease,
            offer_id="synthetic",
            stay_on=timezone.localdate(),
            kind="occupied",
        )
    data = {**command(case, media), "physical_keys": ["bed:" + first]}
    case = assess(reviewer, case, data)
    with pytest.raises(RentalConflict):
        assert_habitable(
            prop, {"rental_scope": "bed", "room_ids": [room], "bed_id": first}
        )
    assert_habitable(
        prop, {"rental_scope": "bed", "room_ids": [room], "bed_id": second}
    )
    assert (
        RentalInventoryDayLock.objects.filter(lease=case.lease, kind="occupied").count()
        == 2
    )
    case = assess(
        reviewer,
        case,
        {**command(case, media, "reopen"), "physical_keys": ["bed:" + first]},
    )
    assert_habitable(prop, {"rental_scope": "bed", "room_ids": [room], "bed_id": first})
    assert (
        RentalInventoryDayLock.objects.filter(lease=case.lease, kind="occupied").count()
        == 2
    )
