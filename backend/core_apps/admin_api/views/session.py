from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core_apps.admin_api.models import StaffProfile
from core_apps.admin_api.permissions import require_staff_actor
from core_apps.admin_api.services.navigation import allowed_paths


class AdminSessionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = require_staff_actor(request.user, allow_recovery=True)
        profile = StaffProfile.objects.filter(user=user, is_active=True).first()
        role = (
            "security_recovery_reviewer"
            if profile and profile.role_name == "security_recovery_reviewer"
            else (
                "system_owner"
                if user.is_superuser
                else profile.role_name if profile else "staff"
            )
        )
        response = Response(
            {
                "id": str(user.id),
                "name": user.get_full_name or user.email,
                "email": user.email,
                "role": role,
                "canManageStaff": role == "system_owner",
                "allowedPaths": allowed_paths(request),
            }
        )
        response["Cache-Control"] = "private, no-store"
        return response
