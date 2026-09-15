import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';

import 'models/chat_content.dart';
import 'models/chat_page_response.dart';

abstract final class ChatData {
  static const int conversationsPageSize = 20;
  static const int messagesPageSize = 50;
  static const String conversationsCacheKey = 'chat_conversations';

  static String messagesCacheKey(String conversationId) =>
      'chat_messages_$conversationId';

  static Future<bool> hasAuthenticatedSession() =>
      injector<NetworkService>().hasSessionCookies();

  static Future<(List<ConversationContent>, PaginationData)>
  getConversationsPage({required int page}) async {
    final ChatPageResponse<ConversationContent> response =
        await getConversations(page: page);
    return (
      response.results,
      PaginationData(
        perPage: conversationsPageSize,
        totalPages: response.totalPages,
      ),
    );
  }

  static Future<ChatPageResponse<ConversationContent>> getConversations({
    required int page,
    int pageSize = conversationsPageSize,
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

  static Future<(List<ChatMessageContent>, PaginationData)> getMessagesPage({
    required String conversationId,
    required int page,
  }) async {
    final response = await injector<NetworkService>().callApi(
      NetworkRequest(
        method: RequestMethod.get,
        path: ApiConstants.chatMessages(conversationId),
        queryParameters: {'page': page, 'page_size': messagesPageSize},
      ),
      mapper: (json) => ChatPageResponse<ChatMessageContent>.fromJson(
        json is Map<String, dynamic> ? json : const {},
        itemFromJson: ChatMessageContent.fromJson,
        page: page,
        pageSize: messagesPageSize,
      ),
    );
    final ChatPageResponse<ChatMessageContent> pageResponse = response.data;
    return (
      pageResponse.results,
      PaginationData(
        perPage: messagesPageSize,
        totalPages: pageResponse.totalPages,
      ),
    );
  }

  static Future<ConversationContent> createConversation(String userId) async {
    final response = await injector<NetworkService>().callApi(
      NetworkRequest(
        method: RequestMethod.post,
        path: ApiConstants.createChatConversation,
        body: {'user_id': userId},
      ),
      mapper: (json) => ConversationContent.fromJson(
        json is Map<String, dynamic> ? json : const {},
      ),
    );
    return response.data;
  }

  static Future<ChatMessageContent> sendMessage({
    required String conversationId,
    required String content,
  }) async {
    final response = await injector<NetworkService>().callApi(
      NetworkRequest(
        method: RequestMethod.post,
        path: ApiConstants.createChatMessage(conversationId),
        body: {'content': content},
      ),
      mapper: (json) => ChatMessageContent.fromJson(
        json is Map<String, dynamic> ? json : const {},
      ),
    );
    return response.data;
  }

  static Future<ChatReadContent> markConversationAsRead(
    String conversationId,
  ) async {
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
