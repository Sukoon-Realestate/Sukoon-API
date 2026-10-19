"""Reasoned operator access; decisions always use the reputation commands."""

import uuid

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from rest_framework.exceptions import APIException

from .models import CompanyMembership, ReviewAppeal, ReviewReport, ReviewSection
from .services.reputation import moderation, submission
from .services.reputation.policy import require_actor


class AccessReasonForm(forms.Form):
    access_reason = forms.CharField(
        max_length=1000, label="Reason for inspecting this content"
    )


class ReviewDecisionForm(forms.Form):
    request_key = forms.CharField(
        max_length=100, min_length=8, widget=forms.HiddenInput
    )
    expected_revision = forms.IntegerField(
        min_value=1,
        help_text="Use the displayed revision of the selected section, reply or case.",
    )
    action = forms.ChoiceField(choices=())
    reason = forms.CharField(
        max_length=1000, widget=forms.Textarea, label="Decision and evidence"
    )
    reply_id = forms.ChoiceField(required=False, choices=(), label="Content to decide")
    redacted_comment = forms.CharField(
        required=False, max_length=1500, widget=forms.Textarea
    )

    def __init__(self, *args, item, can_revoke=False, **kwargs):
        super().__init__(*args, **kwargs)
        if isinstance(item, ReviewSection):
            names = [
                "approve",
                "keep",
                "hold",
                "reject",
                "remove",
                "restore",
                "redact",
            ]
            if can_revoke:
                names.append("revoke_eligibility")
            self.fields["reply_id"].choices = [("", "Original section")]
            if hasattr(item, "reply"):
                self.fields["reply_id"].choices += [
                    (str(item.reply.id), "Subject's reply")
                ]
        else:
            names = (
                ["uphold", "restore", "remove", "reject", "hold"]
                if isinstance(item, ReviewAppeal)
                else ["resolve"]
            )
            self.fields.pop("reply_id")
            self.fields.pop("redacted_comment")
        self.fields["action"].choices = [
            (name, name.replace("_", " ").title()) for name in names
        ]


class ReputationOperatorAdmin(admin.ModelAdmin):
    actions = None
    list_display = ("id", "revision", "inspect_link")
    list_display_links = None
    ordering = ("-created_at", "id")
    list_per_page = 25

    def permitted(self, user):
        try:
            require_actor(user)
        except APIException:
            return False
        return user.has_perm("features.moderate_reviews")

    def has_module_permission(self, request):
        return self.permitted(request.user)

    def has_view_permission(self, request, obj=None):
        return self.permitted(request.user) and (
            obj is None or self.get_queryset(request).filter(pk=obj.pk).exists()
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        query = super().get_queryset(request)
        if not self.permitted(request.user):
            return query.none()
        prefix = (
            ""
            if self.model is ReviewSection
            else "section__" if self.model is ReviewReport else "decision__section__"
        )
        opportunity = prefix + "submission__opportunity__"
        case = opportunity + "case__"
        memberships = CompanyMembership.objects.filter(
            user=request.user, is_active=True
        ).values("company_id")
        # Conservatively exclude every source party and active company member,
        # including a party who is not the subject of this particular section.
        query = query.exclude(
            Q(**{opportunity + "reviewer": request.user})
            | Q(**{case + "party_a": request.user})
            | Q(**{case + "party_b": request.user})
            | Q(**{case + "company_id__in": memberships})
            | Q(**{case + "landlord_company_id__in": memberships})
        )
        if self.model is ReviewAppeal:
            query = query.exclude(
                Q(appellant=request.user) | Q(decision__actor=request.user)
            )
        if self.model is ReviewReport:
            query = query.exclude(reporter=request.user)
        return query

    @admin.display(description="Operator review")
    def inspect_link(self, item):
        return format_html(
            '<a href="{}">Inspect with a reason</a>',
            reverse(self.review_name, args=[item.id]),
        )

    @property
    def review_name(self):
        return "admin:reputation-" + self.model._meta.model_name + "-inspect"

    def get_urls(self):
        return [
            path(
                "<uuid:object_id>/inspect/",
                self.admin_site.admin_view(self.inspect),
                name=self.review_name.split(":", 1)[1],
            )
        ] + super().get_urls()

    def change_view(self, request, object_id, form_url="", extra_context=None):
        # Never expose model fields through the generic admin object page.
        if not self.has_view_permission(request):
            raise PermissionDenied
        item = get_object_or_404(self.get_queryset(request), pk=object_id)
        return redirect(reverse(self.review_name, args=[item.id]))

    def inspect(self, request, object_id):
        if not self.permitted(request.user):
            raise PermissionDenied
        item = get_object_or_404(self.get_queryset(request), id=object_id)
        section = (
            item
            if isinstance(item, ReviewSection)
            else (
                item.section
                if isinstance(item, ReviewReport)
                else item.decision.section
            )
        )
        try:
            moderation.require_moderator(request.user, section)
        except APIException as error:
            raise PermissionDenied from error
        access = AccessReasonForm(
            request.POST if request.method == "POST" else request.GET or None
        )
        decision = None
        disclosed = access.is_bound and access.is_valid()
        if disclosed:
            submission.audit(
                item,
                request.user,
                "operator_admin_read",
                access.cleaned_data["access_reason"],
            )
            decision = ReviewDecisionForm(
                request.POST if request.method == "POST" else None,
                item=item,
                can_revoke=request.user.has_perm("features.review_eligibility"),
                initial={
                    "request_key": str(uuid.uuid4()),
                    "expected_revision": item.revision,
                },
            )
            if request.method == "POST" and decision.is_valid():
                body = dict(decision.cleaned_data)
                action = body.pop("action")
                try:
                    if isinstance(item, ReviewSection):
                        body["action"] = action
                        if not body.get("reply_id"):
                            body.pop("reply_id", None)
                        moderation.moderate(request.user, item.id, body)
                    elif isinstance(item, ReviewAppeal):
                        body["outcome"] = action
                        moderation.resolve_appeal(request.user, item.id, body)
                    else:
                        moderation.resolve_report(request.user, item.id, body)
                    self.message_user(
                        request,
                        "Canonical decision recorded. Publication still depends on the original time and eligibility gates.",
                        messages.SUCCESS,
                    )
                    return redirect(request.path)
                except APIException as error:
                    decision.add_error(None, str(error.detail))
                    item.refresh_from_db()
                    section.refresh_from_db()
        response = TemplateResponse(
            request,
            "admin/reputation/inspect.html",
            {
                **self.admin_site.each_context(request),
                "title": "Reputation operator review",
                "opts": self.model._meta,
                "record_id": item.id,
                "access_form": access,
                "decision_form": decision,
                "item": item if disclosed else None,
                "section": section if disclosed else None,
                "reply": getattr(section, "reply", None) if disclosed else None,
                "is_section": isinstance(item, ReviewSection),
                "can_decide": isinstance(item, ReviewSection) or item.state == "open",
                "resolution": (
                    moderation.report_resolution(item)
                    if disclosed and isinstance(item, ReviewReport)
                    else getattr(item, "resolution", "") if disclosed else ""
                ),
            },
        )
        response["Cache-Control"] = "private, no-store"
        # Suppress cross-origin disclosure while retaining the same-origin
        # form Origin/Referer needed by Django's CSRF verification.
        response["Referrer-Policy"] = "same-origin"
        return response


@admin.register(ReviewSection)
class ReviewSectionAdmin(ReputationOperatorAdmin):
    list_display = ("id", "content_state", "revision", "inspect_link")
    list_filter = ("content_state", "subject_kind")


@admin.register(ReviewReport, ReviewAppeal)
class ReviewCaseAdmin(ReputationOperatorAdmin):
    list_display = ("id", "state", "revision", "inspect_link")
    list_filter = ("state",)
