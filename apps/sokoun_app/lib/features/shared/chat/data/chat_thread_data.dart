import 'package:melos_core/config/res/config_imports.dart';

import 'chats_data.dart';
import 'models/chat_content.dart';

abstract interface class ChatThreadDataSource {
  String? messagesCacheKey(String conversationId);

  Future<List<ChatMessageContent>> loadInitialMessages(String conversationId);
}

final class ChatThreadApiDataSource implements ChatThreadDataSource {
  const ChatThreadApiDataSource({ChatDataSource? dataSource})
    : _dataSource = dataSource;

  final ChatDataSource? _dataSource;

  ChatDataSource get _source => _dataSource ?? ChatData.source;

  @override
  String? messagesCacheKey(String conversationId) =>
      _source.messagesCacheKey(conversationId);

  @override
  Future<List<ChatMessageContent>> loadInitialMessages(
    String conversationId,
  ) async {
    final (List<ChatMessageContent> messages, _) = await _source
        .getMessagesPage(conversationId: conversationId, page: 1);
    return messages;
  }
}

/// Screen-scoped access to chat history and its cache identity.
final class ChatThreadData {
  ChatThreadData({
    required this.conversationId,
    ChatThreadDataSource? threadDataSource,
    ChatDataSource? dataSource,
  }) : _dataSource =
           threadDataSource ??
           (dataSource == null
               ? source
               : ChatThreadApiDataSource(dataSource: dataSource));

  final String conversationId;
  final ChatThreadDataSource _dataSource;

  static ChatThreadDataSource get source =>
      injector.isRegistered<ChatThreadDataSource>()
      ? injector<ChatThreadDataSource>()
      : const ChatThreadApiDataSource();

  String? get messagesCacheKey => _dataSource.messagesCacheKey(conversationId);

  Future<List<ChatMessageContent>> loadInitialMessages() =>
      _dataSource.loadInitialMessages(conversationId);
}
