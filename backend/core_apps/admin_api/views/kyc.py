import logging
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from core_apps.admin_api.permissions import IsIdentityReviewer
from core_apps.admin_api.serializers import (
    KYCSubmissionListSerializer,
    KYCRejectActionSerializer,
)
from core_apps.admin_api.services import (
    get_kyc_queue_queryset,
    get_kyc_metrics,
    get_kyc_detail,
    approve_kyc_submission,
    reject_kyc_submission,
)
from core_apps.admin_api.filters import KYCSubmissionFilter

logger = logging.getLogger(__name__)


@method_decorator(never_cache, name="dispatch")
class AdminKYCIdentityMediaAPIView(APIView):
    permission_classes = [IsIdentityReviewer]

    def get(self, request, submission_id, field):
        from django.shortcuts import get_object_or_404
        from rest_framework.exceptions import NotFound
        from core_apps.admin_api.models import KYCSubmission
        from core_apps.profiles.identity_media import IDENTITY_FIELDS, identity_bytes

        if field not in IDENTITY_FIELDS:
            raise NotFound()
        submission = get_object_or_404(KYCSubmission, id=submission_id)
        return identity_bytes(submission.evidence_snapshot.get(field))


class AdminKYCListAPIView(generics.ListAPIView):
    """
    Returns a paginated list of KYC verification submissions.
    """

    permission_classes = [IsIdentityReviewer]
    serializer_class = KYCSubmissionListSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = KYCSubmissionFilter

    def get_queryset(self):
        return get_kyc_queue_queryset()


class AdminKYCMetricsAPIView(APIView):
    """
    Returns KYC overview statistics (pending, accepted today, rejected today, reviewed today).
    """

    permission_classes = [IsIdentityReviewer]

    def get(self, request):
        metrics = get_kyc_metrics()
        return Response(metrics, status=status.HTTP_200_OK)


class AdminKYCDetailAPIView(APIView):
    """
    Returns complete detail for a specific KYC submission including document images.
    """

    permission_classes = [IsIdentityReviewer]

    def get(self, request, submission_id):
        detail = get_kyc_detail(submission_id)
        return Response(detail, status=status.HTTP_200_OK)


class AdminKYCApproveAPIView(APIView):
    """
    Approves a KYC submission and verifies the user.
    """

    permission_classes = [IsIdentityReviewer]

    def post(self, request, submission_id):
        submission = approve_kyc_submission(submission_id, reviewer=request.user)
        return Response(
            {
                "message": f"تمت الموافقة على توثيق المستخدم {submission.profile.user.email} بنجاح."
            },
            status=status.HTTP_200_OK,
        )


class AdminKYCRejectAPIView(APIView):
    """
    Rejects a KYC submission with a mandatory reason.

    Request Body:
    {
        "reason": "صورة الهوية الوطنية غير واضحة"
    }
    """

    permission_classes = [IsIdentityReviewer]

    def post(self, request, submission_id):
        serializer = KYCRejectActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data["reason"]

        submission = reject_kyc_submission(
            submission_id, reviewer=request.user, reason=reason
        )
        return Response(
            {
                "message": f"تم رفض طلب التوثيق للمستخدم {submission.profile.user.email}."
            },
            status=status.HTTP_200_OK,
        )
