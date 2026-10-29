"""Explicit role projections over the single canonical company records."""

from .role_context import selected


def keep(value, fields):
    return {key: value[key] for key in fields if key in value}


def company(value, item, user):
    role = selected(user, item)
    if role is None:
        return value
    common = {"id", "name", "revision", "review_status", "membership"}
    fields = {
        "admin": {
            "registration_number",
            "contact_email",
            "default_approver_id",
            "backup_approver_id",
            "default_approver_name",
            "backup_approver_name",
            "budget_limit_minor",
            "deposit_limit_minor",
            "readiness",
        },
        "approver": {
            "budget_limit_minor",
            "deposit_limit_minor",
            "reserved_rent_minor",
            "committed_rent_minor",
            "deposit_exposure_minor",
        },
    }.get(role, set())
    result = keep(value, common | fields)
    result["membership"] = {
        **keep(
            value["membership"],
            {
                "id",
                "user_id",
                "name",
                "revision",
                "is_active",
                "account_closure_blocked",
            },
        ),
        "roles": [role],
    }
    result["active_role"] = role
    result["role_projection_version"] = 1
    result["permissions"] = {
        "view_costs": role in {"coordinator", "approver", "signer", "payer"},
        "manage_people": role == "admin",
        "manage_budget": role == "admin",
        "coordinate": role == "coordinator" and value["permissions"]["coordinate"],
        "approve": role == "approver",
        "execute_payment": role == "payer",
        "manage_billing": role == "payer",
        "sign": role == "signer",
    }
    return result


TENANCY_COMMON = {
    "id",
    "company_id",
    "company_name",
    "revision",
    "title",
    "state",
    "occupancy_status",
    "starts_on",
    "ends_on_exclusive",
    "roles",
    "actions",
}
CHANGE_FIELDS = {
    "id",
    "revision",
    "kind",
    "state",
    "digest",
    "roles_to_decide",
    "can_withdraw",
    "can_resume",
    "content",
}
CHANGE_KINDS = {
    "coordinator": {"move_in", "move_out", "handover", "replacement"},
    "employee": {"replacement", "move_in", "move_out"},
    "signer": {
        "renewal",
        "amendment",
        "termination",
        "initial_release",
        "agreement_release",
        "continuation_release",
    },
    "payer": {
        "settlement",
        "settlement_adjustment",
        "termination",
        "renewal",
        "amendment",
    },
}


def payer_settlement_content(content):
    """Decision basis from the validated settlement, not its internal snapshot."""

    def line(value):
        result = keep(
            value, {"id", "type", "description", "invoice_id", "evidence_ids"}
        )
        result["amount"] = keep(
            value.get("amount", {}), {"amount_minor", "currency", "exponent"}
        )
        if "evidence" in value:
            # Already resolved for this lease by review_content. Storage and
            # uploader metadata are not part of the payer's decision basis.
            result["evidence"] = [
                keep(
                    row,
                    {
                        "id",
                        "lease_id",
                        "name",
                        "mime_type",
                        "size_bytes",
                        "status",
                        "sha256",
                        "revision",
                    },
                )
                for row in value["evidence"]
            ]
        return result

    source = content.get("plan", {})
    plan = keep(
        source,
        {
            "rent_balance_minor",
            "deposit_to_return_minor",
            "refund_due_minor",
            "total_due_minor",
            "released_deposit_due_minor",
        },
    )
    plan["charges"] = [line(row) for row in source.get("charges", [])]
    plan["credits"] = [
        keep(row, {"invoice_id", "amount_minor", "type", "line_id"})
        for row in source.get("credits", [])
    ]
    plan["deposit_applications"] = [
        keep(row, {"invoice_id", "amount_minor"})
        for row in source.get("deposit_applications", [])
    ]
    plan["refunds"] = [
        {
            **keep(row, {"payment_attempt_id", "amount_minor"}),
            "allocations": keep(row.get("allocations", {}), {"rent", "deposit"}),
        }
        for row in source.get("refunds", [])
    ]
    return {
        "kind_of_document": "summary",
        "lines": [line(row) for row in content.get("lines", [])],
        "plan": plan,
    }


def tenancy(value, item, user):
    from .role_context import http_context

    request = http_context(user)
    if (
        request is None
        or set(value["roles"])
        & {
            "owner",
            "new_owner",
            "financial_reviewer",
        }
        or (
            "prior_signer" in value["roles"]
            and not request.headers.get("X-Sukoon-Company-Role")
        )
    ):
        return value
    role = selected(user, item.lease.renter_company)
    fields = {
        "coordinator": {
            "lease_id",
            "package",
            "current_rent_minor",
            "assignments",
            "units",
            "people",
            "maintenance",
            "cases",
        },
        "employee": {"assignments", "units", "maintenance", "cases"},
        "signer": {
            "lease_id",
            "terms_digest",
            "document_hash",
            "signing_document",
            "terms",
            "business_policies",
            "reviewed_roles",
            "signing_sessions",
            "provider_available",
            "provider_mode",
            "blocking_reasons",
            "suggested_renewal_end",
            "current_rent_minor",
            "termination_dates",
            "continuation_choices",
            "cases",
        },
        "payer": {
            "lease_id",
            "invoices",
            "refunds",
            "financial_closure_status",
            "closure_blocking_reasons",
            "cases",
        },
        "approver": set(),
    }.get(role, set())
    result = keep(value, TENANCY_COMMON | fields)
    if role == "signer":
        result.update(keep(value, {"commercial_approvers", "amendment_dates"}))
    # Out-of-scope ownership and the old administrator tenancy workflow cannot
    # become alternate role entry points through a retained action button.
    if role not in {None, "owner"}:
        result["actions"] = [
            a
            for a in result.get("actions", [])
            if a not in {"ownership_change", "replace_authority"}
        ]
    result["active_role"] = role
    result["role_projection_version"] = 1
    if role == "payer":
        result["contract_summary"] = {
            "kind": "summary",
            "lease_id": str(item.lease.id),
            "company_name": item.lease.renter_company.name,
            "starts_on": str(item.lease.start_date),
            "ends_on_exclusive": str(item.lease.end_date),
            "rent_amount_minor": item.lease.rent_amount_minor,
            "deposit_minor": item.source_snapshot["deposit_minor"],
            "currency": "EGP",
            "exponent": 2,
        }
    if "cases" in result:
        from ...models import RentalOperationalCase
        from .role_cases import can_read

        allowed_cases = {
            str(case.id)
            for case in RentalOperationalCase.objects.filter(lease=item.lease)
            if can_read(case, user)
        }
        result["cases"] = [row for row in result["cases"] if row["id"] in allowed_cases]
    changes = []
    for change in value["changes"]:
        if role == "approver":
            include = bool(change["roles_to_decide"])
        else:
            include = change["kind"] in CHANGE_KINDS.get(role, set())
            if role in {"employee", "signer"}:
                include = include or bool(change["roles_to_decide"])
            if change["kind"] == "authority":
                include = bool(change["roles_to_decide"])
        if not include:
            continue
        row = keep(
            change,
            CHANGE_FIELDS
            | (
                {
                    "rental_change_id",
                    "signing_document",
                    "signing_roles",
                    "signing_sessions",
                    "continuation_actions",
                }
                if role == "signer"
                else set()
            ),
        )
        if change["kind"] == "authority":
            row["content"] = keep(row.get("content", {}), {role + "_name"})
        elif role in {"coordinator", "employee"}:
            row["content"] = keep(
                row.get("content", {}),
                {
                    "kind",
                    "property_id",
                    "property_name",
                    "employee_name",
                    "effective_on",
                    "starts_on",
                    "ends_on_exclusive",
                    "possession_on",
                    "condition",
                    "notes",
                    "keys",
                    "meters",
                    "inventory",
                    "evidence_ids",
                },
            )
            if role == "employee":
                row["content"].pop("employee_name", None)
        elif role == "payer" and change["kind"] == "settlement":
            row["reason"] = change.get("reason", "")
            row["content"] = payer_settlement_content(row.get("content", {}))
        elif role in {"payer", "approver"}:
            content = row.get("content", {})
            row["content"] = keep(
                content,
                {
                    "kind",
                    "effective_on",
                    "starts_on",
                    "ends_on_exclusive",
                    "rent_amount_minor",
                    "deposit_minor",
                    "rent_minor",
                    "currency",
                    "exponent",
                    "amount_minor",
                    "deductions",
                    "refund_minor",
                    "balance_minor",
                    "reason",
                    "months",
                    "rent_delta_minor",
                },
            )
            if isinstance(content.get("terms"), dict):
                row["content"]["rent_minor"] = (
                    content["terms"].get("rent", {}).get("amount_minor")
                )
            if role == "payer" and "lines" in content:
                row["content"]["lines"] = [
                    keep(
                        line,
                        {
                            "id",
                            "kind",
                            "description",
                            "amount_minor",
                            "evidence_ids",
                            "evidence",
                        },
                    )
                    for line in content["lines"]
                ]
            row["content"]["kind_of_document"] = "summary"
        changes.append(row)
    result["changes"] = changes
    # Mixed historical events are not a verified role-specific audit trail.
    result["history"] = [
        e
        for e in value.get("history", [])
        if e.get("company_role") == role and e.get("actor_id") == str(user.id)
    ]
    if role == "employee":
        from .role_housing import assigned_housing, housing_title, resident_state

        result["housing"] = assigned_housing(item, user)
        result["title"] = housing_title(result["housing"])
        result["state"] = resident_state(
            result.get("assignments", []), item.lease.occupancy_status
        )
        result["occupancy_status"] = result["state"]
        own_requests = set(
            map(
                str,
                item.maintenance_scopes.filter(request__reporter=user).values_list(
                    "request__id", flat=True
                ),
            )
        )
        maintenance = []
        for row in result.get("maintenance", []):
            for key in ("cost_minor", "cost_payer"):
                row.pop(key, None)
            if row["id"] not in own_requests:
                # A shared unit visit requires this resident's access consent;
                # it does not disclose another employee's report/discussion.
                if not row.get("appointment_at"):
                    continue
                row = keep(
                    row,
                    {
                        "id",
                        "revision",
                        "state",
                        "property_id",
                        "property_name",
                        "appointment_at",
                        "appointment_ends_at",
                        "access_approved",
                        "actions",
                    },
                )
                row["title"] = "زيارة صيانة السكن / Housing maintenance visit"
            maintenance.append(row)
        result["maintenance"] = maintenance
    return result


def preparation(value, item, user):
    from .role_context import http_context
    from .contract_access import roles_for
    from .role_context import narrow

    historical_owner = str(user.id) == item.snapshot["owner_id"] and bool(
        narrow(user, item.booking.request.company, {"owner"})
    )
    if (
        http_context(user) is None
        or historical_owner
        or "owner" in roles_for(item, user)
    ):
        return value
    role = selected(user, item.booking.request.company)
    value = dict(value)
    value["active_role"] = role
    value["role_projection_version"] = 1
    # A role sees its own consent, never deliberations made in another role.
    value["reviews"] = [
        r
        for r in value["reviews"]
        if r["actor_id"] == str(user.id) and r["role"] == role
    ]
    value["pending_review_count"] = sum(
        r["decision"] == "pending" for r in value["reviews"]
    )
    if role != "coordinator":
        value.pop("signer_name", None)
        value.pop("payer_name", None)
    if role == "employee":
        from .role_housing import housing_title

        value["title"] = housing_title(value.get("units", []))
        for key in (
            "package",
            "full_term_rent_minor",
            "deposit_minor",
            "currency",
            "exponent",
            "quote_expires_at",
            "hold_expires_at",
            "booking_id",
            "provider_available",
            "blocking_reasons",
            "renter_kind",
            "payer_kind",
            "employees_are_debtors",
        ):
            value.pop(key, None)
    if role in {"payer", "signer"}:
        # Placements and the identities of residents belong to coordination.
        value.pop("placements", None)
    if role == "payer":
        value["package"] = keep(
            value.get("package", {}),
            {
                "id",
                "revision",
                "full_term_rent_minor",
                "deposit_minor",
                "quote_expires_at",
            },
        )
        value["package"]["kind_of_document"] = "summary"
    return value
