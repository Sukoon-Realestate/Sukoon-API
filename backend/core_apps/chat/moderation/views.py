from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.chat.models import Conversation, ChatModerationCase
from core_apps.chat.services.direct_access import authorize
from .policy import projection, account_payload, attach_context
from .decisions import acknowledge, case_payload, appeal, review


class AcknowledgeSerializer(serializers.Serializer):
    policy_version = serializers.CharField(max_length=40)
    notice_id = serializers.UUIDField(required=False)


class AppealSerializer(serializers.Serializer):
    client_id = serializers.UUIDField()
    text = serializers.CharField(min_length=10, max_length=3000, trim_whitespace=True)


class ReviewSerializer(serializers.Serializer):
    client_id = serializers.UUIDField()
    expected_revision = serializers.IntegerField(min_value=1)
    action = serializers.ChoiceField(
        choices=["dismiss", "release", "keep_restricted", "ban"]
    )
    notes = serializers.CharField(min_length=10, max_length=3000, trim_whitespace=True)


class ChatPolicyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        conversation = get_object_or_404(Conversation, id=id)
        authorize(conversation, request.user)
        return Response(projection(conversation, request.user))

    def post(self, request, id):
        serializer = AcknowledgeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            acknowledge(
                request.user,
                get_object_or_404(Conversation, id=id),
                serializer.validated_data,
            )
        )


class RentalContextView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        conversation = get_object_or_404(Conversation, id=id)
        authorize(conversation, request.user)
        attach_context(conversation, request.user, request.data)
        return Response(projection(conversation, request.user))


class AccountPolicyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                **account_payload(request.user),
                "cases": [
                    case_payload(c)
                    for c in ChatModerationCase.objects.filter(
                        subject=request.user
                    ).order_by("-created_at")[:50]
                ],
            }
        )


class AppealView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        serializer = AppealSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(appeal(request.user, id, **serializer.validated_data))


class AdminCasesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from core_apps.admin_api.permissions import require_staff_actor

        require_staff_actor(request.user, {"system_owner", "main_admin"})
        from rest_framework.pagination import PageNumberPagination

        pager = PageNumberPagination()
        pager.page_size = 20
        cases = ChatModerationCase.objects.select_related(
            "subject", "conversation"
        ).order_by("resolved_at", "created_at")
        state = request.query_params.get("state")
        if state:
            cases = cases.filter(state=state)
        return pager.get_paginated_response(
            [case_payload(c) for c in pager.paginate_queryset(cases, request)]
        )


class AdminCaseView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        from core_apps.admin_api.permissions import require_staff_actor

        require_staff_actor(request.user, {"system_owner", "main_admin"})
        return Response(
            case_payload(get_object_or_404(ChatModerationCase, id=id), admin=True)
        )

    def post(self, request, id):
        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(review(request.user, id, **serializer.validated_data))


class AdminCaseMediaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, attachment_id):
        from django.http import FileResponse
        from rest_framework.exceptions import NotFound
        from core_apps.admin_api.permissions import require_staff_actor
        from core_apps.chat.models import ChatAttachment
        from core_apps.chat.services.group_media_storage import private_path
        from .sealed import unseal

        require_staff_actor(request.user, {"system_owner", "main_admin"})
        case = get_object_or_404(ChatModerationCase, id=id)
        evidence = unseal(case.evidence_ciphertext)
        ids = {
            m.get("source")
            for message in evidence.get("messages", [])
            for m in message.get("media", [])
        }
        if str(attachment_id) not in ids:
            raise NotFound()
        attachment = get_object_or_404(
            ChatAttachment,
            id=attachment_id,
            conversation=case.conversation,
            state="attached",
        )
        path = private_path(attachment.storage_key)
        if not path.is_file():
            try:
                from core_apps.chat.services.group_media_remote import materialize

                materialize(attachment.storage_key, path)
            except (ImportError, OSError, ValueError):
                raise NotFound()
        response = FileResponse(path.open("rb"), content_type=attachment.mime_type)
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        response["Content-Disposition"] = "inline"
        return response


class AdminPolicyStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.conf import settings
        from django.db.models import Count, Min
        from django.utils import timezone
        from datetime import timedelta
        from core_apps.admin_api.permissions import require_staff_actor
        from core_apps.chat.models import (
            ChatModerationInput,
            ChatModerationBatch,
            GeminiUsageReservation,
        )
        from .policy import mode

        require_staff_actor(request.user, {"system_owner", "main_admin"})
        now = timezone.now()
        budget = GeminiUsageReservation.objects.filter(day=timezone.localdate()).first()
        last = (
            ChatModerationBatch.objects.filter(state="complete")
            .order_by("-updated_at")
            .first()
        )
        failed = (
            ChatModerationBatch.objects.exclude(diagnostics={})
            .order_by("-updated_at")
            .first()
        )
        response = Response(
            {
                "mode": mode(),
                "model": settings.CHAT_MODERATION_MODEL,
                "private_inputs_approved": settings.CHAT_MODERATION_PRIVATE_INPUTS_APPROVED,
                "provider_configured": bool(settings.GEMINI_API_KEY),
                "daily_requests": budget.requests if budget else 0,
                "daily_limit": settings.CHAT_MODERATION_DAILY_REQUESTS,
                "pending": ChatModerationInput.objects.filter(
                    state="pending"
                ).aggregate(count=Count("pk"), oldest=Min("due_at")),
                "batches": list(
                    ChatModerationBatch.objects.values("state").annotate(
                        count=Count("pk")
                    )
                ),
                "last_success_at": last.updated_at if last else None,
                "last_failure_code": (
                    failed.diagnostics.get("code", "") if failed else ""
                ),
                "overdue_reviews": ChatModerationCase.objects.filter(
                    state__in=["pending_review", "review"],
                    resolved_at__isnull=True,
                    created_at__lt=now - timedelta(hours=48),
                ).count(),
            }
        )
        response["Cache-Control"] = "private, no-store"
        return response
