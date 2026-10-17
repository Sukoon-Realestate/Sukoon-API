"""Audited, source-specific recovery. A disclosed window never reopens."""

from contextvars import ContextVar
from datetime import timedelta
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from ...models import Lease, ReviewCase, CompanyMembership
from core_apps.properties.models import PropertyVisit
from .policy import ReviewError, text_value, revision, require_enabled
from .submission import command, audit

recovery_context = ContextVar("review_recovery", default=None)


def authorize(user, source):
    if not user.has_perm("features.review_eligibility"):
        raise PermissionDenied()
    people = {
        getattr(source, k, None)
        for k in ("owner_id", "tenant_id", "party_a_id", "party_b_id")
    }
    people.add(source.property.owner_id)
    lease = source if isinstance(source, Lease) else getattr(source, "lease", None)
    if lease:
        from ...models import CompanyLeaseBinding

        people.update(
            lease.responsibility_transitions.values_list("next_owner_id", flat=True)
        )
        binding = CompanyLeaseBinding.objects.filter(
            lease__tenancy_root_id=lease.tenancy_root_id
        ).first()
        companies = (
            [binding.renter_company_id, binding.landlord_company_id] if binding else []
        )
        if CompanyMembership.objects.filter(
            company_id__in=companies, user=user, is_active=True
        ).exists():
            raise ReviewError("conflict_of_interest")
    if user.pk in people:
        raise ReviewError("conflict_of_interest")


def evidence(body):
    reason = text_value(body.get("reason", ""), 1000)
    incident = text_value(body.get("incident_reference", ""), 200)
    try:
        start, end = (
            parse_datetime(body.get(k, ""))
            for k in ("outage_started_at", "outage_ended_at")
        )
        valid = (
            start
            and end
            and timezone.is_aware(start)
            and timezone.is_aware(end)
            and start <= end <= timezone.now()
        )
    except (ValueError, TypeError):
        valid = False
    if not reason or not incident or not valid:
        raise ReviewError("invalid_recovery_evidence", 400)
    return {
        "reason": reason,
        "incident_reference": incident,
        "outage_started_at": start.isoformat(),
        "outage_ended_at": end.isoformat(),
    }


def recover(user, body):
    from .generation import generate_tenancy, generate_viewing, generate_housemates
    from .company_generation import generate_employee
    from ...models import EmployeeAssignment

    kind = body.get("source_kind")
    model = (
        Lease
        if kind in {"tenancy", "co_living"}
        else (
            PropertyVisit
            if kind == "viewing"
            else EmployeeAssignment if kind == "employee_occupancy" else None
        )
    )
    if model is None:
        raise ReviewError("invalid_review_target", 400)
    source = get_object_or_404(model, id=body.get("source_id"))
    peer = (
        get_object_or_404(Lease, id=body.get("peer_lease_id"))
        if kind == "co_living"
        else None
    )
    if peer:
        authorize(user, peer)
    if kind == "employee_occupancy":
        from .employee_occupancy import binding

        if user.pk == source.employee_id:
            raise ReviewError("conflict_of_interest")
        authorize(user, binding(source).lease)
    else:
        authorize(user, source)
    proof = evidence(body)

    def action():
        require_enabled()
        if peer:
            list(
                Lease.objects.select_for_update()
                .filter(pk__in=[source.pk, peer.pk])
                .order_by("id")
            )
            locked = Lease.objects.get(pk=source.pk)
            authorize(user, peer)
        elif kind == "employee_occupancy":
            from .eligibility import lock_tenancy

            lock_tenancy(binding(source).lease)
            locked = model.objects.select_for_update().get(pk=source.pk)
        elif kind == "tenancy":
            from .eligibility import lock_tenancy

            locked = lock_tenancy(source)
        else:
            locked = model.objects.select_for_update().get(pk=source.pk)
        authorize(
            user, binding(locked).lease if kind == "employee_occupancy" else locked
        )
        token = recovery_context.set(proof)
        try:
            case = (
                generate_housemates(locked, peer)
                if kind == "co_living"
                else (
                    generate_tenancy(locked)
                    if kind == "tenancy"
                    else (
                        generate_employee(locked)
                        if kind == "employee_occupancy"
                        else generate_viewing(locked)
                    )
                )
            )
        finally:
            recovery_context.reset(token)
        if case.source_snapshot.get("generation_reason") != "audited_outage_recovery":
            raise ReviewError("review_already_generated")
        audit(
            case,
            user,
            "outage_recovered",
            f"{proof['incident_reference']}: {proof['reason']}",
        )
        return {
            "id": str(case.id),
            "opens_at": case.opens_at.isoformat(),
            "closes_at": case.closes_at.isoformat(),
            "revision": case.revision,
        }

    return command(user, f"review.recover.{source.id}", body, action, source.id)


def extend(user, identity, body):
    case = get_object_or_404(ReviewCase, id=identity)
    authorize(user, case)
    proof = evidence(body)

    def action():
        item = ReviewCase.objects.select_for_update().get(pk=case.pk)
        authorize(user, item)
        revision(item, body.get("expected_revision"))
        from .eligibility import valid_source

        if not valid_source(item):
            raise ReviewError("experience_not_confirmed")
        if (
            item.gate_released_at
            or item.closes_at <= timezone.now()
            or item.release_mode == "after_moderation"
        ):
            raise ReviewError("review_already_disclosed")
        if not item.opportunities.filter(submitted_once_at__isnull=True).exists():
            raise ReviewError("review_already_disclosed")
        start, end = (
            parse_datetime(proof[k]) for k in ("outage_started_at", "outage_ended_at")
        )
        if end < item.opens_at or start > item.closes_at:
            raise ReviewError("invalid_recovery_evidence", 400)
        days = body.get("extension_days")
        if (
            type(days) is not int
            or not 1 <= days <= 30
            or item.source_snapshot.get("window_extension")
        ):
            raise ReviewError("invalid_recovery_evidence", 400)
        item.source_snapshot = {
            **item.source_snapshot,
            "window_extension": {
                **proof,
                "previous_closes_at": item.closes_at.isoformat(),
                "days": days,
            },
        }
        item.closes_at += timedelta(days=days)
        item.revision += 1
        item.save()
        audit(
            item,
            user,
            "pair_window_extended",
            f"{proof['incident_reference']}: {proof['reason']}",
        )
        return {
            "id": str(item.id),
            "closes_at": item.closes_at.isoformat(),
            "revision": item.revision,
        }

    return command(user, f"review.extend.{identity}", body, action, case.id)
