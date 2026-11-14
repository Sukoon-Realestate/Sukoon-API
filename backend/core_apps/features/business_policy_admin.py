"""Reviewable policy publication through the same service as the operator API."""

import uuid
from django import forms
from django.contrib import admin, messages
from django.views import View
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path
from rest_framework.exceptions import APIException
from .models import PolicyDecision
from .services import business_policies as policies
from .services.business_policy_catalog import CATALOG


class PublicationForm(forms.Form):
    code = forms.ChoiceField(
        choices=[(code, spec["title"][0]) for code, spec in CATALOG.items()]
    )
    version = forms.CharField(max_length=80)
    rules = forms.JSONField(widget=forms.Textarea(attrs={"rows": 12, "cols": 80}))
    reason = forms.CharField(
        max_length=4000, widget=forms.Textarea(attrs={"rows": 3, "cols": 80})
    )
    evidence_reference = forms.CharField(max_length=500)
    expected_head_revision = forms.IntegerField(widget=forms.HiddenInput)
    request_key = forms.UUIDField(widget=forms.HiddenInput)


@admin.register(PolicyDecision)
class BusinessPolicyAdmin(admin.ModelAdmin):
    list_display = ("code", "version", "status", "effective_at", "approver")
    list_filter = ("code", "status")
    search_fields = ("code", "version")
    change_list_template = "admin/features/policy_change_list.html"
    readonly_fields = tuple(field.name for field in PolicyDecision._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        return [
            path(
                "publish/",
                self.admin_site.admin_view(
                    PolicyPublicationView.as_view(model_admin=self)
                ),
                name="business-policy-publish",
            )
        ] + super().get_urls()


class PolicyPublicationView(View):
    """Native admin transport; retains legacy methods, session and CSRF wrapper."""

    model_admin = None

    def dispatch(self, request, *args, **kwargs):
        from django.core.exceptions import PermissionDenied

        try:
            policies.administrator(request.user)
        except APIException:
            raise PermissionDenied
        code = request.POST.get("code", request.GET.get("code", "D01"))
        if code not in CATALOG:
            code = "D01"
        template = next(row for row in policies.templates() if row["code"] == code)
        current = policies.current(code)
        form = PublicationForm(
            request.POST if request.method == "POST" else None,
            initial={
                "code": code,
                "rules": current.rules if current else template["rules"],
                "expected_head_revision": template["head_revision"],
                "request_key": uuid.uuid4(),
            },
        )
        if request.method == "POST" and form.is_valid():
            data = {
                **form.cleaned_data,
                "request_key": str(form.cleaned_data["request_key"]),
            }
            try:
                policies.publish(request.user, data)
            except APIException as error:
                form.add_error(None, str(error.detail))
            else:
                self.model_admin.message_user(
                    request,
                    "A new policy version was published. Accepted records retain their original snapshots.",
                    messages.SUCCESS,
                )
                return redirect("admin:features_policydecision_changelist")
        return TemplateResponse(
            request,
            "admin/features/policy_publish.html",
            {
                **self.model_admin.admin_site.each_context(request),
                "opts": self.model_admin.model._meta,
                "title": "Publish a prospective business policy",
                "form": form,
                "definition": template,
                "current": policies.public(current) if current else None,
                "policy_choices": [
                    (key, spec["title"][0]) for key, spec in CATALOG.items()
                ],
                "selected_code": code,
            },
        )
