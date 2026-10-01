import 'package:equatable/equatable.dart';

import '../../../../main_view/data/models/workspace_counts.dart';
import '../../../chat/data/models/chat_unread_content.dart';
import '../../../notifications/data/models/unread_notifications_content.dart';

class UnreadCounts extends Equatable {
  const UnreadCounts({
    required this.workspace,
    required this.chat,
    required this.notifications,
  });

  const UnreadCounts.initial()
    : workspace = const WorkspaceCounts.initial(),
      chat = const ChatUnreadContent.initial(),
      notifications = const UnreadNotificationsContent.initial();

  factory UnreadCounts.fromJson(Map<String, dynamic> json) => UnreadCounts(
    workspace: WorkspaceCounts.fromJson(json),
    chat: ChatUnreadContent.fromJson(json),
    notifications: UnreadNotificationsContent.fromJson(json),
  );

  final WorkspaceCounts workspace;
  final ChatUnreadContent chat;
  final UnreadNotificationsContent notifications;

  Map<String, dynamic> toJson() => {
    ...workspace.toJson(),
    'unread_chat_messages_count': chat.count,
    'unread_notifications_count': notifications.count,
  };

  UnreadCounts copyWith({
    WorkspaceCounts? workspace,
    ChatUnreadContent? chat,
    UnreadNotificationsContent? notifications,
  }) => UnreadCounts(
    workspace: workspace ?? this.workspace,
    chat: chat ?? this.chat,
    notifications: notifications ?? this.notifications,
  );

  @override
  List<Object?> get props => [workspace, chat, notifications];
}
