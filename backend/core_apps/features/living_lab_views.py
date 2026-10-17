from rest_framework.response import Response

from .living_lab_models import LivingLabAuditEvent, SharedLivingLab
from .services.living_lab.access import CAPABILITY, group_for, lab_for
from .services.living_lab.commands import change, create
from .services.living_lab.projections import lab_payload, private_payload
from .services.planning import mutate, page, planning_api, require_planning


@planning_api(["GET", "POST"], None)
def living_labs(request, group_id):
    group = group_for(request.user, group_id)
    if request.method == "GET":
        member = group.memberships.get(user=request.user, status="active")
        labs = SharedLivingLab.objects.filter(
            group=group,
            access_group_revision__gte=member.joined_revision,
        ).order_by("-created_at", "pkid")
        return page(
            request, labs, lambda row: lab_payload(row, request.user, detail=False)
        )
    require_planning(request.user, CAPABILITY)
    return mutate(
        request,
        f"living_lab.create:{group_id}",
        lambda: group_for(request.user, group_id, lock=True, coordinator=True),
        lambda group, _: create(request, group),
        lambda lab: lab_payload(lab, request.user),
        creating=True,
    )


@planning_api(["GET"], None)
def living_lab_detail(request, lab_id):
    lab = lab_for(request.user, lab_id)
    LivingLabAuditEvent.objects.create(lab=lab, actor=request.user, event="read")
    return Response(lab_payload(lab, request.user))


@planning_api(["GET", "POST", "PUT"], None)
def living_lab_requirements(request, lab_id):
    lab = lab_for(request.user, lab_id)
    if request.method == "GET":
        LivingLabAuditEvent.objects.create(
            lab=lab, actor=request.user, event="read_own_requirements"
        )
        return Response(private_payload(lab, request.user))
    require_planning(request.user, CAPABILITY)
    return mutate(
        request,
        f"living_lab.requirements:{lab_id}",
        lambda: lab_for(request.user, lab_id, lock=True),
        lambda lab, _: change(request, lab, "requirements"),
        lambda lab: lab_payload(lab, request.user),
    )


@planning_api(["POST"], None)
def living_lab_action(request, lab_id, action):
    if action != "withdraw":
        require_planning(request.user, CAPABILITY)
    lab = lab_for(request.user, lab_id)
    if action in {"run", "scenario"}:
        # Record authorized attempts, including rejected limits and identical retries, without private values.
        LivingLabAuditEvent.objects.create(
            lab=lab, actor=request.user, event=f"{action}_attempt"
        )
    return mutate(
        request,
        f"living_lab.{action}:{lab_id}",
        lambda: lab_for(request.user, lab_id, lock=True),
        lambda lab, _: _apply_action(request, lab, action),
        lambda lab: lab_payload(lab, request.user),
    )


def _apply_action(request, lab, action):
    if action == "scenario":
        from .services.living_lab.journeys import child_lab

        return child_lab(request, lab)
    return change(request, lab, action)
