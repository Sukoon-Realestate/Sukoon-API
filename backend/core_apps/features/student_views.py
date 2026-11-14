from functools import partial
from .services.student_housing import entry_commands as entry_commands

"""Authenticated student endpoints using existing envelopes, pagination and receipts."""

from core_apps.features.http import ActionPolicy, FeatureAPIView
from rest_framework.permissions import IsAuthenticated


from core_apps.common.locale_middleware import resolve_request_language

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .renderers import FeatureJsonRenderer
from .student_models import (
    Campus,
    StudentProfile,
    SharedLivingAgreement,
)
from .services.planning import mutate, page, require_planning
from .rental_lifecycle_views.common import validated
from .services.rental_lifecycle.access import property_for
from .services.student_housing import (
    plans,
    profiles,
    publication,
    arrangements,
    policies,
)
from .services.student_housing.access import plan_for, plans_for
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


class CampusesView(FeatureAPIView):
    name = "Campuses"
    http_method_names = ["get", "options"]
    permission_classes = [AllowAny]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "student_views",
            "campuses",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        query = request.query_params.get("search", "").strip()[:200]
        qs = Campus.objects.filter(
            active=True,
            university__active=True,
            city__is_active=True,
            city__governorate__is_active=True,
        ).select_related("university", "city")
        if query:
            qs = qs.filter(
                Q(name_en__icontains=query)
                | Q(name_ar__icontains=query)
                | Q(university__name_en__icontains=query)
                | Q(university__name_ar__icontains=query)
            )
        return page(
            request,
            qs.order_by(
                "university__sort_order",
                "university__name_en",
                "sort_order",
                "name_en",
                "id",
            ),
            lambda c: profiles.campus_payload(c, resolve_request_language(request)),
        )


# Stable callable import for integrations; URLs use the explicit class.
campuses = CampusesView.as_view()


class StudentProfileView(FeatureAPIView):
    name = "Student Profile"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "student_views",
            "student_profile",
            boundary="planning",
            capability="student_planning",
            typed=False,
        ),
        "post": ActionPolicy(
            "student_views",
            "student_profile",
            boundary="planning",
            capability="student_planning",
            typed=False,
        ),
    }

    def get(self, request):
        return Response(
            profiles.profile_payload(
                StudentProfile.objects.filter(user=request.user).first(), request.user
            )
        )

    def post(self, request):
        data = validated(StudentProfileBody, request.data)
        return mutate(
            request,
            "student_profile.save",
            lambda: None,
            lambda _, revision: profiles.save_profile(request.user, data),
            lambda item: profiles.profile_payload(item, request.user),
        )


# Stable callable import for integrations; URLs use the explicit class.
student_profile = StudentProfileView.as_view()


class AcademicPlansView(FeatureAPIView):
    name = "Academic Plans"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "student_views",
            "academic_plans",
            boundary="planning",
            capability="student_planning",
            typed=False,
        ),
        "post": ActionPolicy(
            "student_views",
            "academic_plans",
            boundary="planning",
            capability="student_planning",
            typed=False,
        ),
    }

    def get(self, request):
        qs = plans_for(request.user)
        if request.query_params.get("group_id"):
            qs = qs.filter(group__id=request.query_params["group_id"])
        return page(
            request,
            qs.order_by("-created_at", "id"),
            lambda item: plans.payload(item, request.user),
        )

    def post(self, request):
        data = validated(PlanBody, request.data)
        return mutate(
            request,
            "academic_plan.create",
            lambda: None,
            lambda _, revision: plans.save_plan(request.user, data),
            lambda item: plans.payload(item, request.user),
            creating=True,
        )


# Stable callable import for integrations; URLs use the explicit class.
academic_plans = AcademicPlansView.as_view()


class AcademicPlanView(FeatureAPIView):
    name = "Academic Plan"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "student_views",
            "academic_plan",
            boundary="planning",
            capability="student_planning",
            typed=False,
        ),
    }

    def get(self, request, plan_id):
        return Response(plans.payload(plan_for(request.user, plan_id), request.user))


# Stable callable import for integrations; URLs use the explicit class.
academic_plan = AcademicPlanView.as_view()


class PlanHistoryView(FeatureAPIView):
    name = "Plan History"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "student_views",
            "plan_history",
            boundary="planning",
            capability="student_planning",
            typed=False,
        ),
    }

    def get(self, request, plan_id):
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


# Stable callable import for integrations; URLs use the explicit class.
plan_history = PlanHistoryView.as_view()


class PlanPreviewView(FeatureAPIView):
    name = "Plan Preview"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "student_views",
            "plan_preview",
            boundary="planning",
            capability="student_demand",
            typed=False,
        ),
    }

    def get(self, request, plan_id):
        plan = plan_for(request.user, plan_id)
        return Response(
            {
                **plans.payload(plan, request.user),
                "publication_preview": publication.preview(plan),
            }
        )


# Stable callable import for integrations; URLs use the explicit class.
plan_preview = PlanPreviewView.as_view()


class PlanActionView(FeatureAPIView):
    name = "Plan Action"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "student_views",
            "plan_action",
            boundary="planning",
            capability="student_planning",
            typed=False,
        ),
    }

    def post(self, request, plan_id, action):
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

        apply = partial(
            entry_commands.plan_action_post_apply,
            action=action,
            actor=request.user,
            data=data,
        )

        return mutate(
            request,
            f"academic_plan.{action}.{plan_id}",
            lambda: plan_for(request.user, plan_id, lock=True),
            apply,
            lambda item: plans.payload(item, request.user),
        )


# Stable callable import for integrations; URLs use the explicit class.
plan_action = PlanActionView.as_view()


class LivingArrangementsView(FeatureAPIView):
    name = "Living Arrangements"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "student_views",
            "living_arrangements",
            boundary="planning",
            capability="student_planning",
            typed=True,
        ),
        "post": ActionPolicy(
            "student_views",
            "living_arrangements",
            boundary="planning",
            capability="student_planning",
            typed=True,
        ),
    }

    def get(self, request, plan_id):
        plan = plan_for(request.user, plan_id)
        return page(
            request,
            plan.arrangements.order_by("-created_at", "id"),
            lambda item: arrangements.payload(item, request.user),
        )

    def post(self, request, plan_id):
        plan_for(request.user, plan_id)
        data = validated(ArrangementBody, request.data)
        require_planning(
            request.user,
            "exam_arrangements" if data["kind"] == "exam" else "shared_living",
        )
        return mutate(
            request,
            f"student_arrangement.create.{plan_id}",
            lambda: plan_for(request.user, plan_id, lock=True),
            lambda parent, revision: arrangements.propose(request.user, parent, data),
            lambda item: arrangements.payload(item, request.user),
            creating=True,
        )


# Stable callable import for integrations; URLs use the explicit class.
living_arrangements = LivingArrangementsView.as_view()


class LivingArrangementView(FeatureAPIView):
    name = "Living Arrangement"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "student_views",
            "living_arrangement",
            boundary="planning",
            capability="student_planning",
            typed=True,
        ),
        "post": ActionPolicy(
            "student_views",
            "living_arrangement",
            boundary="planning",
            capability="student_planning",
            typed=True,
        ),
    }

    def get(self, request, arrangement_id, action=""):
        found = get_object_or_404(SharedLivingAgreement, id=arrangement_id)
        plan_for(request.user, found.plan.id)
        require_planning(
            request.user,
            "exam_arrangements" if found.kind == "exam" else "shared_living",
        )
        if action == "history":
            period = (
                found.plan.group.memberships.filter(user=request.user, status="active")
                .values_list("joined_revision", flat=True)
                .first()
            )
            return page(
                request,
                arrangements.history(found),
                lambda event: arrangements.history_payload(event, request.user, period),
            )
        if action:
            raise NotFound()
        return Response(
            {
                **arrangements.payload(found, request.user),
                "plan": plans.payload(found.plan, request.user),
            }
        )

    def post(self, request, arrangement_id, action=""):
        found = get_object_or_404(SharedLivingAgreement, id=arrangement_id)
        plan_for(request.user, found.plan.id)
        require_planning(
            request.user,
            "exam_arrangements" if found.kind == "exam" else "shared_living",
        )
        if action not in {"decide", "revise"}:
            raise NotFound()
        data = validated(
            ArrangementBody if action == "revise" else ConsentBody, request.data
        )
        if action == "revise" and data["kind"] != found.kind:
            raise ValidationError(
                {"kind": "Create a separate arrangement for a different kind."}
            )
        load = partial(
            entry_commands.living_arrangement_post_load, actor=request.user, found=found
        )
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


# Stable callable import for integrations; URLs use the explicit class.
living_arrangement = LivingArrangementView.as_view()


class StudentOfferPolicyView(FeatureAPIView):
    name = "Student Offer Policy"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "student_views",
            "student_offer_policy",
            boundary="planning",
            capability="student_offer_policies",
            typed=False,
        ),
        "post": ActionPolicy(
            "student_views",
            "student_offer_policy",
            boundary="planning",
            capability="student_offer_policies",
            typed=False,
        ),
    }

    def get(self, request, property_id):
        prop = property_for(request.user, property_id)
        return page(
            request,
            prop.student_policies.filter(active=True).order_by("offer_id"),
            policies.policy_payload,
        )

    def post(self, request, property_id):
        data = validated(StudentPolicyBody, request.data)
        load = partial(
            entry_commands.student_offer_policy_post_load,
            actor=request.user,
            property_id=property_id,
        )
        return mutate(
            request,
            f"student_policy.save.{property_id}.{data['offer_id']}",
            load,
            lambda _, revision: policies.save_policy(
                request.user, property_for(request.user, property_id, owner=True), data
            ),
            policies.policy_payload,
        )


# Stable callable import for integrations; URLs use the explicit class.
student_offer_policy = StudentOfferPolicyView.as_view()
