from django.urls import path
from core_apps.support.views.attachments import TicketAttachmentAPIView
from core_apps.support.views.recovery import TicketCreationReceiptAPIView

from core_apps.support.views import (
    HelpCenterAPIView,
    TicketDetailAPIView,
    TicketListCreateAPIView,
    TicketReplyAPIView,
)

urlpatterns = [
    path("attachments/<uuid:id>/", TicketAttachmentAPIView.as_view(), name="support-attachment"),
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
