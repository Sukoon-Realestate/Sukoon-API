"""Task projections over existing records, with no duplicate financial ledger."""

from rest_framework.exceptions import PermissionDenied
from . import tenancy_access, tenancy_projection, contract_access, contract_projection
from .role_context import selected

SECTIONS = {
    "admin": set(),
    "coordinator": {"tasks", "history"},
    "approver": {"decisions", "history"},
    "signer": {"changes", "history", "tasks"},
    "payer": {"invoices", "settlements", "history", "tasks"},
    "employee": {"tasks"},
}


def rows(user, company, section):
    role = selected(user, company)
    if section not in SECTIONS.get(role, set()):
        raise PermissionDenied("This section is unavailable for the active role.")
    result = []

    def add(identity, title, state, target, kind="tenancy", **fields):
        result.append(
            {
                "id": str(identity),
                "title": title,
                "state": state,
                "target_id": str(target),
                "target_kind": kind,
                "company_id": str(company.id),
                "company_role": role,
                **fields,
            }
        )

    if section == "decisions":
        from ...company_models import CompanyApproval

        for approval in (
            CompanyApproval.objects.filter(
                item__request__company=company,
                approver=user,
                item__assigned_approver__user=user,
            )
            .select_related("item__request")
            .order_by("-created_at")
        ):
            add(
                approval.id,
                approval.item.request.title,
                approval.decision,
                approval.item.request.id,
                "request",
                reason=approval.reason,
                occurred_at=approval.created_at.isoformat(),
            )
        return result
    if section == "tasks":
        for preparation in contract_access.visible(user).filter(
            booking__request__company=company
        ):
            value = contract_projection.payload(preparation, user)
            if value["responses"]:
                add(
                    preparation.id,
                    value["title"],
                    value["effective_state"],
                    preparation.id,
                    "preparation",
                )
    for item in (
        tenancy_access.visible(user)
        .filter(lease__renter_company=company)
        .select_related("lease")
    ):
        value = tenancy_projection.payload(item, user)
        if section == "history":
            if role == "payer":
                from ...models import PaymentAttempt

                for payment in (
                    PaymentAttempt.objects.filter(invoice__lease=item.lease)
                    .select_related("invoice")
                    .order_by("-created_at")
                ):
                    add(
                        payment.id,
                        payment.invoice.reference,
                        payment.payment_status,
                        payment.invoice.id,
                        "invoice",
                        amount_minor=payment.amount_minor,
                        occurred_at=(
                            payment.confirmed_at or payment.created_at
                        ).isoformat(),
                    )
            for index, entry in enumerate(value["history"]):
                add(
                    f"{item.id}:{index}",
                    value["title"],
                    entry["action"],
                    item.id,
                    occurred_at=entry["occurred_at"],
                )
        if section == "invoices":
            for invoice in value.get("invoices", []):
                add(
                    invoice["id"],
                    invoice["reference"],
                    invoice.get("status", invoice.get("state", "")),
                    invoice["id"],
                    "invoice",
                    amount_minor=invoice.get("balance_minor"),
                    lease_id=str(item.lease.id),
                )
        if section in {"changes", "settlements", "tasks"}:
            for change in value["changes"]:
                if section == "tasks" and not change["roles_to_decide"]:
                    continue
                if section == "settlements" and change["kind"] not in {
                    "settlement",
                    "settlement_adjustment",
                }:
                    continue
                add(
                    change["id"],
                    value["title"],
                    change["state"],
                    item.id,
                    action=change["kind"],
                )
            if section == "tasks":
                for assignment in value.get("assignments", []):
                    if assignment["actions"] or any(
                        c["roles_to_decide"] for c in assignment["confirmations"]
                    ):
                        add(
                            assignment["id"],
                            assignment["property_name"],
                            assignment["state"],
                            item.id,
                        )
                for task in value.get("maintenance", []):
                    if task.get("actions"):
                        add(task["id"], task["title"], task["state"], item.id)
            if section == "settlements":
                for refund in value.get("refunds", []):
                    add(
                        refund["id"],
                        value["title"],
                        refund["state"],
                        item.id,
                        amount_minor=refund["amount_minor"],
                    )
    return result
