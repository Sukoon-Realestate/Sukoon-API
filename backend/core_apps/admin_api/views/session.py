from rest_framework.views import APIView
from rest_framework.response import Response
from core_apps.admin_api.models import StaffProfile
from core_apps.admin_api.permissions import IsAdminStaff, require_staff_actor


class AdminSessionAPIView(APIView):
    permission_classes = [IsAdminStaff]

    def get(self, request):
        user = require_staff_actor(request.user)
        profile = StaffProfile.objects.filter(user=user, is_active=True).first()
        role = (
            "system_owner"
            if user.is_superuser
            else profile.role_name if profile else "staff"
        )
        return Response(
            {
                "id": str(user.id),
                "name": user.get_full_name or user.email,
                "email": user.email,
                "role": role,
                "canManageStaff": role == "system_owner",
            }
        )
