import 'dart:async';
import 'dart:developer';

import 'package:equatable/equatable.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';

import '../../data/chat_data.dart';
import '../../data/chat_realtime_service.dart';
import '../../data/chat_unread_refresh_bus.dart';
import '../../data/models/chat_content.dart';
import '../../data/models/chat_socket_message.dart';

part 'chat_thread_state.dart';

class ChatSendResult {
  const ChatSendResult({required this.isSent, this.restMessage});

  const ChatSendResult.failed() : isSent = false, restMessage = null;

  final bool isSent;
  final ChatSocketMessage? restMessage;
}

class ChatThreadCubit extends Cubit<ChatThreadState> {
  ChatThreadCubit({
    required this.conversationId,
    ChatRealtimeService? realtimeService,
  }) : _realtime = realtimeService ?? ChatRealtimeService.instance,
       super(const ChatThreadState.initial());

  static const Duration _confirmationTimeout = Duration(seconds: 5);

  final String conversationId;
  final ChatRealtimeService _realtime;
  final Map<String, List<Completer<ChatSocketMessage>>> _confirmations = {};
  StreamSubscription<ChatSocketMessage>? _messageSubscription;
  StreamSubscription<ChatReadReceipt>? _readSubscription;
  StreamSubscription<ChatRealtimeStatus>? _statusSubscription;
  bool _shouldBeConnected = true;

  Future<void> connect() async {
    _realtime.setActiveConversation(conversationId);
    _messageSubscription ??= _realtime.messages.listen(_receiveMessage);
    _readSubscription ??= _realtime.readReceipts.listen(_receiveReadReceipt);
    _statusSubscription ??= _realtime.statuses.listen(_receiveStatus);
    _receiveStatus(_realtime.status);

    if (!_shouldBeConnected || !UserModel.isAuthenticated) return;
    await _realtime.connect();
    await markConversationAsRead();
  }

  Future<ChatSendResult> sendTextMessage(String rawContent) async {
    final String content = rawContent.trim();
    if (content.isEmpty ||
        content.length > 5000 ||
        !UserModel.isAuthenticated) {
      return const ChatSendResult.failed();
    }

    if (_realtime.isConnected) {
      final Completer<ChatSocketMessage> confirmation =
          Completer<ChatSocketMessage>();
      (_confirmations[content] ??= []).add(confirmation);
      try {
        await _realtime.sendMessage(
          conversationId: conversationId,
          content: content,
        );
        await confirmation.future.timeout(_confirmationTimeout);
        return const ChatSendResult(isSent: true);
      } catch (_) {
        _removeConfirmation(content, confirmation);
      }
    }

    try {
      final ChatMessageContent message = await ChatData.sendMessage(
        conversationId: conversationId,
        content: content,
      );
      return ChatSendResult(
        isSent: true,
        restMessage: _socketMessageFromRest(message),
      );
    } catch (error, stackTrace) {
      log('Unable to send chat message: $error', stackTrace: stackTrace);
      return const ChatSendResult.failed();
    }
  }

  Future<void> markConversationAsRead() async {
    if (!UserModel.isAuthenticated) return;
    if (_realtime.isConnected) {
      try {
        await _realtime.markConversationAsRead(conversationId);
        ChatUnreadRefreshBus.requestRefresh();
        return;
      } catch (_) {
        // Continue with the HTTP fallback below.
      }
    }

    try {
      await ChatData.markConversationAsRead(conversationId);
      ChatUnreadRefreshBus.requestRefresh();
    } catch (error, stackTrace) {
      log('Unable to mark chat as read: $error', stackTrace: stackTrace);
    }
  }

  Future<void> onAppLifecycleStateChanged(AppLifecycleState lifecycle) async {
    _shouldBeConnected =
        lifecycle == AppLifecycleState.resumed ||
        lifecycle == AppLifecycleState.inactive;
    switch (lifecycle) {
      case AppLifecycleState.resumed:
        await _realtime.connect();
        await markConversationAsRead();
      case AppLifecycleState.paused:
      case AppLifecycleState.detached:
      case AppLifecycleState.hidden:
        await _realtime.disconnect();
      case AppLifecycleState.inactive:
        break;
    }
  }

  void _receiveStatus(ChatRealtimeStatus status) {
    if (isClosed) return;
    final ChatSocketStatus mappedStatus = switch (status) {
      ChatRealtimeStatus.disconnected => ChatSocketStatus.disconnected,
      ChatRealtimeStatus.connecting => ChatSocketStatus.connecting,
      ChatRealtimeStatus.connected => ChatSocketStatus.connected,
      ChatRealtimeStatus.error => ChatSocketStatus.error,
    };
    emit(state.copyWith(status: mappedStatus));
  }

  void _receiveMessage(ChatSocketMessage message) {
    if (isClosed || !_isActiveConversation(message.conversationId)) return;
    _confirmOutgoingMessage(message);
    emit(
      state.copyWith(
        receivedMessage: message,
        receivedMessageRevision: state.receivedMessageRevision + 1,
      ),
    );
  }

  void _receiveReadReceipt(ChatReadReceipt receipt) {
    if (isClosed || !_isActiveConversation(receipt.conversationId)) return;
    emit(state.copyWith(readReceiptRevision: state.readReceiptRevision + 1));
  }

  void _confirmOutgoingMessage(ChatSocketMessage message) {
    final String currentUserId = UserModel.currentUser?.id ?? '';
    if (currentUserId.isEmpty || message.sender.id != currentUserId) return;
    final List<Completer<ChatSocketMessage>>? pending =
        _confirmations[message.content];
    if (pending == null || pending.isEmpty) return;
    final Completer<ChatSocketMessage> confirmation = pending.removeAt(0);
    if (pending.isEmpty) _confirmations.remove(message.content);
    if (!confirmation.isCompleted) confirmation.complete(message);
  }

  void _removeConfirmation(
    String content,
    Completer<ChatSocketMessage> confirmation,
  ) {
    final List<Completer<ChatSocketMessage>>? pending = _confirmations[content];
    pending?.remove(confirmation);
    if (pending?.isEmpty ?? false) _confirmations.remove(content);
  }

  ChatSocketMessage _socketMessageFromRest(ChatMessageContent message) {
    return ChatSocketMessage(
      id: message.id.toString(),
      conversationId: message.conversationId.isEmpty
          ? conversationId
          : message.conversationId,
      sender: ChatSocketSender(
        id: message.sender.id,
        name: message.sender.fullName,
        avatarUrl: message.sender.avatarUrl,
        isOnline: message.sender.isOnline,
      ),
      content: message.body,
      createdAt: message.createdAt,
    );
  }

  bool _isActiveConversation(String incomingConversationId) {
    return incomingConversationId.isEmpty ||
        incomingConversationId == conversationId;
  }

  @override
  Future<void> close() async {
    _shouldBeConnected = false;
    if (_realtime.activeConversationId == conversationId) {
      _realtime.setActiveConversation(null);
    }
    await _messageSubscription?.cancel();
    await _readSubscription?.cancel();
    await _statusSubscription?.cancel();
    for (final List<Completer<ChatSocketMessage>> confirmations
        in _confirmations.values) {
      for (final Completer<ChatSocketMessage> confirmation in confirmations) {
        if (!confirmation.isCompleted) {
          confirmation.completeError(StateError('Chat thread was closed.'));
        }
      }
    }
    _confirmations.clear();
    return super.close();
  }
}
