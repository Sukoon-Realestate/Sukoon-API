import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';

import 'models/chat_content.dart';
import 'models/chat_page_response.dart';
import 'models/chat_read_content.dart';
import 'models/message_params_model.dart';
import 'models/request_model.dart';

abstract interface class ChatDataSource {
  String? get conversationsCacheKey;

  String? messagesCacheKey(String conversationId);

  Future<(List<ConversationContent>, PaginationData)> getConversationsPage({
    required int page,
  });

  Future<ChatPageResponse<ConversationContent>> getConversations({
    required int page,
    int pageSize = ChatData.conversationsPageSize,
  });

  Future<(List<ChatMessageContent>, PaginationData)> getMessagesPage({
    required String conversationId,
    required int page,
  });

  Future<ConversationContent> createConversation(String userId);

  Future<ChatMessageContent> sendMessage({
    required String conversationId,
    required String content,
  });

  Future<ChatReadContent> markConversationAsRead(String conversationId);
}

final class ChatApiDataSource implements ChatDataSource {
  const ChatApiDataSource();

  @override
  String get conversationsCacheKey => ChatData.conversationsCacheKey;

  @override
  String messagesCacheKey(String conversationId) =>
      ChatData.messagesCacheKey(conversationId);

  @override
  Future<(List<ConversationContent>, PaginationData)> getConversationsPage({
    required int page,
  }) async {
    final ChatPageResponse<ConversationContent> response =
        await getConversations(page: page);
    return (
      response.results,
      PaginationData(
        perPage: ChatData.conversationsPageSize,
        totalPages: response.totalPages,
      ),
    );
  }

  @override
  Future<ChatPageResponse<ConversationContent>> getConversations({
    required int page,
    int pageSize = ChatData.conversationsPageSize,
  }) async {
    final response = await injector<NetworkService>().callApi(
      NetworkRequest(
        method: RequestMethod.get,
        path: ApiConstants.chatConversations,
        queryParameters: {'page': page, 'page_size': pageSize},
      ),
      mapper: (json) => ChatPageResponse<ConversationContent>.fromJson(
        json is Map<String, dynamic> ? json : const {},
        itemFromJson: ConversationContent.fromJson,
        page: page,
        pageSize: pageSize,
      ),
    );
    return response.data;
  }

  @override
  Future<(List<ChatMessageContent>, PaginationData)> getMessagesPage({
    required String conversationId,
    required int page,
  }) async {
    final response = await injector<NetworkService>().callApi(
      NetworkRequest(
        method: RequestMethod.get,
        path: ApiConstants.chatMessages(conversationId),
        queryParameters: {'page': page, 'page_size': ChatData.messagesPageSize},
      ),
      mapper: (json) => ChatPageResponse<ChatMessageContent>.fromJson(
        json is Map<String, dynamic> ? json : const {},
        itemFromJson: ChatMessageContent.fromJson,
        page: page,
        pageSize: ChatData.messagesPageSize,
      ),
    );
    final ChatPageResponse<ChatMessageContent> pageResponse = response.data;
    return (
      pageResponse.results,
      PaginationData(
        perPage: ChatData.messagesPageSize,
        totalPages: pageResponse.totalPages,
      ),
    );
  }

  @override
  Future<ConversationContent> createConversation(String userId) async {
    final response = await injector<NetworkService>().callApi(
      NetworkRequest(
        method: RequestMethod.post,
        path: ApiConstants.createChatConversation,
        body: RequestModel(userId: userId).toJson(),
      ),
      mapper: (json) => ConversationContent.fromJson(
        json is Map<String, dynamic> ? json : const {},
      ),
    );
    return response.data;
  }

  @override
  Future<ChatMessageContent> sendMessage({
    required String conversationId,
    required String content,
  }) async {
    final response = await injector<NetworkService>().callApi(
      NetworkRequest(
        method: RequestMethod.post,
        path: ApiConstants.createChatMessage(conversationId),
        body: MessageParamsModel(
          conversationId: conversationId,
          content: content,
        ).toRestJson(),
      ),
      mapper: (json) => ChatMessageContent.fromJson(
        json is Map<String, dynamic> ? json : const {},
      ),
    );
    return response.data;
  }

  @override
  Future<ChatReadContent> markConversationAsRead(String conversationId) async {
    final response = await injector<NetworkService>().callApi(
      NetworkRequest(
        method: RequestMethod.post,
        path: ApiConstants.markChatConversationRead(conversationId),
      ),
      mapper: (json) => ChatReadContent.fromJson(
        json is Map<String, dynamic> ? json : const {},
      ),
    );
    return response.data;
  }
}

abstract final class ChatData {
  static const int conversationsPageSize = 20;
  static const int messagesPageSize = 50;
  static const String conversationsCacheKey = 'chat_conversations';

  static ChatDataSource get source => injector.isRegistered<ChatDataSource>()
      ? injector<ChatDataSource>()
      : const ChatApiDataSource();

  static String messagesCacheKey(String conversationId) =>
      'chat_messages_$conversationId';

  static Future<bool> hasAuthenticatedSession() =>
      injector<NetworkService>().hasSessionCookies();

  static Future<(List<ConversationContent>, PaginationData)>
  getConversationsPage({required int page}) =>
      source.getConversationsPage(page: page);

  static Future<ChatPageResponse<ConversationContent>> getConversations({
    required int page,
    int pageSize = conversationsPageSize,
  }) => source.getConversations(page: page, pageSize: pageSize);

  static Future<(List<ChatMessageContent>, PaginationData)> getMessagesPage({
    required String conversationId,
    required int page,
  }) => source.getMessagesPage(conversationId: conversationId, page: page);

  static Future<ConversationContent> createConversation(String userId) =>
      source.createConversation(userId);

  static Future<ChatMessageContent> sendMessage({
    required String conversationId,
    required String content,
  }) => source.sendMessage(conversationId: conversationId, content: content);

  static Future<ChatReadContent> markConversationAsRead(
    String conversationId,
  ) => source.markConversationAsRead(conversationId);
}
