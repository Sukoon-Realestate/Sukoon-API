import 'package:equatable/equatable.dart';

import 'chat_content.dart';
import 'chat_page_response.dart';

class ChatUnreadContent extends Equatable {
  const ChatUnreadContent({required this.count});

  const ChatUnreadContent.initial() : count = 0;

  factory ChatUnreadContent.fromJson(Map<String, dynamic> json) {
    return ChatUnreadContent(
      count:
          ((json['unread_chat_messages_count'] ?? json['count']) as num?)
              ?.toInt() ??
          0,
    );
  }

  factory ChatUnreadContent.fromConversationsJson(Map<String, dynamic> json) {
    final ChatPageResponse<ConversationContent> response =
        ChatPageResponse<ConversationContent>.fromJson(
          json,
          itemFromJson: ConversationContent.fromJson,
          page: 1,
          pageSize: 100,
        );
    return ChatUnreadContent(
      count: response.results.fold<int>(
        0,
        (total, conversation) => total + conversation.unreadCount,
      ),
    );
  }

  final int count;

  ChatUnreadContent copyWith({int? count}) {
    return ChatUnreadContent(count: count ?? this.count);
  }

  Map<String, dynamic> toJson() => {'count': count};

  @override
  List<Object?> get props => [count];
}
