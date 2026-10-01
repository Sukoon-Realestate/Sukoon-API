import 'dart:async';

import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/network/account_session.dart';

import '../../../notifications/data/enums/app_notification_kind.dart';
import '../../../notifications/data/foreground_notification_bus.dart';
import '../../../notifications/data/models/app_notification_content.dart';
import '../../../unread_counts/data/models/unread_counts.dart';
import '../../../unread_counts/presentation/cubits/unread_counts_cubit.dart';
import '../../data/chat_realtime_service.dart';
import '../../data/chat_unread_refresh_bus.dart';
import '../../data/models/chat_socket_message.dart';
import '../../data/models/chat_unread_content.dart';

class ChatUnreadCubit extends AsyncCubit<ChatUnreadContent> {
  ChatUnreadCubit({
    required UnreadCountsCubit unreadCounts,
    ChatRealtimeGateway? realtimeService,
  }) : _unreadCounts = unreadCounts,
       _realtime = realtimeService ?? ChatRealtimeService.instance,
       super(const ChatUnreadContent.initial());

  final UnreadCountsCubit _unreadCounts;
  final ChatRealtimeGateway _realtime;
  StreamSubscription<AsyncState<UnreadCounts>>? _countsSubscription;

  StreamSubscription<int>? _refreshSubscription;
  int _sessionGeneration = AccountSession.generation;
  StreamSubscription<ChatSocketMessage>? _messageSubscription;
  StreamSubscription<AppNotificationContent>? _notificationSubscription;
  final Set<String> _receivedMessageIds = {};
  Future<void>? _startRequest;

  void _watchCounts() {
    if (_countsSubscription != null || isClosed) return;
    _syncCounts();
    _countsSubscription = _unreadCounts.stream.listen((_) => _syncCounts());
  }

  Future<void> start() => _startRequest ??= _start();

  Future<void> _start() async {
    _sessionGeneration = AccountSession.generation;
    _watchCounts();
    _refreshSubscription ??= ChatUnreadRefreshBus.stream.listen((removed) {
      removeConversationUnread(removed);
      if (removed == 0) unawaited(_unreadCounts.refresh());
    });
    _messageSubscription ??= _realtime.messages.listen(_handleIncomingMessage);
    _notificationSubscription ??= ForegroundNotificationBus.stream.listen(
      _handleNotification,
    );
    if (!UserModel.isAuthenticated) return;
    await Future.wait([loadUnreadCount(), _realtime.connect()]);
  }

  Future<void> loadUnreadCount() async {
    if (isClosed) return;
    _watchCounts();
    await _unreadCounts.load();
    _syncCounts();
  }

  void removeConversationUnread(int unreadCount) {
    if (isClosed || unreadCount <= 0) return;
    _unreadCounts.changeChatCount(-unreadCount);
    _syncCounts();
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
    _unreadCounts.changeChatCount(1);
    _syncCounts();
  }

  Future<void> onAppResumed() async {
    await _realtime.connect();
  }

  Future<void> onAppBackgrounded() async {
    if (_sessionGeneration == AccountSession.generation) {
      await _realtime.disconnect();
    }
  }

  void _syncCounts() {
    final AsyncState<UnreadCounts> counts = _unreadCounts.state;
    emit(
      state.copyWith(
        status: counts.status,
        data: counts.data.chat,
        msg: counts.msg,
      ),
    );
  }

  @override
  Future<void> close() async {
    await _countsSubscription?.cancel();
    await _refreshSubscription?.cancel();
    await _messageSubscription?.cancel();
    await _notificationSubscription?.cancel();
    if (_sessionGeneration == AccountSession.generation) {
      await _realtime.disconnect();
    }
    return super.close();
  }
}
