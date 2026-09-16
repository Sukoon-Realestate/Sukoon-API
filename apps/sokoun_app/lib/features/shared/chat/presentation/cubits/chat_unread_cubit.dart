import 'dart:async';

import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';

import '../../data/chats_data.dart';
import '../../data/chat_realtime_service.dart';
import '../../data/chat_unread_refresh_bus.dart';
import '../../data/models/chat_socket_message.dart';
import '../../data/models/chat_unread_content.dart';

class ChatUnreadCubit extends AsyncCubit<ChatUnreadContent> {
  ChatUnreadCubit() : super(const ChatUnreadContent.initial());

  StreamSubscription<int>? _refreshSubscription;
  StreamSubscription<ChatSocketMessage>? _messageSubscription;

  Future<void> start() async {
    _refreshSubscription ??= ChatUnreadRefreshBus.stream.listen((removed) {
      removeConversationUnread(removed);
      if (removed == 0) unawaited(loadUnreadCount());
    });
    _messageSubscription ??= ChatRealtimeService.instance.messages.listen(
      _handleIncomingMessage,
    );
    if (!UserModel.isAuthenticated) return;
    await Future.wait([
      loadUnreadCount(),
      ChatRealtimeService.instance.connect(),
    ]);
  }

  Future<void> loadUnreadCount() async {
    if (isLoading || !await ChatData.hasAuthenticatedSession()) return;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<ChatUnreadContent>(
          api: ApiConstants.chatConversations,
          httpRequestType: HttpRequestType.get,
          queryParameters: const {'page': 1, 'page_size': 100},
          cacheKey: 'chat_unread_count',
          mapper: (json) => ChatUnreadContent.fromConversationsJson(
            json is Map<String, dynamic> ? json : const {},
          ),
          fromCacheJson: ChatUnreadContent.fromJson,
          toJson: (content) => content.toJson(),
        ),
      ),
      withInternetInterceptor: true,
    );
  }

  void removeConversationUnread(int unreadCount) {
    if (unreadCount <= 0) return;
    final int nextCount = data.count > unreadCount
        ? data.count - unreadCount
        : 0;
    updateData(data.copyWith(count: nextCount));
  }

  void _handleIncomingMessage(ChatSocketMessage message) {
    final String currentUserId = UserModel.currentUser?.id ?? '';
    if (message.sender.id == currentUserId ||
        message.conversationId ==
            ChatRealtimeService.instance.activeConversationId) {
      return;
    }
    updateData(data.copyWith(count: data.count + 1));
  }

  Future<void> onAppResumed() async {
    await Future.wait([
      loadUnreadCount(),
      ChatRealtimeService.instance.connect(),
    ]);
  }

  Future<void> onAppBackgrounded() => ChatRealtimeService.instance.disconnect();

  @override
  Future<void> close() async {
    await _refreshSubscription?.cancel();
    await _messageSubscription?.cancel();
    await ChatRealtimeService.instance.disconnect();
    return super.close();
  }
}
