from django.urls import path
from .views.notification_actions import notification_action
from .views.forwarding import forward_destinations, forward
from .views.mentions import unread_mentions, mention_seen
from .views.interactions import MessageReactionAPIView, ConversationMembersAPIView
from .views.group_attachments import (
    GroupAttachmentDetailAPIView,
    GroupAttachmentUploadAPIView,
)
from .views.group_commands import GroupMessageDeleteAPIView
from .views.preferences import ConversationPreferencesAPIView
from .views.group_history import (
    DirectChatSummaryAPIView,
    GroupEventsAPIView,
    GroupMessageContextAPIView,
    GroupMessageLookupAPIView,
)

from .views import productivity

urlpatterns = [
    path("notification-actions/", notification_action, name="chat-notification-action"),
    path("quick-replies/", productivity.saved_replies),
    path("quick-replies/<uuid:id>/", productivity.saved_reply),
    path("conversations/<uuid:id>/starred/", productivity.starred_messages),
    path("conversations/<uuid:id>/forward/", productivity.forward_messages),
    path(
        "conversations/<uuid:id>/messages/<uuid:message_id>/star/",
        productivity.message_star,
    ),
    path(
        "conversations/<uuid:id>/messages/<uuid:message_id>/pin/",
        productivity.message_pin,
    ),
    path(
        "conversations/<uuid:id>/messages/<uuid:message_id>/readers/",
        productivity.message_readers,
    ),
    path(
        "conversations/<uuid:id>/messages/<uuid:message_id>/poll/vote/",
        productivity.poll_vote,
    ),
    path(
        "conversations/<uuid:id>/messages/<uuid:message_id>/poll/close/",
        productivity.poll_close,
    ),
    path(
        "conversations/<uuid:id>/messages/<uuid:message_id>/forward-destinations/",
        forward_destinations,
    ),
    path("conversations/<uuid:id>/messages/<uuid:message_id>/forward/", forward),
    path("conversations/<uuid:id>/mentions/", unread_mentions),
    path("conversations/<uuid:id>/mentions/<uuid:message_id>/seen/", mention_seen),
    path("conversations/<uuid:id>/members/", ConversationMembersAPIView.as_view()),
    path(
        "conversations/<uuid:id>/messages/<uuid:message_id>/reaction/",
        MessageReactionAPIView.as_view(),
    ),
    path("conversations/<uuid:id>/chat/", DirectChatSummaryAPIView.as_view()),
    path(
        "conversations/<uuid:id>/messages/by-client-id/<uuid:client_id>/",
        GroupMessageLookupAPIView.as_view(),
    ),
    path(
        "conversations/<uuid:id>/messages/<uuid:message_id>/context/",
        GroupMessageContextAPIView.as_view(),
    ),
    path(
        "conversations/<uuid:id>/messages/<uuid:message_id>/",
        GroupMessageDeleteAPIView.as_view(),
    ),
    path(
        "conversations/<uuid:id>/preferences/", ConversationPreferencesAPIView.as_view()
    ),
    path("conversations/<uuid:id>/events/", GroupEventsAPIView.as_view()),
    path(
        "conversations/<uuid:id>/attachments/", GroupAttachmentUploadAPIView.as_view()
    ),
    path(
        "conversations/<uuid:id>/attachments/by-client-id/<uuid:client_id>/",
        GroupAttachmentDetailAPIView.as_view(),
    ),
    path(
        "conversations/<uuid:id>/attachments/<uuid:attachment_id>/",
        GroupAttachmentDetailAPIView.as_view(),
    ),
    path(
        "conversations/<uuid:id>/attachments/<uuid:attachment_id>/<str:content>/",
        GroupAttachmentDetailAPIView.as_view(),
    ),
]
