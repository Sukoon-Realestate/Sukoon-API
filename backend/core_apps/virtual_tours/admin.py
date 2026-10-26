from django.contrib import admin, messages
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from . import sessions
from .models import (
    PropertyVirtualTour,
    TourRevision,
    TourReviewEvent,
    TourOperation,
    TourUploadSession,
)
from .services import review
from .errors import TourError


class ReadOnlyTourAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields]


@admin.register(PropertyVirtualTour)
class TourAdmin(ReadOnlyTourAdmin):
    list_display = (
        "id",
        "property",
        "building",
        "complex",
        "kind",
        "active_revision",
        "disabled",
        "deleted",
    )
    list_filter = ("kind", "disabled", "deleted")
    search_fields = ("property__title", "building__name", "complex__name")
    actions = ("disable_viewing",)

    @admin.action(description="Disable viewing immediately")
    def disable_viewing(self, request, queryset):
        queryset.update(disabled=True)


@admin.register(TourRevision)
class RevisionAdmin(ReadOnlyTourAdmin):
    list_display = (
        "id",
        "tour",
        "processing_state",
        "review_state",
        "stage",
        "updated_at",
        "review_link",
    )
    list_filter = ("processing_state", "review_state", "tour__kind")
    # Approval is deliberately an explicit, hash-bound API decision with a reason;
    # a bulk checkbox must not substitute for inspecting every scoped package.

    @admin.display(description="Review")
    def review_link(self, obj):
        return format_html(
            '<a href="{}">Inspect packages and review</a>',
            reverse("admin:virtual-tour-review", args=[obj.pk]),
        )

    def get_urls(self):
        return [
            path(
                "<int:object_id>/review/",
                self.admin_site.admin_view(self.review_console),
                name="virtual-tour-review",
            )
        ] + super().get_urls()

    def review_console(self, request, object_id):
        if not self.has_view_permission(request):
            from django.core.exceptions import PermissionDenied

            raise PermissionDenied
        revision = get_object_or_404(
            TourRevision.objects.select_related("tour__property"), pk=object_id
        )
        if request.method == "POST":
            try:
                if request.POST.get("action") == "preview":
                    data = sessions.create_session(
                        revision.tour,
                        request.user,
                        {
                            "preview": True,
                            "revision_id": str(revision.id),
                            "context": request.POST.get("context", "overview"),
                            "supported_manifest_versions": [1, 2],
                        },
                    )
                    response = JsonResponse(data)
                    response["Cache-Control"] = "private, no-store"
                    return response
                with transaction.atomic():
                    from .review_access import reviewer

                    reviewer(request.user, write=True, lock=True)
                    locked = (
                        TourRevision.objects.select_for_update(of=("self",))
                        .select_related("tour__property")
                        .get(pk=object_id)
                    )
                    review(
                        locked,
                        request.user,
                        {
                            "decision": request.POST.get("decision"),
                            "expected_source_hash": request.POST.get("source_hash"),
                            "reason": request.POST.get("reason", ""),
                        },
                    )
                self.message_user(request, "Review decision saved.", messages.SUCCESS)
                return redirect(request.path)
            except TourError as error:
                if request.POST.get("action") == "preview":
                    return JsonResponse(
                        {"error": str(error.detail)}, status=error.status_code
                    )
                self.message_user(request, str(error.detail), messages.ERROR)
        return TemplateResponse(
            request,
            "admin/virtual_tours/review.html",
            {
                **self.admin_site.each_context(request),
                "title": "Review property tour",
                "revision": revision,
                "variants": revision.variants.all(),
                "can_review": self.has_change_permission(request, revision)
                and revision.review_state == "pending",
            },
        )


@admin.register(TourReviewEvent)
class ReviewAdmin(ReadOnlyTourAdmin):
    list_display = ("revision", "reviewer", "decision", "created_at")


@admin.register(TourOperation)
class OperationAdmin(ReadOnlyTourAdmin):
    list_display = ("id", "user", "action", "status", "created_at")
    exclude = ("key",)


@admin.register(TourUploadSession)
class UploadAdmin(ReadOnlyTourAdmin):
    list_display = ("id", "revision", "role", "size", "state", "expires_at")
    exclude = ("parts",)
