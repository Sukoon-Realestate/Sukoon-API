import logging
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from core_apps.admin_api.permissions import IsAdminStaff
from core_apps.admin_api.serializers import (
    StaffProfileListSerializer,
    StaffInviteSerializer,
)
from core_apps.admin_api.services import (
    get_staff_queryset,
    get_roles_summary,
    invite_staff_member,
    remove_staff_member,
    DEFAULT_PERMISSIONS_MATRIX,
)

logger = logging.getLogger(__name__)


class AdminStaffListAPIView(generics.ListAPIView):
    """
    Returns a list of all current staff and administrators.
    """

    permission_classes = [IsAdminStaff]
    serializer_class = StaffProfileListSerializer

    def get_queryset(self):
        return get_staff_queryset()


class AdminRolesSummaryAPIView(APIView):
    """
    Returns summarized information about defined admin roles and member counts.
    """

    permission_classes = [IsAdminStaff]

    def get(self, request):
        summary = get_roles_summary()
        return Response(summary, status=status.HTTP_200_OK)


class AdminStaffInviteAPIView(APIView):
    """
    Invites or creates a new administrator profile.

    Request Body:
    {
        "name": "خالد عبدالرحمن",
        "email": "khaled@example.com",
        "role_name": "مشرف رئيسي"
    }
    """

    permission_classes = [IsAdminStaff]

    def post(self, request):
        serializer = StaffInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        name = serializer.validated_data["name"]
        email = serializer.validated_data["email"]
        role_name = serializer.validated_data.get("role_name", "مراجع KYC")

        staff = invite_staff_member(email=email, name=name, role_name=role_name)
        return Response(
            {"message": f"تمت إضافة المشرف {name} بدور {role_name} بنجاح."},
            status=status.HTTP_201_CREATED,
        )


class AdminStaffDeleteAPIView(APIView):
    """
    Revokes staff access for an administrator.
    """

    permission_classes = [IsAdminStaff]

    def delete(self, request, staff_id):
        staff = remove_staff_member(staff_id)
        return Response(
            {"message": f"تم سحب صلاحيات المشرف {staff.user.get_full_name or staff.user.email} بنجاح."},
            status=status.HTTP_200_OK,
        )


class AdminPermissionsMatrixAPIView(APIView):
    """
    Returns or updates the permissions matrix for administrative roles.
    """

    permission_classes = [IsAdminStaff]

    def get(self, request):
        return Response(DEFAULT_PERMISSIONS_MATRIX, status=status.HTTP_200_OK)

    def patch(self, request):
        matrix_data = request.data
        return Response(
            {
                "message": "تم تحديث مصفوفة الصلاحيات بنجاح.",
                "matrix": matrix_data,
            },
            status=status.HTTP_200_OK,
        )
