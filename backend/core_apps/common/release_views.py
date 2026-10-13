import re
from django.db.models import Q
from django.utils import timezone
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from .content_models import ReleaseNote
from .renderers import GenericJsonRenderer


class ReleaseNotesAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    renderer_classes = [GenericJsonRenderer]

    def get(self, request):
        version = request.query_params.get("version", "")
        workspace = request.query_params.get("workspace", "tenant")
        if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?", version) or workspace not in {"tenant", "owner"}:
            raise ValidationError("Supply a supported version and workspace.")
        language = "ar" if getattr(request, "LANGUAGE_CODE", "en").startswith("ar") else "en"
        rows = ReleaseNote.objects.filter(version=version, active=True).filter(
            Q(workspace=workspace) | Q(workspace="both")).filter(
            Q(publish_at__isnull=True) | Q(publish_at__lte=timezone.now()))
        row = rows.filter(workspace=workspace).first() or rows.filter(workspace="both").first()
        response = Response({"version": version, "workspace": workspace,
            "revision": row.revision if row else 0,
            "items": [line.strip() for line in getattr(row, f"items_{language}").splitlines() if line.strip()] if row else []})
        response["Content-Language"] = language
        response["Cache-Control"] = "public, max-age=0, must-revalidate"
        response["Vary"] = "Accept-Language"
        return response
