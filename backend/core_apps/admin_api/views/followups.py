"""Current authorized work queues, not fabricated notifications/read receipts."""

from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core_apps.admin_api.models import KYCSubmission, StaffProfile
from core_apps.admin_api.permissions import (
    IsIdentityReviewer,
    IsPropertyReviewer,
    require_staff_actor,
)
from core_apps.properties.models import Property
from core_apps.support.models import Ticket
from core_apps.support.services.operations import SUPPORT, SUPERVISORS
from core_apps.users.models import AccountClosureRequest
from core_apps.users.services.account_closure import REVIEW_ROLES


class AdminFollowupsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        actor = require_staff_actor(request.user, allow_recovery=True)
        profile = StaffProfile.objects.filter(user=actor).first()
        rows = []

        def allowed(roles):
            try:
                require_staff_actor(actor, roles)
                return True
            except PermissionDenied:
                return False

        def add(identity, title, query, href):
            rows.append(
                {"id": identity, "title": title, "count": query.count(), "href": href}
            )

        # Even a superuser with this designated profile stays recovery-only.
        limited = profile and profile.role_name == "security_recovery_reviewer"
        if not limited:
            if IsIdentityReviewer().has_permission(request, self):
                add(
                    "kyc",
                    "طلبات توثيق الهوية المعلقة",
                    KYCSubmission.objects.filter(
                        status="pending",
                        superseded_at__isnull=True,
                    ).exclude(profile__user=actor),
                    "/admin/kyc",
                )
            if allowed(IsPropertyReviewer.roles):
                add(
                    "properties",
                    "عقارات قيد المراجعة",
                    Property.objects.filter(
                        status=Property.Status.UNDER_REVIEW,
                    ).exclude(owner=actor),
                    "/admin/properties/review",
                )
            if allowed(SUPPORT):
                tickets = Ticket.objects.filter(
                    status__in=[Ticket.Status.OPEN, Ticket.Status.IN_PROGRESS]
                ).exclude(user=actor)
                assigned = tickets.filter(
                    Q(assigned_to=actor) | Q(assigned_to__isnull=True)
                )
                if not allowed(SUPERVISORS):
                    assigned = assigned.filter(escalated=False)
                add(
                    "support",
                    "تذاكر الدعم المسندة إليك أو غير المسندة",
                    assigned,
                    "/admin/support",
                )
                if allowed(SUPERVISORS):
                    add(
                        "escalations",
                        "تذاكر التصعيد المفتوحة للمشرفين",
                        tickets.filter(escalated=True),
                        "/admin/support",
                    )
            if allowed(REVIEW_ROLES):
                add(
                    "account_closure",
                    "طلبات حذف الحساب قيد المتابعة",
                    AccountClosureRequest.objects.filter(active=True).exclude(
                        user=actor
                    ),
                    "/admin/account-closure",
                )

        return Response(
            {"results": rows, "measured_at": timezone.now().isoformat()},
            headers={"Cache-Control": "private, no-store"},
        )
