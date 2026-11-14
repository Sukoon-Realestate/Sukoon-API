from functools import partial
from ..services.rental_lifecycle import cases_commands as commands

from core_apps.features.http import ActionPolicy, FeatureAPIView
from rest_framework.permissions import IsAuthenticated
from core_apps.features.renderers import FeatureJsonRenderer

from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from ..rental_lifecycle_serializers import CaseBody, CaseActionBody
from ..services.rental_lifecycle.cases import case_queryset, case_payload
from .common import page, validated, mutate


class RentalCasesView(FeatureAPIView):
    name = "Rental Cases"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "cases", "rental_cases", boundary="standard", capability=None, typed=False
        ),
        "post": ActionPolicy(
            "cases", "rental_cases", boundary="standard", capability=None, typed=False
        ),
    }

    def get(self, request, operations=False):
        if operations:
            from ..services.rental_lifecycle.common import require_staff
            from ..services.rental_lifecycle.cases import ROLES

            require_staff(request.user, ROLES)
        return page(
            request,
            case_queryset(request.user).order_by("due_at", "id"),
            lambda item: case_payload(item, request.user),
        )

    def post(self, request, operations=False):
        if operations:
            from ..services.rental_lifecycle.common import require_staff
            from ..services.rental_lifecycle.cases import ROLES

            require_staff(request.user, ROLES)
        data = validated(CaseBody, request.data)
        authorize = partial(
            commands.rental_cases_post_authorize, actor=request.user, data=data
        )
        execute = partial(
            commands.rental_cases_post_execute, actor=request.user, data=data
        )
        return mutate(request, "rental_case.create", authorize, execute)


# Stable callable import for integrations; URLs use the explicit class.
rental_cases = RentalCasesView.as_view()


class RentalCaseView(FeatureAPIView):
    name = "Rental Case"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "cases", "rental_case", boundary="standard", capability=None, typed=False
        ),
        "post": ActionPolicy(
            "cases", "rental_case", boundary="standard", capability=None, typed=False
        ),
    }

    def get(self, request, case_id, operations=False):
        if operations:
            from ..services.rental_lifecycle.common import require_staff
            from ..services.rental_lifecycle.cases import ROLES

            require_staff(request.user, ROLES)
        item = get_object_or_404(case_queryset(request.user), id=case_id)
        return Response(case_payload(item, request.user))

    def post(self, request, case_id, operations=False):
        if operations:
            from ..services.rental_lifecycle.common import require_staff
            from ..services.rental_lifecycle.cases import ROLES

            require_staff(request.user, ROLES)
        get_object_or_404(case_queryset(request.user), id=case_id)
        data = validated(CaseActionBody, request.data)
        from ..services.rental_lifecycle.case_commands import act_on_case

        output, status = act_on_case(
            request.user, case_id, data, command_data=request.data
        )
        return Response(output, status=status)


# Stable callable import for integrations; URLs use the explicit class.
rental_case = RentalCaseView.as_view()
