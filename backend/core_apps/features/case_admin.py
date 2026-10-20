"""Operable case queue; all writes pass through the canonical domain command."""

import uuid
from django import forms
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from rest_framework.exceptions import APIException
from .models import RentalOperationalCase
from .company_models import PortfolioOffer
from .rental_lifecycle_serializers import CaseActionBody
from .services.rental_lifecycle.cases import (
    ROLES,
    case_queryset,
    independent_case_operator,
)
from .services.rental_lifecycle.common import staff_role
from .services.rental_lifecycle.case_commands import act_on_case
from . import company_service_form


class CaseCommandForm(forms.ModelForm, company_service_form.CompanyServiceFormFields):
    command_action = forms.ChoiceField(
        choices=[("", "Review only")]
        + [
            (v, v.replace("_", " "))
            for v in [
                "assign",
                "triage",
                "reply",
                "link_remedy",
                "resolve",
                "reopen",
                "prepare_company_change",
                "recommend_offers",
            ]
        ],
        required=False,
    )
    decision_reason = forms.CharField(
        widget=forms.Textarea, required=False, max_length=4000
    )
    assignee_id = forms.UUIDField(required=False)
    target_status = forms.ChoiceField(
        required=False,
        choices=[("", "Choose")]
        + [
            (v, v)
            for v in [
                "triaged",
                "waiting_for_company",
                "waiting_for_tenant",
                "waiting_for_owner",
                "waiting_for_provider",
                "under_review",
                "action_pending",
            ]
        ],
    )
    remedy_refund_id = forms.UUIDField(required=False)
    remedy_payout_id = forms.UUIDField(required=False)
    decision_code = forms.ChoiceField(
        required=False,
        choices=[("", "Choose")]
        + [
            (v, v)
            for v in [
                "corrected",
                "mutually_resolved",
                "refund_executed",
                "payout_executed",
                "no_action_required",
                "recommendations_delivered",
                "no_suitable_offer",
            ]
        ],
    )
    next_step = forms.CharField(required=False, max_length=500)
    housing_request_revision = forms.IntegerField(
        required=False, widget=forms.HiddenInput
    )
    recommended_offers = forms.ModelMultipleChoiceField(
        queryset=PortfolioOffer.objects.none(),
        required=False,
        help_text="Recommend at most three current offers; this does not reserve or approve them.",
    )
    expected_revision = forms.IntegerField(widget=forms.HiddenInput)
    request_key = forms.UUIDField(widget=forms.HiddenInput, initial=uuid.uuid4)

    class Meta:
        model = RentalOperationalCase
        fields = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["expected_revision"].initial = self.instance.revision
        company_service_form.configure(self)
        if self.instance.housing_request_id:
            from .company_models import PortfolioOffer
            from .services.company.viewing_handoff import filter_offers

            self.fields["housing_request_revision"].initial = (
                self.instance.housing_request.revision
            )
            self.fields["recommended_offers"].queryset = filter_offers(
                PortfolioOffer.objects.filter(status="published"),
                self.instance.housing_request,
            )
        else:
            self.fields["recommended_offers"].widget = forms.HiddenInput()

    def clean(self):
        data = super().clean()
        if data.get("command_action") and not data.get("decision_reason", "").strip():
            self.add_error(
                "decision_reason", "Explain this decision and the evidence reviewed."
            )
        self.company_proposal = company_service_form.proposal(self)
        return data


@admin.register(RentalOperationalCase)
class RentalCaseAdmin(admin.ModelAdmin):
    form = CaseCommandForm
    list_display = (
        "id",
        "kind",
        "team",
        "status",
        "assigned_to",
        "due_at",
        "next_action",
    )
    list_filter = ("team", "kind", "status")
    ordering = ("due_at", "id")
    search_fields = ("source_key",)
    readonly_fields = (
        "id",
        "kind",
        "team",
        "status",
        "revision",
        "lease",
        "housing_request",
        "reason",
        "sourcing_requirements",
        "payment_attempt",
        "assigned_to",
        "due_at",
        "escalated_at",
        "next_action",
        "baseline",
        "evidence",
        "refund",
        "payout",
        "resolution",
    )

    @admin.display(description="Current company housing requirements")
    def sourcing_requirements(self, obj):
        if not obj.housing_request_id:
            return "—"
        from django.utils.html import format_html
        from .services.company.sourcing import projection
        import json

        return format_html(
            "<pre>{}</pre>", json.dumps(projection(obj), indent=2, ensure_ascii=False)
        )

    fields = (
        *readonly_fields,
        "command_action",
        "decision_reason",
        "assignee_id",
        "target_status",
        "remedy_refund_id",
        "remedy_payout_id",
        "decision_code",
        "next_step",
        "expected_revision",
        "request_key",
        "housing_request_revision",
        "recommended_offers",
        *company_service_form.FIELDS,
    )
    actions = None

    def get_queryset(self, request):
        return case_queryset(request.user).select_related(
            "lease", "assigned_to", "refund", "payout"
        )

    def has_module_permission(self, request):
        return staff_role(request.user, ROLES)

    def has_view_permission(self, request, obj=None):
        return staff_role(request.user, ROLES) and (
            obj is None or case_queryset(request.user).filter(pk=obj.pk).exists()
        )

    def has_change_permission(self, request, obj=None):
        return self.has_view_permission(request, obj) and (
            obj is None or independent_case_operator(obj, request.user)
        )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        action = form.cleaned_data.get("command_action")
        if not action:
            return
        data = {
            "action": action,
            "reason": form.cleaned_data["decision_reason"],
            "request_key": str(form.cleaned_data["request_key"]),
            "expected_revision": form.cleaned_data["expected_revision"],
        }
        mapping = {
            "assignee_id": "assignee_id",
            "target_status": "status",
            "remedy_refund_id": "refund_id",
            "remedy_payout_id": "payout_id",
            "decision_code": "resolution_code",
            "next_step": "next_action",
        }
        data.update(
            {
                target: str(form.cleaned_data[source])
                for source, target in mapping.items()
                if form.cleaned_data.get(source)
            }
        )
        if action == "recommend_offers":
            data.update(
                housing_request_revision=form.cleaned_data.get(
                    "housing_request_revision"
                ),
                recommended_offer_ids=[
                    str(v.id) for v in form.cleaned_data["recommended_offers"]
                ],
            )
        if action == "prepare_company_change":
            data.update(
                tenancy_revision=form.cleaned_data["tenancy_revision"],
                company_proposal=form.company_proposal,
            )
        try:
            serializer = CaseActionBody(data=data)
            serializer.is_valid(raise_exception=True)
            act_on_case(request.user, obj.id, serializer.validated_data)
        except APIException as error:
            request.case_command_failed = True
            self.message_user(request, str(error.detail), level=messages.ERROR)
        obj.refresh_from_db()

    def response_change(self, request, obj):
        if getattr(request, "case_command_failed", False):
            return HttpResponseRedirect(request.path)
        return super().response_change(request, obj)
