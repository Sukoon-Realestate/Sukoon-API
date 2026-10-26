"""Versioned preparation, individual authority, and truthful partial resolution."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError
from core_apps.properties.models import Property
from ...advanced_execution_models import AdvancedExecutionConsent
from ...models import RentalProviderInstruction
from ..rental_phase2 import RentalConflict
from ..rental_lifecycle.inventory import unresolved_payment
from ..rental_lifecycle.cases import open_system_case
from . import canonical
from .plans import require_accepted, record_step, POLICY, actions
from .provider import mock_instruction, reconcile_instructions
from .registry import adapter, CAPABILITIES


def own_leg(plan, actor, identifier):
    leg = get_object_or_404(plan.legs.select_for_update(of=("self",)), id=identifier)
    if str(actor.id) not in leg.actor_ids:
        raise PermissionDenied("This execution leg belongs to another participant.")
    return leg


def sync(plan):
    if plan.provider_mode == "test":
        from .progress import refresh

        refresh(plan, persist=True)
        return plan
    if plan.legs.filter(canonical_kind="company").exists():
        return adapter(plan.source_kind).sync(plan)
    states = []
    unknown = False
    for leg in plan.legs.select_related("lease"):
        if leg.lease_id:
            lease = leg.lease
            if lease.status in {"active", "termination_pending", "ended"}:
                leg.state = "confirmed"
            elif lease.status == "signed":
                leg.state = "signed"
            elif lease.status in {"cancelled", "expired"}:
                leg.state = "withdrawn" if lease.status == "cancelled" else "expired"
            elif lease.status == "pending_signatures":
                leg.state = (
                    "signing"
                    if lease.signing_sessions.filter(status="completed").exists()
                    else "held"
                )
            leg.save(update_fields=["state", "updated_at"])
        unknown |= RentalProviderInstruction.objects.filter(
            subject_id=leg.id, status="unknown"
        ).exists()
        states.append(leg.state)
    if unknown:
        plan.state = "unknown"
    elif plan.case_id and plan.case.status not in {"resolved", "closed"}:
        plan.state = "manual_resolution"
    elif states and all(state == "confirmed" for state in states):
        plan.state = "completed"
    elif any(state in {"withdrawn", "failed", "expired"} for state in states):
        plan.state = (
            "partial"
            if any(state == "confirmed" for state in states)
            else "manual_resolution"
        )
    elif plan.state not in {"awaiting_consents", "ready", "closed_partial"}:
        plan.state = (
            "executing"
            if any(state in {"signing", "signed", "confirmed"} for state in states)
            else "prepared"
        )
    completion = getattr(adapter(plan.source_kind), "completion_state", None)
    if completion:
        plan.state = completion(plan, plan.state)
    return plan


def prepare(plan, actor):
    require_accepted(plan)
    adapter(plan.source_kind).revalidate(plan, action="prepare")
    if any(leg.canonical_kind == "company" for leg in plan.legs.all()):
        adapter(plan.source_kind).prepare(plan, actor)
    else:
        legs = list(plan.legs.all())
        # Shared physical roots are locked in one stable order before obligations.
        list(
            Property.objects.select_for_update()
            .filter(id__in=[x.specification["property_id"] for x in legs])
            .order_by("pk")
        )
        for leg in sorted(legs, key=lambda x: x.specification["property_id"]):
            canonical.prepare_leg(plan, leg, actor)
    plan.state = "prepared"
    return sync(plan)


def advance(plan, actor, data):
    if plan.provider_mode != "mock":
        raise PermissionDenied("Continue through the original agreement or invoice.")
    leg = own_leg(plan, actor, data.get("leg_id"))
    adapter(plan.source_kind).revalidate(plan, action="advance")
    if leg.canonical_kind == "company":
        adapter(plan.source_kind).advance(plan, actor, data)
        return plan
    if not leg.lease_id:
        raise RentalConflict(
            "Prepare this execution before signing or payment.", code="invalid_state"
        )
    action = data.get("step")
    lease = leg.lease
    if action == "sign" and actor.pk not in {lease.owner_id, lease.tenant_id}:
        raise PermissionDenied("Only an agreement signer may authorize a signature.")
    if action == "pay" and actor.pk != lease.tenant_id:
        raise PermissionDenied("Only the canonical payer may authorize this payment.")
    if action not in {"sign", "pay"}:
        raise ValidationError("Choose signing or first-invoice payment.")
    if data.get(
        "document_hash"
    ) != lease.document_hash or lease.terms != canonical.terms_for(
        leg.specification, plan
    ):
        raise RentalConflict(
            "Review the current exact agreement before this step.",
            code="document_changed",
        )
    if action == "pay":
        from ..rental_phase3 import invoice_balance_minor

        invoice = (
            lease.invoices.select_for_update()
            .filter(billing_period__sequence=1)
            .first()
        )
        if not invoice or (
            data.get("invoice_id"),
            data.get("invoice_revision"),
            data.get("amount_minor"),
        ) != (str(invoice.id), invoice.revision, invoice_balance_minor(invoice)):
            raise RentalConflict(
                "Review the exact current first invoice and payable amount.",
                code="invoice_changed",
            )
    if action == "pay" and plan.mode == "conditional_package":
        if RentalProviderInstruction.objects.filter(
            subject_id__in=plan.legs.values_list("id", flat=True), status="unknown"
        ).exists() or any(
            x.lease_id is None or x.lease.status not in {"signed", "active"}
            for x in plan.legs.select_related("lease")
        ):
            raise RentalConflict(
                "Conditional execution requires every agreement signed before payment.",
                code="conditional_threshold",
            )
    instruction = mock_instruction(
        plan,
        leg,
        kind=action,
        actor=actor,
        request_key=data["request_key"],
        behavior=data.get("mock_outcome", "confirmed"),
        perform=lambda item: (canonical.sign if action == "sign" else canonical.pay)(
            plan, leg, actor, item
        ),
    )
    if instruction.status == "failed":
        record_step(plan, leg, "retry_available", "failed", actor=actor)
    return sync(plan)


def reconcile(plan, actor):
    if any(x.canonical_kind == "company" for x in plan.legs.all()):
        adapter(plan.source_kind).reconcile(plan, actor)
    for leg in plan.legs.all():
        if plan.provider_mode == "mock" and str(actor.id) in leg.actor_ids:
            reconcile_instructions(plan, leg, actor)
        if leg.lease_id:
            if leg.lease.renter_company_id:
                from ..company.tenancy_expiry import expire

                expire(leg.lease.company_tenancy)
                continue
            from ..rental_lifecycle.inventory import expire_property_holds

            prop = Property.objects.select_for_update().get(pk=leg.lease.property_id)
            expire_property_holds(prop)
    return sync(plan)


def withdraw(plan, actor, data):
    leg = own_leg(plan, actor, data.get("leg_id"))
    if leg.canonical_kind == "company":
        adapter(plan.source_kind).withdraw(plan, actor, data)
        return plan
    return withdraw_canonical(plan, leg, actor)


def withdraw_canonical(plan, leg, actor):
    if leg.lease_id:
        from ..signing_documents import unresolved as unresolved_signature
        from ..rental_lifecycle.locks import lock_financial_lease

        lease = lock_financial_lease(leg.lease)
        if (
            unresolved_payment(lease)
            or unresolved_signature(lease)
            or RentalProviderInstruction.objects.filter(
                subject_id=leg.id, status="unknown"
            ).exists()
        ):
            raise RentalConflict(
                "Reconcile uncertain outcomes before releasing accommodation.",
                code="reconciliation_required",
            )
        if (
            lease.status in {"signed", "active", "termination_pending", "ended"}
            or lease.signing_sessions.filter(status="completed").exists()
        ):
            plan.case = open_system_case(
                kind="group_incomplete",
                source_key=f"advanced-partial:{plan.id}",
                lease=lease,
                actor=actor,
                reason="A participant requested withdrawal after a binding or partially signed step.",
                next_action=(
                    "Support must review canonical lease change authority. "
                    "Confirmed leases and prices remain unchanged."
                ),
            )
            plan.state = "manual_resolution"
            record_step(
                plan,
                leg,
                "withdrawal_review",
                "manual_resolution",
                "rental_operational_case",
                plan.case.id,
                actor=actor,
            )
            return plan
        if lease.renter_company_id:
            from ..company.tenancy_contracts import cancel

            cancel(lease.company_tenancy, actor, {
                "reason": "Explicit withdrawal of an uncommitted execution package.",
            })
        else:
            lease.inventory_day_locks.filter(kind="hold").delete()
            lease.status = "cancelled"
            lease.revision += 1
            lease.save()
    leg.state = "withdrawn"
    leg.save()
    record_step(plan, leg, "release_uncommitted", "confirmed", actor=actor)
    return sync(plan)


def resolve(plan, actor, data):
    if (
        data.get("policy_version") != POLICY
        or data.get("resolution") != "preserve_confirmed"
    ):
        raise ValidationError(
            "Explicitly accept preserving confirmed obligations and unchanged prices."
        )
    legs = list(plan.legs.all())
    if (
        (plan.case_id and plan.case.status not in {"resolved", "closed"})
        or any(
            x.state
            not in {
                "confirmed",
                "withdrawn",
                "expired",
                "failed",
                "mock_confirmed",
                "mock_withdrawn",
            }
            for x in legs
        )
        or RentalProviderInstruction.objects.filter(
            subject_id__in=[x.id for x in legs], status="unknown"
        ).exists()
    ):
        raise RentalConflict(
            "Resolve every binding or uncertain canonical outcome before closing.",
            code="manual_resolution_required",
        )
    AdvancedExecutionConsent.objects.create(
        execution=plan,
        actor=actor,
        digest=plan.digest,
        decision="accept_partial",
        execution_revision=plan.revision,
    )
    accepted = {
        str(x)
        for x in plan.consents.filter(
            decision="accept_partial", digest=plan.digest
        ).values_list("actor__id", flat=True)
    }
    if set(plan.required_actor_ids).issubset(accepted):
        plan.state = "closed_partial"
    record_step(
        plan,
        None,
        "partial_resolution",
        "accepted",
        actor=actor,
        metadata={"policy_version": POLICY},
    )
    return plan


def command(plan, actor, action, data):
    from config.advanced_housing import require_execution_mode

    require_execution_mode(plan.provider_mode)
    if plan.provider_mode == "test":
        sync(plan)
    if action not in actions(actor, CAPABILITIES[plan.source_kind], str(plan.id), plan=plan):
        raise PermissionDenied("This execution action is not currently authorized.")
    if data.get("digest") != plan.digest:
        raise RentalConflict("The execution snapshot changed.", code="document_changed")
    from .plans import consent

    if action == "consents":
        consent(plan, actor, data)
    elif action == "prepare":
        prepare(plan, actor)
    elif action == "advance":
        advance(plan, actor, data)
    elif action == "reconcile":
        reconcile(plan, actor)
    elif action == "withdraw":
        withdraw(plan, actor, data)
    elif action == "resolve":
        resolve(plan, actor, data)
    else:
        raise ValidationError("Unknown execution action.")
    plan.revision += 1
    plan.save()
    return plan
