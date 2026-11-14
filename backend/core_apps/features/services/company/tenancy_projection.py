"""Company tenancy projections disclose only the viewer's actual responsibility."""

from django.utils import timezone
from ...models import RentalEvidence
from ...providers import mock_completion_metadata
from . import tenancy_access as access


def payload(item, user):
    """Stable service import; prepare current disclosure facts for each read."""
    from .tenancy_reads import payload as prepared_payload

    return prepared_payload(item, user)


def review_content(content, lease, *, redact_people=False):
    from ..evidence_projection import evidence_payload

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


def assignment_actions(item, row, user, *, prepared_roles=None):
    current = access.roles(item, user) if prepared_roles is None else prepared_roles
    actions = []
    if "owner" in current or "employee" in current and user.pk == row.employee_id:
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
