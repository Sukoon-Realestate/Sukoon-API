import uuid
from django.contrib import admin, messages
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from rest_framework.exceptions import APIException
from .billing_admin import FinancialHistoryAdmin
from .models import (
    RentalChargeback,
    ChargebackReplacementPayment,
    ChargebackRestoration,
)
from .chargeback_views import ChargebackApprovalBody
from .services.chargebacks import operations
from .services.chargebacks.projection import payload


class ChargebackHistoryAdmin(FinancialHistoryAdmin):
    lease_path = "chargeback__payment_attempt__invoice__lease__"

    def has_module_permission(self, request):
        return self.has_view_permission(request)

    def has_view_permission(self, request, obj=None):
        from .services.financial_authority import require_financial_actor

        try:
            if obj is not None:
                obj = getattr(obj, "chargeback", obj)
                operations.require_operator(
                    request.user, obj.payment_attempt.invoice.lease
                )
            else:
                require_financial_actor(
                    request.user,
                    {"financial_approver", "refund_operator", "psp_reconciliation"},
                    "chargeback.review",
                )
        except APIException:
            return False
        return True

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .exclude(**{self.lease_path + "owner": request.user})
            .exclude(**{self.lease_path + "tenant": request.user})
            .exclude(
                **{self.lease_path + "renter_company__memberships__user": request.user}
            )
        )


@admin.register(RentalChargeback)
class ChargebackAdmin(ChargebackHistoryAdmin):
    lease_path = "payment_attempt__invoice__lease__"
    list_display = [
        "payment_attempt",
        "provider",
        "provider_dispute_id",
        "outcome",
        "resolved_at",
        "review_link",
    ]

    @admin.display(description="Financial reconciliation")
    def review_link(self, item):
        return format_html(
            '<a href="{}">Inspect original evidence</a>',
            reverse("admin:chargeback-review", args=[item.pk]),
        )

    def get_urls(self):
        return [
            path(
                "<int:object_id>/review/",
                self.admin_site.admin_view(self.review),
                name="chargeback-review",
            )
        ] + super().get_urls()

    def review(self, request, object_id):
        item = get_object_or_404(RentalChargeback, pk=object_id)
        try:
            item = operations.detail(request.user, item.id)
        except APIException:
            from django.core.exceptions import PermissionDenied

            raise PermissionDenied
        try:
            if request.method == "POST":
                body = ChargebackApprovalBody(
                    data={
                        key: request.POST.get(key)
                        for key in [
                            "request_key",
                            "expected_revision",
                            "action",
                            "refund_id",
                            "reason",
                        ]
                    }
                )
                body.is_valid(raise_exception=True)
                operations.approve_refund(
                    request.user,
                    item.id,
                    body.validated_data,
                )
                self.message_user(
                    request,
                    "The exact excess refund was approved. Execute its original instruction through the protected "
                    "refund operation; approval is not returned money.",
                    messages.SUCCESS,
                )
                return redirect(request.path)
        except APIException as error:
            if request.method != "POST":
                from django.core.exceptions import PermissionDenied

                raise PermissionDenied
            self.message_user(request, str(error.detail), messages.ERROR)
            item.refresh_from_db()
        from .services.rental_lifecycle.common import staff_role

        current = operations.require_operator(
            request.user, item.payment_attempt.invoice.lease
        )
        response = TemplateResponse(
            request,
            "admin/features/chargeback_review.html",
            {
                **self.admin_site.each_context(request),
                "title": "Inspect chargeback evidence",
                "item": item,
                "projection": payload(item),
                "request_key": request.POST.get("request_key") or str(uuid.uuid4()),
                "can_approve": staff_role(
                    current, {"financial_approver", "refund_operator"}
                ),
            },
        )
        response["Cache-Control"] = "private, no-store"
        return response


admin.site.register(
    [ChargebackReplacementPayment, ChargebackRestoration], ChargebackHistoryAdmin
)
