from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView
from core_apps.admin_api.permissions import IsSupportStaff
from core_apps.common.idempotency import request_key, response_headers
from core_apps.support.models import Ticket
from core_apps.support.services import operations
from core_apps.support.services.staff_replies import reply_as_staff
from core_apps.users.models import User


class SupportCommand(serializers.Serializer):
    expected_revision = serializers.IntegerField(min_value=1)
    action = serializers.ChoiceField(
        choices=["claim", "assign", "escalate", "note", "reply", "resolve"]
    )
    reason = serializers.CharField(max_length=1000)
    assignee_id = serializers.UUIDField(required=False)
    body = serializers.CharField(max_length=4000, required=False)
    acknowledge_resolution = serializers.BooleanField(required=False)


class AdminSupportDetailAPIView(APIView):
    permission_classes = [IsSupportStaff]

    def get(self, request, ticket_id):
        user = operations.actor(request.user)
        ticket = (
            Ticket.objects.select_related("user", "assigned_to")
            .filter(id=ticket_id)
            .first()
        )
        if not ticket:
            raise NotFound()
        return Response(
            operations.projection(ticket, user, detail=True),
            headers={"Cache-Control": "private, no-store"},
        )

    def post(self, request, ticket_id):
        body = SupportCommand(data=request.data)
        body.is_valid(raise_exception=True)
        data = body.validated_data
        key = request_key(request)
        if data["action"] in {"reply", "resolve"}:
            result, code, replayed = reply_as_staff(
                user=request.user,
                ticket_id=ticket_id,
                body=data.get("body", ""),
                expected_revision=data["expected_revision"],
                request_key=key,
                resolve_inquiry=data["action"] == "resolve",
                acknowledge_resolution=data.get("acknowledge_resolution", False),
            )
        else:
            result, code, replayed = operations.command(
                request.user, ticket_id, data, key
            )
        return Response(result, status=code, headers=response_headers(replayed))


class AdminSupportTeamAPIView(APIView):
    permission_classes = [IsSupportStaff]

    def get(self, request):
        operations.actor(request.user)
        team = (
            User.objects.filter(is_active=True)
            .filter(
                Q(is_superuser=True)
                | Q(
                    staff_profile__is_active=True,
                    staff_profile__role_name__in=operations.SUPPORT,
                )
            )
            .exclude(staff_profile__role_name="security_recovery_reviewer")
            .distinct()
        )
        return Response(
            {
                "results": [
                    {"id": str(user.id), "name": user.get_full_name or user.email}
                    for user in team
                ]
            }
        )


class AdminSupportReceiptAPIView(APIView):
    permission_classes = [IsSupportStaff]

    def get(self, request, ticket_id, key):
        return Response(
            operations.receipt(
                request.user, ticket_id, str(key), request.query_params.get("action")
            ),
            headers={"Cache-Control": "private, no-store"},
        )

    def post(self, request, ticket_id, key):
        return Response(
            operations.receipt(
                request.user,
                ticket_id,
                str(key),
                request.data.get("action"),
                close=True,
                auth_claims=request.auth,
            ),
            headers={"Cache-Control": "private, no-store"},
        )
