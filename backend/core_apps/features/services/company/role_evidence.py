"""Attachment audience follows its verified use, never general commercial access."""

from .tenancy_access import roles


def can_read(evidence, user):
    lease = evidence.lease
    if not lease.renter_company_id:
        return user.pk in {lease.owner_id, lease.tenant_id}
    item = lease.company_tenancy
    current = roles(item, user)
    if "owner" in current:
        return True
    scope = (evidence.media_metadata or {}).get("company_role")
    if evidence.uploader_id == user.pk and scope in current:
        return True
    # Historical uploads without an audience are accessible only when attached
    # to a reviewed, typed workflow for this role. Unattached legacy files stay
    # undisclosed until their use is established.
    for change in item.changes.all():
        content = change.snapshot.get("content", {})
        if current & {"coordinator"} and change.kind in {"move_in", "move_out"}:
            if str(evidence.id) in content.get("evidence_ids", []):
                return True
        if "payer" in current and change.kind in {
            "settlement",
            "settlement_adjustment",
        }:
            if any(
                str(evidence.id) in line.get("evidence_ids", [])
                for line in content.get("lines", [])
            ):
                return True
    return False
