from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from rest_framework.exceptions import APIException

from .models import KYCSubmission, PlatformPreferenceAudit
from .permissions import IsIdentityReviewer
from .services.kyc_service import (
    approve_kyc_submission,
    get_kyc_detail,
    reject_kyc_submission,
)


@admin.register(KYCSubmission)
class KYCSubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "profile", "status", "created_at", "reviewer", "review_link")
    list_filter = ("status", "created_at", "superseded_at")
    search_fields = (
        "profile__user__email",
        "profile__user__first_name",
        "profile__user__last_name",
    )
    list_select_related = ("profile__user", "reviewer")
    readonly_fields = tuple(field.name for field in KYCSubmission._meta.fields) + (
        "review_link",
    )
    actions = None

    def has_module_permission(self, request):
        return self.has_view_permission(request)

    def has_view_permission(self, request, obj=None):
        return IsIdentityReviewer().has_permission(request, self)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="مراجعة التوثيق")
    def review_link(self, obj):
        return format_html(
            '<a href="{}">عرض المستندات ومراجعة الطلب</a>',
            reverse("admin:admin_api_kycsubmission_review", args=[obj.pk]),
        )

    def get_urls(self):
        return [
            path(
                "<int:object_id>/identity-media/<str:field>/",
                self.admin_site.admin_view(self.identity_media_view),
                name="admin_api_kycsubmission_media",
            ),
            path(
                "<int:object_id>/review/",
                self.admin_site.admin_view(self.review_view),
                name="admin_api_kycsubmission_review",
            ),
        ] + super().get_urls()

    def identity_media_view(self, request, object_id, field):
        from core_apps.profiles.identity_media import IDENTITY_FIELDS, identity_bytes

        if not self.has_view_permission(request):
            raise PermissionDenied
        if request.method != "GET":
            return HttpResponseNotAllowed(["GET"])
        if field not in IDENTITY_FIELDS:
            raise Http404
        submission = get_object_or_404(KYCSubmission, pk=object_id)
        try:
            return identity_bytes(submission.evidence_snapshot.get(field))
        except APIException as error:
            return HttpResponse(
                str(error.detail), status=error.status_code, content_type="text/plain"
            )

    def review_view(self, request, object_id):
        if not self.has_view_permission(request):
            raise PermissionDenied
        submission = get_object_or_404(KYCSubmission, pk=object_id)
        reason = request.POST.get("reason", "")
        if request.method == "POST":
            try:
                decision = request.POST.get("decision")
                if decision == "approve":
                    approve_kyc_submission(submission.id, reviewer=request.user)
                elif decision == "reject":
                    reject_kyc_submission(
                        submission.id, reviewer=request.user, reason=reason
                    )
                else:
                    self.message_user(
                        request, "اختر الموافقة أو الرفض.", messages.ERROR
                    )
                    return redirect(request.path)
            except APIException as error:
                self.message_user(request, str(error.detail), messages.ERROR)
            else:
                self.message_user(
                    request, "تم حفظ قرار مراجعة التوثيق بنجاح.", messages.SUCCESS
                )
                return redirect(request.path)
        detail = get_kyc_detail(submission.id)
        # Image tags authenticate with the Django admin session, rather than API tokens.
        for key, field in (
            ("idFaceUrl", "id_face"),
            ("idBackUrl", "id_back"),
            ("selfieUrl", "confirmation_selfi"),
        ):
            if detail[key]:
                detail[key] = reverse(
                    "admin:admin_api_kycsubmission_media", args=[submission.pk, field]
                )
        response = TemplateResponse(
            request,
            "admin/admin_api/kyc_review.html",
            {
                **self.admin_site.each_context(request),
                "opts": self.model._meta,
                "title": "مراجعة طلب توثيق الهوية",
                "submission": detail,
                "reason": reason,
                "can_review": detail["canReview"]
                and submission.profile.user_id != request.user.pk,
            },
        )
        response["Cache-Control"] = "private, no-store"
        return response


@admin.register(PlatformPreferenceAudit)
class PlatformPreferenceAuditAdmin(admin.ModelAdmin):
    list_display = ("revision", "actor", "created_at")
    readonly_fields = ("revision", "actor", "created_at", "before", "after")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
