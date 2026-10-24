from django.utils import timezone
from ...planning_models import PlanningEvent
from ..planning import display_name
from .access import members, is_member, actions
from .commands import consented


def allocation_payload(row, viewer):
    own = viewer.pk in {row.tenant_id, row.proposal.property.owner_id}
    invitation = row.invitation
    lease = invitation.lease if invitation and invitation.lease_id else None
    progress = "planning"
    if invitation:
        progress = (
            "invited" if invitation.status in {"pending", "accepted"} else "stopped"
        )
        if not lease and invitation.expires_at <= timezone.now():
            progress = "stopped"
    if lease:
        progress = "contracting"
        if lease.status in {"cancelled", "expired", "ended"}:
            progress = "stopped"
        elif lease.occupancy_status == "occupied":
            progress = "received"
        elif lease.status == "active":
            progress = "awaiting_handover"
    from ..planning import offer_money, money

    rent, deposit = offer_money(row.selection)
    return {
        "rent": money(rent),
        "deposit": money(deposit),
        "tenant_id": str(row.tenant.id),
        "name": display_name(row.tenant),
        "selection": row.selection,
        "progress": progress,
        "interest_id": str(row.interest.id) if own and row.interest_id else "",
        "terms_id": str(row.terms.id) if own and row.terms_id else "",
        "terms": row.terms.terms if own and row.terms_id else {},
        "invitation_id": str(invitation.id) if own and invitation else "",
        "lease_id": str(lease.id) if own and lease else "",
    }


def proposal_payload(proposal, viewer, plan_actions):
    available = set(plan_actions)
    if proposal.status == "candidate":
        available &= {"consent_selection", "submit"}
    elif proposal.status == "submitted":
        available &= {"owner_accept", "owner_reject", "request_changes"}
    elif proposal.status == "terms":
        available &= {
            "consent_terms",
            "send_invitations",
            "request_changes",
            "owner_reject",
        }
    else:
        available = set()
    selected = consented(proposal, "selection")
    independent = consented(proposal, "independent")
    if str(viewer.id) in selected:
        available.discard("consent_selection")
    if str(viewer.id) in independent:
        available.discard("consent_terms")
    if len(selected) != 2:
        available.discard("submit")
    if len(independent) != 2:
        available.discard("send_invitations")
    return {
        "id": str(proposal.id),
        "revision": proposal.revision,
        "status": proposal.status,
        "property_id": str(proposal.property.id),
        "title": proposal.property.title,
        "note": proposal.note,
        "owner_id": str(proposal.property.owner.id),
        "selection_consents": sorted(selected),
        "independent_consents": sorted(independent),
        "allowed_actions": sorted(available),
        "allocations": [
            allocation_payload(row, viewer)
            for row in proposal.allocations.select_related(
                "tenant",
                "terms",
                "interest",
                "invitation__lease",
                "proposal__property__owner",
            ).order_by("tenant_id")
        ],
    }


def payload(plan, viewer):
    allowed = actions(plan, viewer)
    query = plan.proposals.select_related("property__owner").order_by("-created_at")
    if not is_member(plan, viewer):
        query = query.filter(property__owner=viewer)
    proposals = [proposal_payload(value, viewer, allowed) for value in query]
    status = plan.status
    if status == "handed_off":
        active = next(
            (value for value in proposals if value["status"] == "handed_off"), None
        )
        stages = [row["progress"] for row in active["allocations"]] if active else []
        if stages and all(value == "received" for value in stages):
            status = "completed"
        elif "stopped" in stages:
            status = (
                "partial" if any(value != "stopped" for value in stages) else "closed"
            )
    elif plan.status != "closed" and plan.expires_at <= timezone.now():
        status = "expired"
    return {
        "id": str(plan.id),
        "revision": plan.revision,
        "status": status,
        "connection_id": str(plan.connection.id),
        "coordinator_id": str(plan.coordinator.id),
        "is_member": is_member(plan, viewer),
        "criteria": plan.criteria,
        "published": plan.published and status == "searching",
        "expires_at": plan.expires_at.isoformat(),
        "publication_consents": plan.publication_consents,
        "participants": [
            {"id": str(user.id), "name": display_name(user)} for user in members(plan)
        ],
        "allowed_actions": ["read", *allowed],
        "proposals": proposals,
        "next_step": {
            "invited": "accept_invite",
            "searching": "choose_housing",
            "reviewing": "review_pair",
            "handed_off": "continue_individually",
            "partial": "continue_individually",
        }.get(status, "view_history"),
    }


def record_event(plan, actor, operation):
    recipients = {user.pk: (user, "tenant") for user in members(plan)}
    for proposal in plan.proposals.exclude(status="candidate").select_related(
        "property__owner"
    ):
        owner = proposal.property.owner
        recipients[owner.pk] = (owner, "owner")
    for user, workspace in recipients.values():
        if user.pk == actor.pk or not user.is_active:
            continue
        PlanningEvent.objects.get_or_create(
            recipient=user,
            event_key=f"shared:{operation}:{plan.id}:{plan.revision}",
            defaults={
                "destination": {
                    "action_type": "open_shared_housing_plan",
                    "target_id": str(plan.id),
                    "workspace": workspace,
                    "schema_version": "1",
                }
            },
        )
