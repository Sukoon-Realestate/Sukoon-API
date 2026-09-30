import 'dart:async';
import 'dart:math' show max;

import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/network/account_session.dart';

import '../../../notifications/data/enums/app_notification_kind.dart';
import '../../../notifications/data/foreground_notification_bus.dart';
import '../../../notifications/data/models/app_notification_content.dart';
import '../../data/chats_data.dart';
import '../../data/chat_realtime_service.dart';
import '../../data/chat_unread_refresh_bus.dart';
import '../../data/models/chat_socket_message.dart';
import '../../data/models/chat_unread_content.dart';

class ChatUnreadCubit extends AsyncCubit<ChatUnreadContent> {
  ChatUnreadCubit({ChatRealtimeGateway? realtimeService})
    : _realtime = realtimeService ?? ChatRealtimeService.instance,
      super(const ChatUnreadContent.initial());

  final ChatRealtimeGateway _realtime;
  StreamSubscription<int>? _refreshSubscription;
  int _sessionGeneration = AccountSession.generation;
  StreamSubscription<ChatSocketMessage>? _messageSubscription;
  StreamSubscription<AppNotificationContent>? _notificationSubscription;
  final Set<String> _receivedMessageIds = {};
  int _unreadChange = 0;
  Future<void>? _startRequest;

  Future<void> start() => _startRequest ??= _start();

  Future<void> _start() async {
    _sessionGeneration = AccountSession.generation;
    _refreshSubscription ??= ChatUnreadRefreshBus.stream.listen((removed) {
      removeConversationUnread(removed);
      if (removed == 0) unawaited(loadUnreadCount());
    });
    _messageSubscription ??= _realtime.messages.listen(_handleIncomingMessage);
    _notificationSubscription ??= ForegroundNotificationBus.stream.listen(
      _handleNotification,
    );
    if (!UserModel.isAuthenticated) return;
    await Future.wait([loadUnreadCount(), _realtime.connect()]);
  }

  Future<void> loadUnreadCount() async {
    if (isClosed || isLoading || !await ChatData.hasAuthenticatedSession()) {
      return;
    }
    if (isClosed || isLoading) return;
    final int unreadChangeAtRequest = _unreadChange;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<ChatUnreadContent>(
          api: ApiConstants.tenantUnreadCounts,
          httpRequestType: HttpRequestType.get,
          cacheKey: 'chat_unread_count_v2',
          mapper: (json) => ChatUnreadContent.fromJson(
            json is Map<String, dynamic> ? json : const {},
          ),
          fromCacheJson: ChatUnreadContent.fromJson,
          toJson: (content) => content.toJson(),
        ),
      ),
      onSuccess: (_) {
        final int delta = _unreadChange - unreadChangeAtRequest;
        if (delta != 0) {
          updateData(data.copyWith(count: max(0, data.count + delta)));
        }
      },
      withInternetInterceptor: true,
    );
  }

  void removeConversationUnread(int unreadCount) {
    if (unreadCount <= 0) return;
    final int nextCount = data.count > unreadCount
        ? data.count - unreadCount
        : 0;
    _unreadChange -= unreadCount;
    updateData(data.copyWith(count: nextCount));
  }

  void _handleNotification(AppNotificationContent notification) {
    if (notification.kind != AppNotificationKind.newMessage &&
        notification.category != 'chat') {
      return;
    }
    _addUnreadMessage(
      messageId: notification.payload.messageId,
      conversationId: notification.payload.chatId,
      senderId: notification.payload.senderId,
    );
  }

  void _handleIncomingMessage(ChatSocketMessage message) {
    _addUnreadMessage(
      messageId: message.id,
      conversationId: message.conversationId,
      senderId: message.sender.id,
    );
  }

  void _addUnreadMessage({
    required String messageId,
    required String conversationId,
    required String senderId,
  }) {
    if (isClosed ||
        !UserModel.isAuthenticated ||
        _sessionGeneration != AccountSession.generation) {
      return;
    }
    // FCM and the personal socket may deliver the same incoming message.
    if (messageId.isNotEmpty) {
      if (!_receivedMessageIds.add(messageId)) return;
      if (_receivedMessageIds.length > 200) {
        _receivedMessageIds.remove(_receivedMessageIds.first);
      }
    }
    final String currentUserId = UserModel.currentUser?.id ?? '';
    if (senderId == currentUserId ||
        conversationId == _realtime.activeConversationId) {
      return;
    }
    _unreadChange++;
    updateData(data.copyWith(count: data.count + 1));
  }

  Future<void> onAppResumed() async {
    await Future.wait([loadUnreadCount(), _realtime.connect()]);
  }

  Future<void> onAppBackgrounded() async {
    if (_sessionGeneration == AccountSession.generation) {
      await _realtime.disconnect();
    }
  }

  @override
  Future<void> close() async {
    await _refreshSubscription?.cancel();
    await _messageSubscription?.cancel();
    await _notificationSubscription?.cancel();
    if (_sessionGeneration == AccountSession.generation) {
      await _realtime.disconnect();
    }
    return super.close();
  }
}
