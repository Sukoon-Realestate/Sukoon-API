from django.urls import path
from core_apps.support.views.attachments import TicketAttachmentAPIView
from core_apps.support.views.recovery import TicketCreationReceiptAPIView
from core_apps.support.views.reply_recovery import TicketReplyReceiptAPIView
from core_apps.support.views.uploads import (
    AttachmentPolicyAPIView,
    AttachmentUploadAPIView,
    AttachmentUploadDetailAPIView,
)

from core_apps.support.views import (
    HelpCenterAPIView,
    TicketDetailAPIView,
    TicketListCreateAPIView,
    TicketReplyAPIView,
)

urlpatterns = [
    path(
        "attachment-policy/",
        AttachmentPolicyAPIView.as_view(),
        name="support-attachment-policy",
    ),
    path("uploads/", AttachmentUploadAPIView.as_view(), name="support-upload"),
    path(
        "uploads/<uuid:id>/",
        AttachmentUploadDetailAPIView.as_view(),
        name="support-upload-detail",
    ),
    path(
        "tickets/<str:id>/reply-receipt/",
        TicketReplyReceiptAPIView.as_view(),
        name="support-reply-receipt",
    ),
    path(
        "attachments/<uuid:id>/",
        TicketAttachmentAPIView.as_view(),
        name="support-attachment",
    ),
    path("help-center/", HelpCenterAPIView.as_view(), name="support-help-center"),
    path(
        "tickets/", TicketListCreateAPIView.as_view(), name="support-ticket-list-create"
    ),
    path(
        "tickets/creation-receipt/",
        TicketCreationReceiptAPIView.as_view(),
        name="support-ticket-creation-receipt",
    ),
    path(
        "tickets/<str:id>/", TicketDetailAPIView.as_view(), name="support-ticket-detail"
    ),
    path(
        "tickets/<str:id>/replies/",
        TicketReplyAPIView.as_view(),
        name="support-ticket-reply",
    ),
]
