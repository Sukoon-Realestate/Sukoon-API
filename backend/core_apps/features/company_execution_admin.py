"""Independent mandate verification with canonical revision and operation identity."""

import uuid
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from rest_framework.exceptions import APIException
from .billing_admin import FinancialHistoryAdmin
from .models import CompanyMandate
from .company_tenancy_serializers import ExecutionAuthorityBody
from .services.company.tenancy_contracts import verify_mandate
from .services.rental_lifecycle.common import command, staff_role


@admin.register(CompanyMandate)
class CompanyExecutionAdmin(FinancialHistoryAdmin):
    list_display = (
        "company",
        "membership",
        "kind",
        "state",
        "valid_until",
        "execution_verified_until",
        "review_link",
    )
    list_filter = ("kind", "state")
    search_fields = ("company__name", "membership__user__email", "evidence_reference")

    @admin.display(description="Execution authority")
    def review_link(self, item):
        return format_html(
            '<a href="{}">Inspect mandate</a>',
            reverse("admin:company-execution-review", args=[item.pk]),
        )

    def get_urls(self):
        return [
            path(
                "<int:object_id>/execution-review/",
                self.admin_site.admin_view(self.review),
                name="company-execution-review",
            )
        ] + super().get_urls()

    def review(self, request, object_id):
        from core_apps.common.recovery import require_scope, RecoveryRequired
        from django.http import HttpResponse

        try:
            require_scope("company_authority")
        except RecoveryRequired:
            return HttpResponse(
                "Company authority is awaiting recovery verification. No review was recorded.",
                status=503,
            )
        item = get_object_or_404(CompanyMandate, pk=object_id)
        roles = {"kyc_reviewer"} if item.kind == "sign" else {"financial_approver"}
        if not staff_role(request.user, roles):
            raise PermissionDenied
        if request.method == "POST":
            try:
                serializer = ExecutionAuthorityBody(
                    data={
                        "request_key": request.POST.get("request_key"),
                        "expected_revision": request.POST.get("revision"),
                        "evidence_reference": request.POST.get("evidence_reference"),
                        "verified_until": request.POST.get("verified_until"),
                        "reason": request.POST.get("reason"),
                    }
                )
                serializer.is_valid(raise_exception=True)
                data = serializer.validated_data

                def authorize():
                    from .services.rental_lifecycle.common import require_staff

                    require_staff(request.user, roles)
                    return item

                def execute(_):
                    updated = verify_mandate(request.user, item.id, data)
                    return (
                        updated,
                        {"id": str(updated.id), "revision": updated.revision},
                        200,
                    )

                command(
                    user=request.user,
                    operation="company.mandate.execution_review",
                    data=serializer.initial_data,
                    authorize=authorize,
                    execute=execute,
                )
                self.message_user(
                    request,
                    "Execution evidence recorded. Prepare fresh participant reviews using this mandate revision.",
                    messages.SUCCESS,
                )
                return redirect(request.path)
            except APIException as error:
                self.message_user(request, str(error.detail), messages.ERROR)
                item.refresh_from_db()
        response = TemplateResponse(
            request,
            "admin/company/execution_review.html",
            {
                **self.admin_site.each_context(request),
                "title": "Verify company execution authority",
                "item": item,
                "request_key": request.POST.get("request_key") or str(uuid.uuid4()),
            },
        )
        response["Cache-Control"] = "private, no-store"
        return response
