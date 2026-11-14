"""Preparation tasks are coordination only, never signatures or approvals."""

from core_apps.features.http import ActionPolicy, FeatureAPIView

import uuid
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..pagination import FeaturePagination
from ..renderers import FeatureJsonRenderer
from ..services.rental_phase2 import RentalConflict
from .access import require, scope_for
from .models import PreparationTask
from .sync import fingerprint


class TaskCommand(serializers.Serializer):
    operation_id = serializers.UUIDField()
    id = serializers.UUIDField(required=False)
    revision = serializers.IntegerField(min_value=0)
    title = serializers.CharField(max_length=160, required=False)
    description = serializers.CharField(
        max_length=3000, required=False, allow_blank=True
    )
    assignee_id = serializers.UUIDField(required=False)
    due_at = serializers.DateTimeField(required=False, allow_null=True)
    status = serializers.ChoiceField(
        choices=["todo", "in_progress", "completed", "cancelled"], required=False
    )
    comment = serializers.CharField(max_length=2000, required=False)


def context(request, *, lock=False):
    from ..planning_models import HousingGroup
    from ..company_models import CompanyHousingRequest
    from ..services.company.access import company_for
    from ..services.company.role_context import selected

    scope = scope_for(request)
    group_id, request_id = request.query_params.get(
        "group_id"
    ), request.query_params.get("request_id")
    if bool(group_id) == bool(request_id):
        raise ValidationError("Choose exactly one group or company request.")
    try:
        uuid.UUID(str(group_id or request_id))
    except (ValueError, TypeError):
        raise ValidationError("Invalid preparation context.")
    if group_id:
        if scope != "student":
            raise PermissionDenied("Use the student workspace for a housing group.")
        groups = (
            HousingGroup.objects.select_for_update() if lock else HousingGroup.objects
        )
        group = get_object_or_404(groups, id=group_id)
        member = get_object_or_404(
            group.memberships, user=request.user, status="active"
        )
        members = group.memberships.filter(
            status="active", user__is_active=True
        ).select_related("user")
        return (
            {"group": group},
            member.role == "admin",
            group.status == "active",
            members,
            member.joined_revision,
        )
    if not scope.startswith("company/"):
        raise PermissionDenied("Use a current company role.")
    item = get_object_or_404(
        CompanyHousingRequest.objects.select_related("company"), id=request_id
    )
    company = company_for(request.user, item.company.id, lock=lock)
    if lock:
        item = CompanyHousingRequest.objects.select_for_update().get(pk=item.pk)
    role = selected(request.user, company)
    manager = (
        role == "admin"
        or role == "coordinator"
        and item.coordinator_id == request.user.pk
    )
    members = company.memberships.filter(
        is_active=True, user__is_active=True
    ).select_related("user")
    return {"company_request": item}, manager, True, members, 0


def payload(item, *, manager, user, members, editable):
    member = next((m for m in members if m.user_id == item.assignee_id), None)
    current = member is not None and (
        not item.group_id or member.joined_revision == item.membership_period
    )
    return {
        "id": str(item.id),
        "revision": item.revision,
        "title": item.title,
        "description": item.description,
        "status": item.status,
        "assignee_id": str(item.assignee.id),
        "assignee_name": member.user.get_full_name if member else "",
        "needs_reassignment": not current,
        "due_at": item.due_at.isoformat() if item.due_at else None,
        "can_manage": manager and editable,
        "can_update": editable and (manager or current and item.assignee_id == user.pk),
        "history": item.history,
    }


class TasksView(FeatureAPIView):
    name = "Tasks"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "preparation", "tasks", boundary="standard", capability=None, typed=False
        ),
        "post": ActionPolicy(
            "preparation", "tasks", boundary="standard", capability=None, typed=False
        ),
    }

    def get(self, request):
        require("preparation")
        with transaction.atomic():
            filters, manager, editable, members, period = context(
                request, lock=request.method == "POST"
            )
            members = list(members)
            query = PreparationTask.objects.filter(**filters)
            if "company_request" in filters and not manager:
                query = query.filter(assignee=request.user)
            if request.query_params.get("context_only") == "1":
                return Response(
                    {
                        "can_manage": manager and editable,
                        "members": (
                            [
                                {"id": str(m.user.id), "name": m.user.get_full_name}
                                for m in members
                            ]
                            if manager
                            else []
                        ),
                    }
                )
            page = FeaturePagination()
            rows = page.paginate_queryset(
                query.order_by("due_at", "created_at", "pk"), request
            )
            result = page.get_paginated_response(
                [
                    payload(
                        row,
                        manager=manager,
                        user=request.user,
                        members=members,
                        editable=editable,
                    )
                    for row in rows
                ]
            )
            result.data.update(
                {
                    "can_manage": manager and editable,
                    "members": (
                        [
                            {"id": str(m.user.id), "name": m.user.get_full_name}
                            for m in members
                        ]
                        if manager
                        else []
                    ),
                }
            )
            return result

    def post(self, request):
        require("preparation")
        with transaction.atomic():
            filters, manager, editable, members, period = context(
                request, lock=request.method == "POST"
            )
            members = list(members)
            query = PreparationTask.objects.filter(**filters)
            if "company_request" in filters and not manager:
                query = query.filter(assignee=request.user)
            if not editable:
                raise PermissionDenied("This preparation board is archived.")
            serializer = TaskCommand(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            identity = data.get("id")
            if not identity:
                raise ValidationError("A stable task ID is required before sending.")
            item = query.select_for_update().filter(pk=identity).first()
            digest, operation = fingerprint(request.data), str(data["operation_id"])
            if item and operation in item.operations:
                if item.operations[operation] != digest:
                    raise RentalConflict("This operation ID has already been used.")
                return Response(
                    payload(
                        item,
                        manager=manager,
                        user=request.user,
                        members=members,
                        editable=editable,
                    )
                )
            creating = item is None
            if creating:
                if (
                    not manager
                    or data["revision"] != 0
                    or not data.get("title")
                    or not data.get("assignee_id")
                ):
                    raise PermissionDenied(
                        "Only the responsible person can create and assign a task."
                    )
                if PreparationTask.objects.filter(pk=identity).exists():
                    raise RentalConflict("Task identity is unavailable.")
                item = PreparationTask(id=identity, creator=request.user, **filters)
            elif data["revision"] != item.revision:
                raise RentalConflict(
                    "The task changed. Refresh before applying your edit."
                )
            elif not manager:
                current = payload(
                    item,
                    manager=False,
                    user=request.user,
                    members=members,
                    editable=editable,
                )
                if (
                    not current["can_update"]
                    or set(data)
                    - {"operation_id", "id", "revision", "status", "comment"}
                    or data.get("status") == "cancelled"
                ):
                    raise PermissionDenied(
                        "You can update or comment only on your current assigned task."
                    )
            if "assignee_id" in data:
                member = next(
                    (m for m in members if m.user.id == data["assignee_id"]), None
                )
                if member is None:
                    raise ValidationError("The assignee must be a current member.")
                item.assignee = member.user
                item.membership_period = getattr(member, "joined_revision", 0)
            for name in ("title", "description", "status", "due_at"):
                if name in data:
                    setattr(item, name, data[name])
            if not creating:
                item.revision += 1
            item.history = [
                *item.history,
                {
                    "actor_id": str(request.user.id),
                    "at": timezone.now().isoformat(),
                    "status": item.status,
                    "revision": item.revision,
                    "assignee_id": str(item.assignee.id),
                    "comment": data.get("comment", ""),
                    "action": "created" if creating else "updated",
                },
            ]
            if len(item.history) > 1000:
                raise ValidationError("This task has reached its history limit.")
            item.operations = {**item.operations, operation: digest}
            item.save()
            return Response(
                payload(
                    item,
                    manager=manager,
                    user=request.user,
                    members=members,
                    editable=editable,
                )
            )


# Stable callable import for integrations; URLs use the explicit class.
tasks = TasksView.as_view()
