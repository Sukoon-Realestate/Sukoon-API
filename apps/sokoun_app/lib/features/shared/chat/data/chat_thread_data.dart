import 'chat_data.dart';
import 'models/chat_content.dart';

/// Screen-scoped access to chat history and its cache identity.
final class ChatThreadData {
  ChatThreadData({required this.conversationId, ChatDataSource? dataSource})
    : _dataSource = dataSource ?? ChatData.source;

  final String conversationId;
  final ChatDataSource _dataSource;

  String? get messagesCacheKey => _dataSource.messagesCacheKey(conversationId);

  Future<List<ChatMessageContent>> loadInitialMessages() async {
    final (messages, _) = await _dataSource.getMessagesPage(
      conversationId: conversationId,
      page: 1,
    );
    return messages;
  }
}
