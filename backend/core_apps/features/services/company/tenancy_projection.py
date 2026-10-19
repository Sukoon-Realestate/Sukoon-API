"""Company tenancy projections disclose only the viewer's actual responsibility."""

from django.utils import timezone
from ...models import (
    CompanyMembership,
    RentalOperationalCase,
    RentalEvidence,
    FinalSettlement,
    RentalChargeback,
)
from ...providers import fake_provider_available, mock_completion_metadata
from ..rental_phase3 import invoice_balance_minor, invoice_payment_allowed
from ..rental_phase6 import closure_blocking_reasons
from . import tenancy_access as access


def payload(item, user):
    from ..business_policies import public_bound
    from django.utils.translation import get_language
    from ..chargebacks.projection import payload as chargeback_payload

    roles = access.roles(item, user)
    from . import tenancy_initial_recovery as initial_recovery

    release_pending = initial_recovery.pending(item)
    commercial = bool(roles - access.PRIVATE_ONLY)
    lease = item.lease
    booking = item.preparation.booking
    assignments = list(
        booking.assignments.select_related("employee", "property").order_by(
            "created_at"
        )
    )
    visible_assignments = (
        assignments
        if commercial
        else [r for r in assignments if r.employee_id == user.pk]
    )
    allowed = ["open_case"]
    provider = fake_provider_available()
    blockers = []
    if lease.status in {"draft", "pending_signatures"}:
        from .tenancy_contracts import validate_unsigned
        from ..rental_phase2 import RentalConflict

        try:
            validate_unsigned(item)
        except RentalConflict as exc:
            blockers.append(str(exc.get_codes()))
    if not provider and lease.status in {"draft", "pending_signatures", "signed"}:
        blockers.append("signature_payment_provider_unavailable")
    if roles & {"owner", "coordinator", "signer", "payer"}:
        allowed += ["reconcile"]
    if lease.status == "draft" and not any(
        b != "signature_payment_provider_unavailable" for b in blockers
    ):
        if roles & {"owner", "signer"}:
            allowed += ["review"]
        if (
            "owner" in roles
            and set(item.contract_reviews) == {"owner", "signer"}
            and provider
        ):
            allowed += ["submit_signature"]
    if (
        lease.status in {"draft", "expired", "pending_signatures"}
        and roles & {"owner", "coordinator"}
        and not (
            lease.status == "pending_signatures" and lease.signing_sessions.exists()
        )
        and not lease.signing_sessions.filter(
            status__in=["pending", "completed", "review_required"]
        ).exists()
        and not lease.invoices.exists()
    ):
        allowed += ["cancel"]
    if (
        lease.status == "pending_signatures"
        and roles & {"owner", "signer"}
        and provider
        and not blockers
        and not release_pending
        and not lease.signing_sessions.filter(
            signer=user, document_id=lease.document_id, document_hash=lease.document_hash
        ).exists()
    ):
        allowed += ["sign"]
    if roles & {"owner", "signer"} and initial_recovery.can_propose(item):
        allowed += ["release_agreement"]
    if release_pending:
        blockers.append("initial_release_pending")
    if lease.status in {"active", "termination_pending", "ended"}:
        if roles & {"owner", "coordinator"} and (
            lease.occupancy_status
            in {"occupied", "move_out_pending", "handover_disputed"}
            or lease.occupancy_status == "not_started"
            and lease.status in {"active", "ended"}
        ):
            allowed += ["handover"]
        if roles & {"owner", "employee"}:
            allowed += ["presence", "presence_respond"]
        if lease.occupancy_status != "returned" and (
            roles & {"owner", "coordinator"}
            or any(r.occupancy_status == "occupied" for r in visible_assignments)
        ):
            allowed += ["maintenance"]
    if lease.status == "active":
        if "coordinator" in roles:
            allowed += ["replace_employee"]
    if lease.status in {"signed", "active"}:
        if roles & {"owner", "signer"}:
            allowed += ["terminate"]
    if (
        lease.status in {"ended", "cancelled"}
        and roles & {"owner", "payer"}
        and lease.occupancy_status in {"returned", "not_started"}
        and not FinalSettlement.objects.filter(
            lease=lease, execution_status="executed"
        ).exists()
    ):
        allowed += ["settlement"]
    if (
        lease.status
        in {"signed", "active", "termination_pending", "ended", "cancelled"}
        and "administrator" in roles
    ):
        allowed += ["replace_authority"]
    if lease.status == "active" and roles & {"owner", "signer"}:
        from .tenancy_commercial import KINDS, OPEN

        if not item.changes.filter(kind__in=KINDS, state__in=OPEN).exists():
            allowed += ["commercial_change", "ownership_change"]
    if (
        lease.status in {"ended", "cancelled"}
        and roles & {"owner", "payer"}
        and FinalSettlement.objects.filter(
            lease=lease, execution_status="executed"
        ).exists()
    ):
        allowed += ["settlement_adjustment"]
    change_rows = []
    for row in item.changes.order_by("-created_at")[:100]:
        if not commercial and str(user.id) not in row.snapshot["required"].values():
            continue
        own_roles = [
            role
            for role, identity in row.snapshot["required"].items()
            if identity == str(user.id)
        ]
        change_rows.append(
            {
                "id": str(row.id),
                "revision": row.revision,
                "kind": row.kind,
                "state": row.state,
                "digest": row.snapshot_digest,
                "reason": row.reason,
                "content": (
                    review_content(
                        row.snapshot["content"], lease, redact_people=not commercial
                    )
                    if commercial
                    or set(own_roles) & {"approver", "new_owner", "financial_reviewer"}
                    or row.kind == "continuation_release"
                    and any(r.startswith("prior_signer_") for r in own_roles)
                    else {
                        k: row.snapshot["content"][k]
                        for k in [
                            "property_id",
                            "property_name",
                            "effective_on",
                            "ends_on_exclusive",
                            "employee_name",
                        ]
                        if k in row.snapshot["content"]
                    }
                ),
                "roles_to_decide": (
                    [r for r in own_roles if r not in row.decisions]
                    if row.state == "pending"
                    else []
                ),
                "can_withdraw": row.state
                in {
                    "pending",
                    "waiting_departure",
                    "accepted",
                    "pending_signatures",
                    "review_required",
                }
                and not (
                    row.rental_change_id and row.rental_change.signing_sessions.exists()
                )
                and (user.pk == row.proposed_by_id or "coordinator" in roles),
                "can_resume": row.state == "waiting_departure"
                and "coordinator" in roles,
                "rental_change_id": (
                    str(row.rental_change.id) if row.rental_change_id else ""
                ),
                "signing_roles": [
                    r
                    for r in own_roles
                    if r in {"owner", "signer", "new_owner"}
                    or r.startswith("prior_signer_")
                ],
                "continuation_actions": continuation_actions(
                    row, user, roles, provider
                ),
                "signing_sessions": continuation_sessions(row, user),
                "decisions": (
                    row.decisions
                    if commercial
                    else {r: row.decisions[r] for r in own_roles if r in row.decisions}
                ),
            }
        )
    maintenance_rows = []
    for scope in item.maintenance_scopes.select_related("request", "property"):
        if not commercial and not any(
            r.property_id == scope.property_id and r.occupancy_status == "occupied"
            for r in visible_assignments
        ):
            continue
        request = scope.request
        from .tenancy_maintenance import (
            actions as maintenance_actions,
            access_reviewers,
        )

        maintenance_rows.append(
            {
                "id": str(request.id),
                "revision": request.revision,
                "title": request.title,
                "description": request.description,
                "state": request.status,
                "property_id": str(scope.property.id),
                "property_name": scope.property.title,
                "appointment_at": (
                    request.appointment_at.isoformat()
                    if request.appointment_at
                    else None
                ),
                "appointment_ends_at": (
                    request.appointment_ends_at.isoformat()
                    if request.appointment_ends_at
                    else None
                ),
                "cost_minor": request.proposed_cost_minor if commercial else None,
                "cost_payer": request.cost_payer if commercial else "",
                "access_approved": str(user.id) in scope.access_consents
                and scope.access_consents.get(str(user.id))
                == access_reviewers(item, scope).get(str(user.id))
                and request.appointment_version > 0,
                "actions": maintenance_actions(item, scope, user),
                "events": [
                    {"action": e.action, "note": e.note}
                    for e in request.events.order_by("-created_at")[:30]
                    if commercial
                    or e.action not in {"propose_cost", "approve_cost", "reject_cost"}
                ],
            }
        )
    allowed += sorted({a for r in change_rows for a in r["continuation_actions"]})
    if any(r["roles_to_decide"] for r in change_rows):
        allowed.append("respond_change")
    if any(r["can_withdraw"] for r in change_rows):
        allowed.append("withdraw_change")
    if any(r["can_resume"] for r in change_rows):
        allowed.append("resume_change")
    if any(r["actions"] for r in maintenance_rows):
        allowed.append("maintenance_action")
    from .tenancy_continuation_projection import choices

    continuation_choices = choices(item, user, roles)
    source = item.source_snapshot
    replacement_mandates = []
    if "administrator" in roles:
        replacement_mandates = [
            m
            for m in lease.renter_company.mandates.select_related("membership__user")
            if m.membership.user_id != lease.owner_id
            and access.execution_mandate(
                m, exposure=source["full_term_rent_minor"] + source["deposit_minor"]
            )
        ]
    unit_rows = access.properties(item)
    from ..rental_phase2 import add_months

    return {
        "current_rent_minor": lease.rent_amount_minor if commercial else None,
        "suggested_renewal_end": (
            str(add_months(lease.end_date, 1)) if commercial else ""
        ),
        **continuation_choices,
        "id": str(item.id),
        "lease_id": str(lease.id),
        "revision": lease.revision,
        "company_id": str(lease.renter_company.id),
        "company_name": lease.renter_company.name,
        "title": booking.request.title,
        "state": lease.status,
        "occupancy_status": lease.occupancy_status,
        "financial_closure_status": lease.financial_closure_status,
        "roles": sorted(roles),
        "renter_kind": "company",
        "payer_kind": "company",
        "employees_are_debtors": False,
        "starts_on": str(lease.start_date),
        "ends_on_exclusive": str(lease.end_date),
        "terms_digest": item.terms_digest,
        "document_hash": lease.document_hash if commercial else "",
        "business_policies": (
            public_bound(
                lease.terms, "ar" if (get_language() or "").startswith("ar") else "en"
            )
            if commercial
            else []
        ),
        "terms": lease.terms if commercial else {},
        "reviewed_roles": list(item.contract_reviews) if commercial else [],
        "actions": allowed,
        "provider_available": provider,
        "provider_mode": "mock" if provider else "unavailable",
        "blocking_reasons": blockers,
        "closure_blocking_reasons": (
            closure_blocking_reasons(lease) if commercial else []
        ),
        "package": (
            {
                "id": str(booking.id),
                "revision": booking.revision,
                "full_term_rent_minor": source["full_term_rent_minor"],
                "deposit_minor": source["deposit_minor"],
                "quote_expires_at": source["quote_expires_at"],
                "snapshot": {
                    **source["inventory"],
                    "company_name": source["company_name"],
                    "starts_on": source["starts_on"],
                    "ends_on_exclusive": source["ends_on_exclusive"],
                },
            }
            if commercial
            else {}
        ),
        "assignments": [
            {
                "id": str(r.id),
                "revision": r.revision,
                "employee_id": str(r.employee.id),
                "employee_name": r.employee.get_full_name,
                "property_id": str(r.property.id),
                "property_name": r.property.title,
                "starts_on": str(r.starts_on),
                "ends_on_exclusive": str(r.ends_on_exclusive),
                "state": r.occupancy_status,
                "actions": assignment_actions(item, r, user),
                "confirmations": [
                    {
                        "id": str(c.id),
                        "kind": c.kind,
                        "state": c.state,
                        "revision": c.revision,
                        "possession_on": str(c.possession_on),
                        "accepted_roles": list(c.approvals),
                        "roles_to_decide": (
                            [
                                role
                                for role, actor, mapped in [
                                    ("owner", lease.owner_id, "landlord"),
                                    ("employee", r.employee_id, "employee"),
                                ]
                                if actor == user.pk and mapped not in c.approvals
                            ]
                            if c.state == "pending"
                            else []
                        ),
                    }
                    for c in r.occupancy_confirmations.all()
                ],
            }
            for r in visible_assignments
        ],
        "changes": change_rows,
        "maintenance": maintenance_rows,
        "chargebacks": (
            [
                chargeback_payload(row)
                for row in RentalChargeback.objects.filter(
                    payment_attempt__invoice__lease=lease
                )
            ] if commercial else []
        ),
        "invoices": (
            [
                {
                    "id": str(i.id),
                    "revision": i.revision,
                    "reference": i.reference,
                    "state": i.status,
                    "amount_minor": i.charges_minor,
                    "balance_minor": invoice_balance_minor(i),
                    "due_date": str(i.due_date),
                    "can_pay": invoice_payment_allowed(user, i),
                }
                for i in lease.invoices.all()
            ]
            if commercial
            else []
        ),
        "signing_sessions": [
            {
                "id": str(s.id),
                "state": s.status,
                "hosted_url": s.hosted_url,
                "expires_at": s.expires_at.isoformat(),
                "document_hash": s.document_hash,
                **mock_completion_metadata("signing-sessions", s.id, lease.revision),
            }
            for s in lease.signing_sessions.filter(signer=user).order_by("-created_at")[
                :10
            ]
        ],
        "cases": [
            {"id": str(c.id), "state": c.status, "next_action": c.next_action}
            for c in RentalOperationalCase.objects.filter(
                lease=lease, **({} if commercial else {"opened_by": user})
            ).order_by("-created_at")[:20]
        ],
        "refunds": (
            [
                {
                    "id": str(r.id),
                    "state": r.status,
                    "amount_minor": r.amount_minor,
                    "purpose": r.purpose,
                    "failure_code": r.failure_code,
                }
                for r in lease.refund_requests.order_by("created_at")
            ]
            if commercial
            else []
        ),
        "people": (
            [
                {"id": str(m.user.id), "name": m.user.get_full_name}
                for m in CompanyMembership.objects.filter(
                    company=lease.renter_company, is_active=True, is_employee=True
                ).select_related("user")[:500]
            ]
            if "coordinator" in roles
            else []
        ),
        "units": [
            {"id": str(p.id), "name": p.title}
            for p in unit_rows
            if commercial
            or any(
                a.property_id == p.pk and a.occupancy_status == "occupied"
                for a in visible_assignments
            )
        ],
        "termination_dates": (
            list(map(str, lease.billing_periods.values_list("start", flat=True)))
            + [str(lease.end_date)]
            if roles & {"owner", "signer"}
            else []
        ),
        "signer_mandates": [
            {"id": str(m.id), "name": m.membership.user.get_full_name}
            for m in replacement_mandates
            if m.kind == "sign"
        ],
        "payer_mandates": [
            {"id": str(m.id), "name": m.membership.user.get_full_name}
            for m in replacement_mandates
            if m.kind == "pay"
        ],
        "coordinators": (
            [
                {"id": str(m.id), "name": m.user.get_full_name}
                for m in lease.renter_company.memberships.filter(
                    is_active=True,
                    is_coordinator=True,
                    user__is_active=True,
                    user__is_verified=True,
                    user__sensitive_actions_frozen=False,
                )
                .exclude(user=lease.owner)
                .select_related("user")
            ]
            if "administrator" in roles
            else []
        ),
        "authority_reviewers": (
            [
                {"id": str(m.id), "name": m.user.get_full_name}
                for m in lease.renter_company.memberships.filter(
                    is_active=True, is_admin=True
                )
                .exclude(user__in=[user, lease.owner])
                .select_related("user")
            ]
            if "administrator" in roles
            else []
        ),
    }


def review_content(content, lease, *, redact_people=False):
    from ...rental_phase4_views_parts.handover_payload import evidence_payload

    def evidence(ids):
        return [
            evidence_payload(e)
            for e in RentalEvidence.objects.filter(
                lease=lease, id__in=ids, deleted_at__isnull=True
            )
        ]

    from copy import deepcopy

    result = deepcopy(content)
    if content.get("policy_scope") == "company.agreement.release":
        from ..business_policies import public
        from django.utils.translation import get_language

        result["release_policy"] = public(content["policy"], get_language())
    if redact_people:
        result.pop("roster", None)
        if "terms" in result:
            for key in ["placements", "employee_placements"]:
                result["terms"].pop(key, None)
    result["evidence"] = evidence(content.get("evidence_ids", []))
    if "lines" in content:
        result["lines"] = [
            {**line, "evidence": evidence(line.get("evidence_ids", []))}
            for line in content["lines"]
        ]
    return result


def assignment_actions(item, row, user):
    current = access.roles(item, user)
    actions = []
    if user.pk in {row.employee_id, item.lease.owner_id}:
        for kind, state in [("arrival", "arrival_pending"), ("departure", "occupied")]:
            if (
                row.occupancy_status == state
                and not row.occupancy_confirmations.filter(
                    kind=kind, state__in=["pending", "accepted"]
                ).exists()
            ):
                if kind == "departure" or (
                    item.lease.status == "active"
                    and item.lease.occupancy_status == "occupied"
                ):
                    actions.append(kind)
    if (
        "coordinator" in current
        and item.lease.status == "active"
        and row.occupancy_status in {"arrival_pending", "occupied", "returned"}
    ):
        if not item.changes.filter(
            kind="replacement",
            state="applied",
            snapshot__content__assignment_id=str(row.id),
        ).exists():
            actions.append("replace_employee")
    return actions


def continuation_actions(row, user, roles, provider):
    if not row.rental_change_id:
        return []
    result = []
    if (
        row.kind in {"renewal", "amendment", "ownership"}
        and row.state in {"accepted", "pending_signatures", "review_required"}
        and roles & {"owner", "signer"}
    ):
        result.append("release_continuation")
    if row.state == "accepted" and "owner" in roles and provider:
        result.append("submit_continuation")
    own = [
        r
        for r, identity in row.snapshot["required"].items()
        if identity == str(user.id)
        and (r in {"owner", "signer", "new_owner"} or r.startswith("prior_signer_"))
    ]
    if (
        row.state == "pending_signatures"
        and own
        and provider
        and str(user.id) not in row.rental_change.signed_by
    ):
        result.append("sign_continuation")
    if row.state == "review_required" and roles & {
        "owner",
        "coordinator",
        "signer",
        "payer",
    }:
        result.append("resume_continuation")
    return result


def continuation_sessions(row, user):
    if not row.rental_change_id:
        return []
    return [
        {
            "id": str(s.id),
            "document_id": str(s.document_id),
            "document_hash": s.document_hash,
            "state": s.status,
            "hosted_url": (
                s.hosted_url
                if s.status == "pending" and s.expires_at > timezone.now()
                else ""
            ),
            "expires_at": s.expires_at.isoformat(),
            **mock_completion_metadata(
                "change-signing-sessions", s.id, s.change_revision
            ),
        }
        for s in row.rental_change.signing_sessions.filter(signer=user)
    ]
