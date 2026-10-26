from ...models import RentalProviderInstruction
from rest_framework.exceptions import NotFound, PermissionDenied
from django.http import Http404
from .plans import actions, decisions
from .registry import CAPABILITIES, adapter


def payload(plan, actor):
    own = str(actor.id)
    latest = decisions(plan)
    from .progress import refresh, outcome

    all_legs = (
        refresh(plan) if plan.provider_mode == "test"
        else list(plan.legs.select_related("lease"))
    )
    coordinator = own in plan.context.get("coordinator_ids", [])
    if coordinator:
        try:
            adapter(plan.source_kind).authorize(actor, plan.source_id)
        except (NotFound, PermissionDenied, Http404):
            coordinator = False
    visible = [x for x in all_legs if own in x.actor_ids or coordinator]
    result = []
    for leg in visible:
        spec = leg.specification
        role = (
            "owner"
            if own == spec.get("owner_id")
            else "tenant" if own == spec.get("tenant_id") else "occupant"
        )
        lease = leg.lease
        invoice = (
            lease.invoices.filter(billing_period__sequence=1).first() if lease else None
        )
        from ..rental_phase3 import invoice_balance_minor

        steps = []
        if (
            lease
            and lease.status == "pending_signatures"
            and role in {"owner", "tenant"}
            and not lease.signing_sessions.filter(
                signer=actor, status="completed", document_hash=lease.document_hash
            ).exists()
        ):
            steps.append("sign")
        if lease and lease.status == "signed" and role == "tenant":
            steps.append("pay")
        if leg.canonical_kind == "company":
            steps = adapter(plan.source_kind).leg_actions(plan, leg, actor)
        unknown = RentalProviderInstruction.objects.filter(
            subject_id=leg.id, status="unknown"
        ).exists()
        if plan.provider_mode == "test":
            unknown |= outcome(leg, lease)[1]
            steps = []
        row = {
            "id": str(leg.id),
            "key": leg.key,
            "state": leg.state,
            "role": role,
            "canonical_kind": leg.canonical_kind,
            "canonical_id": str(leg.canonical_id or ""),
            "lease_id": str(lease.id) if lease else "",
            "lease_status": lease.status if lease else "",
            "occupancy_status": lease.occupancy_status if lease else "not_started",
            "financial_closure_status": (
                lease.financial_closure_status if lease else "open"
            ),
            "outgoing_lease_id": (
                spec.get("outgoing_lease_id", "") if role == "tenant" else ""
            ),
            "selection": spec.get("selection", {}),
            "starts_on": spec.get("starts_on", ""),
            "ends_on_exclusive": spec.get("ends_on_exclusive", ""),
            "rent_minor": spec.get("rent_minor", 0),
            "deposit_minor": spec.get("deposit_minor", 0),
            "terms": lease.terms if lease else spec.get("terms", {}),
            "document_hash": lease.document_hash if lease else "",
            "invoice_id": str(invoice.id) if invoice else "",
            "invoice_revision": invoice.revision if invoice else 0,
            "first_invoice_minor": invoice_balance_minor(invoice) if invoice else None,
            "unknown_outcome": unknown,
            "available_steps": [] if unknown else steps,
            "hold_expires_at": (
                lease.hold_expires_at.isoformat()
                if lease and lease.hold_expires_at
                else None
            ),
        }
        leg_payload = getattr(adapter(plan.source_kind), "leg_payload", None)
        if leg_payload:
            row.update(leg_payload(plan, leg, actor))
        if plan.provider_mode == "test" and leg.canonical_kind != "company":
            from ..signing_documents import projection as signing_projection
            from ..signing_documents import unresolved as unresolved_signature
            from ..company.tenancy_access import commercial_read

            permitted = lease and commercial_read(lease, actor)
            row.update({
                "available_steps": [],
                "continuation_kind": "lease" if permitted else "",
                "continuation_id": str(lease.id) if permitted else "",
                "signing_document": signing_projection(lease, actor) if permitted else None,
                "may_withdraw": own in leg.actor_ids and leg.state not in {"confirmed", "withdrawn", "expired"},
                "can_withdraw": bool(
                    own in leg.actor_ids and not unknown
                    and not (lease and unresolved_signature(lease))
                    and leg.state not in {"confirmed", "withdrawn", "expired"}
                ),
                "waiting_reason": (
                    "reconciliation_required" if unknown
                    else "canonical_agreement" if lease else "prepare_required"
                ),
            })
        # A source adapter can narrow actions; unknown outcomes always stop writes.
        if unknown:
            row["available_steps"] = []
        result.append(row)
    visible_ids = {x.pk for x in visible}
    journal = [
        {
            "id": str(x.id),
            "leg_id": str(x.leg.id) if x.leg_id else "",
            "kind": x.kind,
            "state": x.state,
            "canonical_kind": x.canonical_kind,
            "canonical_id": str(x.canonical_id or ""),
            "created_at": x.created_at.isoformat(),
        }
        for x in plan.steps.select_related("leg").order_by("pkid")
        if x.leg_id in visible_ids
        or (x.leg_id is None and (coordinator or x.actor_id == actor.pk))
    ]
    return {
        "id": str(plan.id),
        "revision": plan.revision,
        "source_kind": plan.source_kind,
        "source_id": str(plan.source_id),
        "digest": plan.digest,
        "mode": plan.mode,
        "policy_version": plan.policy_version,
        "provider_mode": plan.provider_mode,
        "simulated": plan.provider_mode == "mock",
        "state": plan.state,
        "capability": CAPABILITIES[plan.source_kind],
        "required_count": len(plan.required_actor_ids),
        "accepted_count": sum(
            latest.get(x) == "accept" for x in plan.required_actor_ids
        ),
        "own_decision": latest.get(own, "pending"),
        "confirmed_count": sum(
            x.state in {"confirmed", "mock_confirmed"} for x in all_legs
        ),
        "leg_count": len(all_legs),
        "legs": result,
        "steps": journal,
        "case_id": str(plan.case.id) if plan.case_id else "",
        "blocking_reasons": (
            ["signing_provider_unavailable"] if plan.state == "ready"
            and plan.provider_mode == "test" and plan.source_kind != "company_scenario"
            and "prepare" not in actions(actor, CAPABILITIES[plan.source_kind], str(plan.id), plan=plan)
            else []
        ),
        "allowed_actions": actions(actor, CAPABILITIES[plan.source_kind], str(plan.id), plan=plan)[
            1:
        ],
    }
