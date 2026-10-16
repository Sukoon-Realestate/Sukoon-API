"""Authenticated student endpoints using existing envelopes, pagination and receipts."""

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from .student_models import (
    Campus,
    StudentProfile,
    AcademicHousingPlan,
    SharedLivingAgreement,
)
from .models import Lease
from .services.planning import (
    planning_api,
    mutate,
    page,
    check_revision,
    require_planning,
)
from .rental_lifecycle_views.common import validated
from .services.rental_lifecycle.access import property_for
from .services.rental_lifecycle.common import audit
from .services.student_housing import (
    plans,
    profiles,
    publication,
    arrangements,
    policies,
)
from .services.student_housing.access import plan_for, plans_for, coordinator_for
from .student_serializers import (
    PlanBody,
    StudentProfileBody,
    ParticipantBody,
    ConsentBody,
    PublishBody,
    CommandBody,
    ArrangementBody,
    StudentPolicyBody,
    LinkBody,
    CheckInBody,
)


@planning_api(["GET"], "student_planning")
def campuses(request):
    query = request.query_params.get("search", "").strip()[:200]
    qs = Campus.objects.filter(active=True, university__active=True).select_related(
        "university", "city"
    )
    if query:
        qs = qs.filter(
            Q(name_en__icontains=query)
            | Q(name_ar__icontains=query)
            | Q(university__name_en__icontains=query)
            | Q(university__name_ar__icontains=query)
        )
    return page(
        request,
        qs.order_by("university__name_en", "name_en", "id"),
        lambda c: profiles.campus_payload(
            c, request.headers.get("Accept-Language", "en")
        ),
    )


@planning_api(["GET", "POST"], "student_planning")
def student_profile(request):
    if request.method == "GET":
        return Response(
            profiles.profile_payload(
                StudentProfile.objects.filter(user=request.user).first(), request.user
            )
        )
    data = validated(StudentProfileBody, request.data)
    return mutate(
        request,
        "student_profile.save",
        lambda: None,
        lambda _, revision: profiles.save_profile(request.user, data),
        lambda item: profiles.profile_payload(item, request.user),
    )


@planning_api(["GET", "POST"], "student_planning")
def academic_plans(request):
    if request.method == "GET":
        qs = plans_for(request.user)
        if request.query_params.get("group_id"):
            qs = qs.filter(group__id=request.query_params["group_id"])
        return page(
            request,
            qs.order_by("-created_at", "id"),
            lambda item: plans.payload(item, request.user),
        )
    data = validated(PlanBody, request.data)
    return mutate(
        request,
        "academic_plan.create",
        lambda: None,
        lambda _, revision: plans.save_plan(request.user, data),
        lambda item: plans.payload(item, request.user),
        creating=True,
    )


@planning_api(["GET"], "student_planning")
def academic_plan(request, plan_id):
    return Response(plans.payload(plan_for(request.user, plan_id), request.user))


@planning_api(["GET"], "student_planning")
def plan_history(request, plan_id):
    plan = plan_for(request.user, plan_id)
    return page(
        request,
        plan.versions.order_by("-revision"),
        lambda item: {
            "revision": item.revision,
            "digest": item.digest,
            "label": item.snapshot["label"],
            "starts_on": item.snapshot["starts_on"],
            "ends_on_exclusive": item.snapshot["ends_on_exclusive"],
            "budget_basis": item.snapshot["budget_basis"],
            "budget_min": item.snapshot["criteria"]["budget_min"],
            "budget_max": item.snapshot["criteria"]["budget_max"],
            "intended_occupants": len(item.snapshot["participants"]),
            "own_requirements": next(
                (
                    row["requirements"]
                    for row in item.snapshot["participants"]
                    if row["user_id"] == str(request.user.id)
                ),
                {},
            ),
            "created_at": item.created_at.isoformat(),
        },
    )


@planning_api(["GET"], "student_demand")
def plan_preview(request, plan_id):
    plan = plan_for(request.user, plan_id)
    return Response(
        {
            **plans.payload(plan, request.user),
            "publication_preview": publication.preview(plan),
        }
    )


@planning_api(["POST"], "student_planning")
def plan_action(request, plan_id, action):
    serializer = {
        "edit": PlanBody,
        "requirements": ParticipantBody,
        "review": ConsentBody,
        "withdraw": ConsentBody,
        "publish": PublishBody,
        "complete": CommandBody,
        "link_lease": LinkBody,
        "check_in": CheckInBody,
    }.get(action)
    if serializer is None:
        raise NotFound()
    capability = (
        "student_demand"
        if action == "publish"
        else (
            "student_transitions"
            if action in {"link_lease", "check_in"}
            else "student_planning"
        )
    )
    require_planning(request.user, capability)
    data = validated(serializer, request.data)

    def apply(plan, revision):
        if plan.status == "completed" and action not in {"link_lease", "check_in"}:
            from .services.rental_phase2 import RentalConflict

            raise RentalConflict(
                "This period is complete. Create another plan for new requirements.",
                code="plan_completed",
            )
        if action == "edit":
            return plans.save_plan(request.user, data, plan)
        if action == "requirements":
            return plans.save_requirements(request.user, plan, data)
        if action in {"review", "withdraw"}:
            return plans.review(request.user, plan, data, withdraw=action == "withdraw")
        if action == "publish":
            return publication.publish(request.user, plan, data)
        if action == "complete":
            if not coordinator_for(request.user, plan):
                raise PermissionDenied(
                    "Only the current coordinator can complete this plan."
                )
            plan.status = "completed"
        else:
            row = get_object_or_404(plan.participants, user=request.user)
            from .services.student_housing.access import participant_current

            if row.status == "withdrawn" or not participant_current(row):
                raise PermissionDenied("Current participation is required.")
            lease = get_object_or_404(Lease, id=data["lease_id"], tenant=request.user)
            if action == "link_lease":
                row.lease = lease
                row.save(update_fields=["lease", "updated_at"])
            else:
                if lease.pk not in {row.lease_id, plan.current_lease_id}:
                    raise ValidationError(
                        {
                            "lease_id": "Link your own rental to this plan before reporting an issue."
                        }
                    )
                if lease.status not in {"active", "termination_pending", "ended"}:
                    raise ValidationError(
                        {"lease_id": "A supported confirmed agreement is required."}
                    )
                from .services.rental_lifecycle.cases import open_system_case

                item = open_system_case(
                    kind={
                        "access": "access_failure",
                        "wrong_space": "move_in_mismatch",
                        "missing_facility": "move_in_mismatch",
                    }.get(data["kind"], data["kind"]),
                    source_key=f"student-check-in:{request.user.id}:{data['request_key']}",
                    actor=request.user,
                    lease=lease,
                    reason=data["note"],
                    next_action="Review the student's report and coordinate the existing maintenance, change or support process.",
                )
                item.baseline = {**item.baseline, "academic_plan_id": str(plan.id)}
                item.save(update_fields=["baseline", "updated_at"])
        plan.revision += 1
        plan.save(update_fields=["revision", "status", "updated_at"])
        audit(plan, request.user, "academic_plan." + action)
        return plan

    return mutate(
        request,
        f"academic_plan.{action}.{plan_id}",
        lambda: plan_for(request.user, plan_id, lock=True),
        apply,
        lambda item: plans.payload(item, request.user),
    )


@planning_api(["GET", "POST"], "student_planning", typed=True)
def living_arrangements(request, plan_id):
    plan = plan_for(request.user, plan_id)
    if request.method == "GET":
        return page(
            request,
            plan.arrangements.order_by("-created_at", "id"),
            lambda item: arrangements.payload(item, request.user),
        )
    data = validated(ArrangementBody, request.data)
    require_planning(
        request.user, "exam_arrangements" if data["kind"] == "exam" else "shared_living"
    )
    return mutate(
        request,
        f"student_arrangement.create.{plan_id}",
        lambda: plan_for(request.user, plan_id, lock=True),
        lambda parent, revision: arrangements.propose(request.user, parent, data),
        lambda item: arrangements.payload(item, request.user),
        creating=True,
    )


@planning_api(["GET", "POST"], "student_planning", typed=True)
def living_arrangement(request, arrangement_id, action=""):
    found = get_object_or_404(SharedLivingAgreement, id=arrangement_id)
    plan_for(request.user, found.plan.id)
    require_planning(
        request.user, "exam_arrangements" if found.kind == "exam" else "shared_living"
    )
    if request.method == "GET":
        return Response(arrangements.payload(found, request.user))
    if action not in {"decide", "revise"}:
        raise NotFound()
    data = validated(
        ArrangementBody if action == "revise" else ConsentBody, request.data
    )
    if action == "revise" and data["kind"] != found.kind:
        raise ValidationError(
            {"kind": "Create a separate arrangement for a different kind."}
        )

    def load():
        plan_for(request.user, found.plan.id, lock=True)
        return SharedLivingAgreement.objects.select_for_update().get(pk=found.pk)

    return mutate(
        request,
        f"student_arrangement.{action}.{arrangement_id}",
        load,
        lambda item, revision: (
            arrangements.propose(request.user, item.plan, data, item)
            if action == "revise"
            else arrangements.decide(request.user, item, data)
        ),
        lambda item: arrangements.payload(item, request.user),
    )


@planning_api(["GET", "POST"], "student_offer_policies")
def student_offer_policy(request, property_id):
    if request.method == "GET":
        prop = property_for(request.user, property_id)
        return page(
            request,
            prop.student_policies.filter(active=True).order_by("offer_id"),
            policies.policy_payload,
        )
    data = validated(StudentPolicyBody, request.data)

    def load():
        property_for(request.user, property_id, owner=True, lock=True)
        return None

    return mutate(
        request,
        f"student_policy.save.{property_id}.{data['offer_id']}",
        load,
        lambda _, revision: policies.save_policy(
            request.user, property_for(request.user, property_id, owner=True), data
        ),
        policies.policy_payload,
    )
