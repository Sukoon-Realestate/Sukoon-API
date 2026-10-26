from django.core.paginator import Paginator, InvalidPage
from rest_framework.generics import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import NotFound, ValidationError, MethodNotAllowed
from rest_framework.response import Response
from rest_framework.views import APIView
from core_apps.admin_api.permissions import IsSystemOwner
from core_apps.admin_api.services import content_editor, content_registry as registry
from core_apps.common.content_models import ContentEditAudit
from core_apps.common.idempotency import request_key, response_headers


class ContentCommand(serializers.Serializer):
    expected_revision = serializers.JSONField()
    reason = serializers.CharField(max_length=500)
    values = serializers.DictField()

    def validate_expected_revision(self, value):
        if type(value) is int and 0 <= value <= 2147483647:
            return value
        if isinstance(value, str) and 1 <= len(value) <= 32:
            return value
        raise serializers.ValidationError("Supply the reviewed catalog revision.")


class AdminContentAPIView(APIView):
    permission_classes = [IsSystemOwner]

    def get(self, request, kind=None, identity=None):
        if kind is None:
            from core_apps.admin_api.permissions import require_staff_actor
            from core_apps.users.services.totp import require_sensitive_access
            from rest_framework.exceptions import PermissionDenied

            current = require_staff_actor(request.user, {"system_owner"})
            reason = ""
            try:
                require_sensitive_access(current)
                if current.sensitive_actions_frozen:
                    raise PermissionDenied()
            except PermissionDenied:
                reason = "التعديل متوقف. راجع أمان الحساب وطلب استعادة عامل التحقق."
            return Response(
                {
                    "catalogs": [registry.schema(key) for key in registry.REGISTRY],
                    "can_edit": not reason,
                    "blocking_reason": reason,
                },
                headers={"Cache-Control": "private, no-store"},
            )
        entry = registry.spec(kind)
        if identity:
            result = registry.projection(
                kind, get_object_or_404(entry.model, **{entry.identity_field: identity})
            )
            result["history"] = list(
                ContentEditAudit.objects.filter(kind=kind, object_id=identity)
                .order_by("-revision")
                .values("revision", "reason", "before", "after", "created_at")
            )
            return Response(result, headers={"Cache-Control": "private, no-store"})
        query = entry.model.objects.order_by("pk")
        search = request.query_params.get("search", "").strip()[:200]
        if search:
            from django.db.models import Q

            fields = [
                key
                for key in entry.fields
                if key
                in {
                    "name",
                    "name_ar",
                    "name_en",
                    "title_ar",
                    "title_en",
                    "question_ar",
                    "question_en",
                    "slug",
                    "label_ar",
                    "label_en",
                    "code",
                }
            ]
            predicate = Q()
            for field in fields:
                predicate |= Q(**{f"{field}__icontains": search})
            query = query.filter(predicate)
        try:
            page = Paginator(query, 25).page(request.query_params.get("page", 1))
        except (InvalidPage, ValueError):
            raise NotFound()
        return Response(
            {
                "results": [registry.projection(kind, row) for row in page],
                "total_pages": page.paginator.num_pages,
                "page": page.number,
                "per_page": page.paginator.per_page,
                "count": page.paginator.count,
            },
            headers={"Cache-Control": "private, no-store"},
        )

    def post(self, request, kind=None, identity=None):
        if kind is None:
            raise MethodNotAllowed("POST")
        body = ContentCommand(data=request.data)
        body.is_valid(raise_exception=True)
        if set(request.data) - set(body.fields):
            raise ValidationError("Unsupported content command fields.")
        result, code, replayed = content_editor.edit(
            request.user,
            kind,
            identity,
            body.validated_data,
            request_key(request),
            request.auth,
        )
        return Response(result, status=code, headers=response_headers(replayed))


class AdminContentReceiptAPIView(APIView):
    permission_classes = [IsSystemOwner]

    def post(self, request, kind, key):
        if not isinstance(request.data, dict) or set(request.data) - {"identity"}:
            raise ValidationError("Supply only the original content identity.")
        identity = request.data.get("identity")
        if identity is not None and (
            not isinstance(identity, str) or not 1 <= len(identity) <= 150
        ):
            raise ValidationError("Supply the original content identity.")
        return Response(
            content_editor.recover(
                request.user, kind, request.data.get("identity"), str(key), request.auth
            ),
            headers={"Cache-Control": "private, no-store"},
        )
