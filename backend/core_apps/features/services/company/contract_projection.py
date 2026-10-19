from rest_framework.exceptions import APIException
from django.conf import settings
from ...company_contract_models import CompanyMandate
from . import contract_access as access, contract_snapshot as snapshots, mandates


def unit_label(row):
    return " / ".join(
        dict.fromkeys(
            str(row[key])
            for key in ("complex_name", "building_name", "code", "title")
            if row.get(key)
        )
    )


def reviewed_package(item):
    source = item.snapshot
    return {
        "id": str(item.booking.id),
        "revision": item.booking.revision,
        "full_term_rent_minor": source["full_term_rent_minor"],
        "deposit_minor": source["deposit_minor"],
        "quote_expires_at": source["quote_expires_at"],
        "snapshot": {
            **source["inventory"],
            "company_name": source["company_name"],
            "purpose": item.booking.snapshot.get("purpose", ""),
            "starts_on": source["starts_on"],
            "ends_on_exclusive": source["ends_on_exclusive"],
            "reserve_places": item.booking.snapshot.get("reserve_places"),
        },
    }


def payload(item, user):
    roles = access.roles_for(item, user)
    manages = access.manages(item, user)
    employee_only = roles == ["employee"] and not manages
    blocking = []
    finished = item.state in {"withdrawn", "agreement_created"}
    if not finished:
        try:
            snapshots.revalidate(item)
        except APIException as error:
            codes = error.get_codes()
            blocking.append(codes if isinstance(codes, str) else "source_changed")
    if (
        not finished
        and item.booking.request.coordinator_id == item.booking.offer.owner_id
    ):
        blocking.append("independent_coordinator_required")
    if item.booking.status == "withdrawn":
        effective = "withdrawn"
    else:
        effective = "review_required" if blocking else item.state
    if effective == "reviews_complete":
        effective = "ready_for_provider" if item.booking.hold_id else "ready_for_hold"
    rows = list(
        item.consents.filter(snapshot_digest=item.snapshot_digest).select_related(
            "actor"
        )
    )
    shown = [r for r in rows if not employee_only or r.actor_id == user.pk]
    allowed = []
    enabled = getattr(settings, "COMPANY_HOUSING_ENABLED", False)
    if not finished:
        for row in rows:
            if row.actor_id == user.pk and row.role in roles:
                if row.decision == "pending":
                    if not blocking and enabled:
                        allowed.append({"role": row.role, "decision": "accepted"})
                    allowed.append({"role": row.role, "decision": "declined"})
                if row.decision == "accepted":
                    allowed.append({"role": row.role, "decision": "withdrawn"})
    source = item.snapshot
    from .tenancy_access import execution_mandate

    execution_ready = all(
        execution_mandate(
            m, exposure=source["full_term_rent_minor"] + source["deposit_minor"]
        )
        for m in [item.signer_mandate, item.payer_mandate]
    )
    placements = [
        p
        for p in source["placements"]
        if not employee_only or p["employee_id"] == str(user.id)
    ]
    unit_ids = {p["property_id"] for p in placements}
    names = {p["id"]: p["name"] for p in source["people"]}
    units = [
        {"id": p["id"], "title": unit_label(p)}
        for p in source["inventory"]["units"]
        if not employee_only or p["id"] in unit_ids
    ]
    return {
        "id": str(item.id),
        "booking_id": str(item.booking.id),
        "company_id": source["company_id"],
        "company_name": source["company_name"],
        "title": item.booking.request.title,
        "revision": item.revision,
        "state": item.state,
        "effective_state": effective,
        "snapshot_digest": item.snapshot_digest,
        "renter_kind": "company",
        "payer_kind": "company",
        "employees_are_debtors": False,
        "provider_available": False,
        "package": {} if employee_only else reviewed_package(item),
        "signer_name": source["signer_name"] if not employee_only else "",
        "payer_name": source["payer_name"] if not employee_only else "",
        "full_term_rent_minor": (
            source["full_term_rent_minor"] if not employee_only else None
        ),
        "deposit_minor": source["deposit_minor"] if not employee_only else None,
        "currency": "EGP",
        "exponent": 2,
        "starts_on": source["starts_on"],
        "ends_on_exclusive": source["ends_on_exclusive"],
        "quote_expires_at": source["quote_expires_at"],
        "hold_expires_at": (
            item.booking.hold.expires_at.isoformat() if item.booking.hold_id else None
        ),
        "blocking_reasons": blocking
        + (
            ["execution_authority_required"]
            if effective == "ready_for_provider" and not execution_ready
            else []
        ),
        "can_revise": manages and not finished and enabled,
        "can_withdraw": manages and not finished,
        "tenancy_id": str(item.tenancy.id) if hasattr(item, "tenancy") else "",
        "can_create_agreement": manages
        and effective == "ready_for_provider"
        and enabled
        and execution_ready,
        "can_reserve": manages and effective == "ready_for_hold" and enabled,
        "new_business_enabled": enabled,
        "responses": allowed,
        "units": units,
        "placements": [
            {**p, "employee_name": names[p["employee_id"]]} for p in placements
        ],
        "reviews": [
            {
                "role": r.role,
                "actor_id": str(r.actor.id),
                "actor_name": r.actor.get_full_name,
                "decision": r.decision,
                "reason": r.reason if manages or r.actor_id == user.pk else "",
            }
            for r in shown
        ],
        "pending_review_count": (
            sum(r.decision == "pending" for r in rows)
            if not employee_only
            else sum(r.decision == "pending" for r in shown)
        ),
    }


def context(booking, user):
    from .bookings import item_payload

    people = snapshots.people_for(booking)
    existing = getattr(booking, "contract_preparation", None)
    rows = CompanyMandate.objects.filter(
        company=booking.request.company, state="approved"
    ).select_related("membership__user")
    exposure = booking.full_term_rent_minor + booking.deposit_minor
    return {
        "package": item_payload(booking),
        "id": str(booking.id),
        "company_id": str(booking.request.company.id),
        "revision": existing.revision if existing else booking.revision,
        "preparation_id": str(existing.id) if existing else "",
        "signer_mandate_id": str(existing.signer_mandate.id) if existing else "",
        "payer_mandate_id": str(existing.payer_mandate.id) if existing else "",
        "placements": existing.snapshot["placements"] if existing else [],
        "people": [{"id": p["id"], "name": p["name"]} for p in people],
        "units": [
            {"id": p["id"], "title": unit_label(p), "capacity": p.get("capacity")}
            for p in booking.snapshot["units"]
        ],
        "mandates": [
            mandates.payload(row, user)
            for row in rows
            if mandates.current(row, exposure=exposure)
        ],
        "full_term_rent_minor": booking.full_term_rent_minor,
        "deposit_minor": booking.deposit_minor,
    }
