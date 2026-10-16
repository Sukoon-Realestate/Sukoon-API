"""Private inspection and independent review through the same audited service."""

import uuid
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from rest_framework.exceptions import APIException
from core_apps.properties.models import ResidentialMedia, PortfolioChangeSet
from core_apps.virtual_tours import storage
from .billing_admin import FinancialHistoryAdmin
from .services.company import portfolio_media
from .services.rental_lifecycle.common import staff_role
from .portfolio_serializers import MediaReviewBody


def require_reviewer(user):
    # Django admin is not a DRF endpoint; use its native permission exception.
    if not staff_role(user, {"property_reviewer"}):
        raise PermissionDenied


@admin.register(PortfolioChangeSet)
class ChangeInspection(FinancialHistoryAdmin):
    list_display = ("id", "owner", "operation", "applied_at", "revision")
    list_filter = ("operation",)


@admin.register(ResidentialMedia)
class MediaInspection(FinancialHistoryAdmin):
    list_display = ("id", "owner", "purpose", "state", "review_status", "review_link")
    list_filter = ("purpose", "state", "review_status")
    search_fields = ("building__name", "complex__name", "owner__email")

    @admin.display(description="Review")
    def review_link(self, obj):
        return format_html(
            '<a href="{}">Inspect and review</a>',
            reverse("admin:portfolio-media-review", args=[obj.pk]),
        )

    def get_urls(self):
        return [
            path(
                "<int:object_id>/review/",
                self.admin_site.admin_view(self.review_console),
                name="portfolio-media-review",
            ),
            path(
                "<int:object_id>/image/",
                self.admin_site.admin_view(self.image),
                name="portfolio-media-image",
            ),
        ] + super().get_urls()

    def image(self, request, object_id):
        require_reviewer(request.user)
        item = get_object_or_404(
            ResidentialMedia.objects.exclude(blob=""), pk=object_id
        )
        response = FileResponse(
            storage.read_path(item.blob).open("rb"), content_type="image/png"
        )
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response

    def review_console(self, request, object_id):
        require_reviewer(request.user)
        item = get_object_or_404(ResidentialMedia, pk=object_id)
        if request.method == "POST":
            try:
                body = MediaReviewBody(
                    data={
                        "request_key": request.POST.get("request_key"),
                        "expected_revision": request.POST.get("revision"),
                        "status": request.POST.get("status"),
                        "reason": request.POST.get("reason"),
                    }
                )
                body.is_valid(raise_exception=True)
                portfolio_media.review(request.user, item.id, body.validated_data)
                self.message_user(
                    request,
                    "Review saved. Asset authority remains a separate scoped decision.",
                    messages.SUCCESS,
                )
                return redirect(request.path)
            except APIException as error:
                self.message_user(request, str(error.detail), messages.ERROR)
        response = TemplateResponse(
            request,
            "admin/portfolio/media_review.html",
            {
                **self.admin_site.each_context(request),
                "title": "Review residential media",
                "item": item,
                "request_key": str(uuid.uuid4()),
                "image_url": reverse("admin:portfolio-media-image", args=[item.pk]),
            },
        )
        response["Cache-Control"] = "private, no-store"
        return response
