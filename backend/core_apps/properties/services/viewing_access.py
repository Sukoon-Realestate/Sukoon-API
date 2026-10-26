"""Current authority for one canonical appointment, independent of contracting."""

from django.db.models import Q, F
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError
from core_apps.features.company_models import CompanyMembership
from core_apps.features.planning_models import GroupProcess
from ..models import PropertyVisit


def group_process(visit):
    return (
        GroupProcess.objects.filter(visit=visit)
        .select_related("group", "academic_plan")
        .first()
    )


def participant(visit, user):
    if not user or not user.is_active:
        return False
    if visit.company_id:
        return (
            visit.tenant_id == user.pk
            and CompanyMembership.objects.filter(
                company_id=visit.company_id, user=user, is_active=True
            ).exists()
        )
    process = group_process(visit)
    if process:
        return (
            str(user.id) in process.participant_ids
            and str(user.id) in process.consented_ids
            and process.group.memberships.filter(
                user=user,
                status="active",
                joined_revision__lte=process.access_group_revision,
            ).exists()
            and (
                not process.academic_plan_id
                or process.academic_plan.participants.filter(user=user)
                .exclude(status="withdrawn")
                .exists()
            )
        )
    return visit.tenant_id == user.pk


def can_read(visit, user):
    if not user or not user.is_active:
        return False
    if visit.property.owner_id == user.pk or participant(visit, user):
        return True
    return bool(
        visit.company_id
        and CompanyMembership.objects.filter(
            company_id=visit.company_id, user=user, is_active=True, is_coordinator=True
        ).exists()
    )


def for_user(user):
    from core_apps.features.student_models import AcademicPlanParticipant

    current_plans = (
        AcademicPlanParticipant.objects.filter(user=user)
        .exclude(status="withdrawn")
        .values("plan_id")
    )
    processes = GroupProcess.objects.filter(
        group__memberships__user=user,
        group__memberships__status="active",
        group__memberships__joined_revision__lte=F("access_group_revision"),
        participant_ids__contains=[str(user.id)],
        consented_ids__contains=[str(user.id)],
    ).filter(Q(academic_plan__isnull=True) | Q(academic_plan_id__in=current_plans))
    result = PropertyVisit.objects.filter(
        Q(company__isnull=True, tenant=user, groupprocess__isnull=True)
        | Q(
            company__memberships__user=user,
            company__memberships__is_active=True,
            company__memberships__is_coordinator=True,
        )
        | Q(
            company__memberships__user=user,
            company__memberships__is_active=True,
            tenant=user,
        )
        | Q(groupprocess__in=processes)
    ).distinct()
    return result


def prepare_context(actor, raw):
    kind = raw.get("kind", "personal")
    if kind not in {"personal", "student", "company"}:
        raise ValidationError(
            {
                "viewing_context": "Use personal, student or company; group bookings use the existing group consent flow."
            }
        )
    result = {"requested_by": actor, "context_kind": kind}
    if kind == "company":
        from core_apps.features.services.company.access import company_for

        company = company_for(actor, raw.get("company_id"), "coordinate", lock=True)
        if company.review_status != "verified":
            raise PermissionDenied(
                "Company authority must be reviewed before booking on its behalf."
            )
        representative = get_object_or_404(
            CompanyMembership.objects.select_for_update().select_related("user"),
            company=company,
            id=raw.get("representative_membership_id"),
            is_active=True,
            user__is_active=True,
        )
        result.update(company=company, tenant=representative.user)
    elif raw.get("company_id") or raw.get("representative_membership_id"):
        raise ValidationError(
            {
                "viewing_context": "Company authority cannot be attached to a personal appointment."
            }
        )
    if raw.get("academic_plan_id"):
        if kind != "student":
            raise ValidationError(
                {"viewing_context": "Use a student context for an academic plan."}
            )
        from core_apps.features.services.student_housing.access import plan_for

        plan = plan_for(actor, raw["academic_plan_id"], lock=True)
        if plan.group_id:
            raise ValidationError(
                {
                    "viewing_context": "Use the existing group consent flow for a group appointment."
                }
            )
        result["academic_plan"] = plan
    return result


def context_payload(visit, actor):
    from core_apps.features.planning_group_views_parts.process_payload import (
        process_history,
    )

    process = group_process(visit)
    kind = (
        "student_group"
        if process and process.academic_plan_id
        else "group" if process else visit.context_kind
    )
    attendees = []
    if process and (actor.pk == visit.property.owner_id or participant(visit, actor)):
        # Share attendance/decision identities, never another participant's reason.
        for membership in process.group.memberships.filter(
            user__id__in=process.participant_ids
        ).select_related("user"):
            user = membership.user
            decision = visit.participant_decisions.filter(tenant=user).first()
            from .post_visit_decision_parts.continuation import contracting_problem

            can_invite = (
                actor.pk == visit.property.owner_id
                and participant(visit, user)
                and decision
                and decision.value == "proceed"
                and not contracting_problem(visit, decision)
                and not visit.rental_invitations.filter(
                    tenant=user, status__in=["pending", "accepted"]
                ).exists()
            )
            attendees.append(
                {
                    "user_id": str(user.id),
                    "name": user.get_full_name,
                    "current": participant(visit, user),
                    "decision": decision.value if decision else None,
                    "decision_id": str(decision.id) if decision else None,
                    "can_invite": bool(can_invite),
                }
            )
    return {
        "kind": kind,
        "history": visit.change_history if can_read(visit, actor) else [],
        "company_id": str(visit.company.id) if visit.company_id else None,
        "company_name": visit.company.name if visit.company_id else None,
        "academic_plan_id": (
            str(visit.academic_plan.id)
            if visit.academic_plan_id
            else (
                str(process.academic_plan.id)
                if process and process.academic_plan_id
                else None
            )
        ),
        "group_id": str(process.group.id) if process else None,
        "group_history": (
            process_history(process) if process and can_read(visit, actor) else []
        ),
        "requested_by_id": (
            str(visit.requested_by.id)
            if visit.requested_by_id
            else str(visit.tenant.id)
        ),
        "attendee_id": str(visit.tenant.id),
        "attendees": attendees,
        "can_attest": participant(visit, actor),
        "can_reassign": bool(
            visit.status in {"pending", "confirmed"}
            and visit.company_id
            and not visit.participant_decisions.exists()
            and not visit.rental_invitations.exists()
            and CompanyMembership.objects.filter(
                company_id=visit.company_id,
                user=actor,
                is_active=True,
                is_coordinator=True,
            ).exists()
        ),
        "contract_party": "company" if visit.company_id else "individual",
        "contracting_blocker": (
            "corporate_contract_policy_required" if visit.company_id else None
        ),
    }
