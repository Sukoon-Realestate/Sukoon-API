from django.urls import path
from .views.notification_actions import NotificationActionAPIView
from .views.forwarding import ForwardDestinationsAPIView, ForwardAPIView
from .views.mentions import UnreadMentionsAPIView, MentionSeenAPIView
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
    path(
        "notification-actions/",
        NotificationActionAPIView.as_view(),
        name="chat-notification-action",
    ),
    path("quick-replies/", productivity.SavedRepliesAPIView.as_view()),
    path("quick-replies/<uuid:id>/", productivity.SavedReplyAPIView.as_view()),
    path(
        "conversations/<uuid:id>/starred/",
        productivity.StarredMessagesAPIView.as_view(),
    ),
    path(
        "conversations/<uuid:id>/forward/",
        productivity.ForwardMessagesAPIView.as_view(),
    ),
    path(
        "conversations/<uuid:id>/messages/<uuid:message_id>/star/",
        productivity.MessageStarAPIView.as_view(),
    ),
    path(
        "conversations/<uuid:id>/messages/<uuid:message_id>/pin/",
        productivity.MessagePinAPIView.as_view(),
    ),
    path(
        "conversations/<uuid:id>/messages/<uuid:message_id>/readers/",
        productivity.MessageReadersAPIView.as_view(),
    ),
    path(
        "conversations/<uuid:id>/messages/<uuid:message_id>/poll/vote/",
        productivity.PollVoteAPIView.as_view(),
    ),
    path(
        "conversations/<uuid:id>/messages/<uuid:message_id>/poll/close/",
        productivity.PollCloseAPIView.as_view(),
    ),
    path(
        "conversations/<uuid:id>/messages/<uuid:message_id>/forward-destinations/",
        ForwardDestinationsAPIView.as_view(),
    ),
    path(
        "conversations/<uuid:id>/messages/<uuid:message_id>/forward/",
        ForwardAPIView.as_view(),
    ),
    path("conversations/<uuid:id>/mentions/", UnreadMentionsAPIView.as_view()),
    path(
        "conversations/<uuid:id>/mentions/<uuid:message_id>/seen/",
        MentionSeenAPIView.as_view(),
    ),
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
