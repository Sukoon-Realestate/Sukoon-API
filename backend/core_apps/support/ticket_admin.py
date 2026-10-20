"""Connected support inbox using the existing Django operations console."""

import uuid
from django import forms
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.utils.html import format_html, format_html_join
from rest_framework.exceptions import APIException
from .models import Ticket
from .services.staff_replies import can_service_tickets, reply_as_staff
from .services.payment_reports import readable_tickets, can_read_ticket


class TicketReplyForm(forms.ModelForm):
    service_action = forms.ChoiceField(
        choices=(("reply", "Reply"), ("resolve", "Resolve general inquiry")),
        initial="reply",
        required=False,
        help_text="Resolution is limited to unlinked general inquiries, not domain cases.",
    )
    acknowledge_resolution = forms.BooleanField(
        required=False,
        label="Only the general inquiry is resolved; no contract, payment, access or retention decision is made.",
    )
    reply = forms.CharField(
        widget=forms.Textarea,
        max_length=4000,
        required=False,
        help_text="Advice only. Refunds, access and possession require their domain workflow.",
    )
    expected_revision = forms.IntegerField(widget=forms.HiddenInput)
    request_key = forms.UUIDField(widget=forms.HiddenInput, initial=uuid.uuid4)

    class Meta:
        model = Ticket
        fields = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["expected_revision"].initial = self.instance.revision

    def clean(self):
        data = super().clean()
        if data.get("service_action") == "resolve":
            if not data.get("acknowledge_resolution"):
                self.add_error(
                    "acknowledge_resolution", "Acknowledge the limited effect."
                )
            if not data.get("reply", "").strip():
                self.add_error("reply", "Explain how the general inquiry was answered.")
        return data


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    form = TicketReplyForm
    list_display = ("reference", "workspace", "category", "status", "updated_at")
    list_filter = ("workspace", "category", "status")
    search_fields = ("reference",)
    readonly_fields = (
        "reference",
        "workspace",
        "category",
        "subject",
        "status",
        "revision",
        "rental_context",
        "conversation",
    )
    fields = (
        *readonly_fields,
        "service_action",
        "reply",
        "acknowledge_resolution",
        "expected_revision",
        "request_key",
    )
    actions = None

    def has_module_permission(self, request):
        return (
            can_service_tickets(request.user) or readable_tickets(request.user).exists()
        )

    def has_view_permission(self, request, obj=None):
        return (
            self.has_module_permission(request)
            if obj is None
            else can_read_ticket(request.user, obj)
        )

    def get_queryset(self, request):
        return readable_tickets(request.user)

    def get_fields(self, request, obj=None):
        return (
            self.fields if can_service_tickets(request.user) else self.readonly_fields
        )

    def has_change_permission(self, request, obj=None):
        return can_service_tickets(request.user) and (
            not obj or obj.user_id != request.user.pk
        )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Conversation (advice only)")
    def conversation(self, obj):
        return format_html_join(
            "",
            "<p><strong>{} · {}</strong><br>{}<br>{}</p>",
            (
                (
                    row.created_at,
                    row.sender,
                    row.body,
                    format_html_join(
                        " ",
                        '<a href="{}?workspace={}">{}</a>',
                        (
                            (attachment.file_url, obj.workspace, attachment.name)
                            for attachment in row.attachments.all()
                        ),
                    ),
                )
                for row in obj.messages.prefetch_related("attachments").order_by(
                    "created_at"
                )
            ),
        )

    def save_model(self, request, obj, form, change):
        if not form.cleaned_data.get("reply"):
            return
        # Validate at the command boundary again; the posted read-only ticket
        # fields never become authority for status or financial changes.
        try:
            reply_as_staff(
                user=request.user,
                ticket_id=obj.id,
                body=form.cleaned_data["reply"],
                expected_revision=form.cleaned_data["expected_revision"],
                request_key=str(form.cleaned_data["request_key"]),
                resolve_inquiry=form.cleaned_data.get("service_action") == "resolve",
                acknowledge_resolution=form.cleaned_data.get(
                    "acknowledge_resolution", False
                ),
            )
        except APIException as error:
            request.support_reply_failed = True
            self.message_user(request, str(error.detail), level=messages.ERROR)
        obj.refresh_from_db()

    def response_change(self, request, obj):
        if getattr(request, "support_reply_failed", False):
            return HttpResponseRedirect(request.path)
        return super().response_change(request, obj)
