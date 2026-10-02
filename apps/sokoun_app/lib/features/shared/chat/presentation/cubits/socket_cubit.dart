import 'dart:async';
import 'package:melos_core/core/helpers/validators.dart';
import 'dart:developer';

import 'package:equatable/equatable.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/network/account_session.dart';

import '../../data/chats_data.dart';
import '../../data/chat_realtime_service.dart';
import '../../data/chat_unread_refresh_bus.dart';
import '../../data/models/chat_content.dart';
import '../../data/models/chat_socket_message.dart';

part 'chat_thread_state.dart';

enum ChatSendStatus { sent, queued, failed }

class ChatSendResult {
  const ChatSendResult.sent({this.restMessage}) : status = ChatSendStatus.sent;

  const ChatSendResult.queued()
    : status = ChatSendStatus.queued,
      restMessage = null;

  const ChatSendResult.failed()
    : status = ChatSendStatus.failed,
      restMessage = null;

  final ChatSendStatus status;
  final ChatSocketMessage? restMessage;

  bool get isSent => status == ChatSendStatus.sent;

  bool get isQueued => status == ChatSendStatus.queued;
}

class ChatThreadCubit extends Cubit<ChatThreadState> {
  ChatThreadCubit({
    required this.conversationId,
    this.otherParticipantId = '',
    ChatRealtimeGateway? realtimeService,
    ChatDataSource? dataSource,
  }) : _realtime = realtimeService ?? ChatRealtimeService.instance,
       _dataSource = dataSource ?? ChatData.source,
       super(const ChatThreadState.initial());

  static const Duration _confirmationTimeout = Duration(seconds: 5);
  static const Duration _queueRetryDelay = Duration(seconds: 5);

  final String conversationId;
  final String otherParticipantId;
  final ChatRealtimeGateway _realtime;
  final ChatDataSource _dataSource;
  final int _sessionGeneration = AccountSession.generation;
  final List<_QueuedChatMessage> _outbox = [];
  final Map<String, List<_SocketConfirmation>> _confirmations = {};
  StreamSubscription<ChatSocketMessage>? _messageSubscription;
  StreamSubscription<ChatReadReceipt>? _readSubscription;
  StreamSubscription<ChatRealtimeStatus>? _statusSubscription;
  Future<void>? _outboxFlush;
  Timer? _queueRetryTimer;
  bool _shouldBeConnected = true;
  bool _closing = false;

  bool get _hasCurrentSession =>
      !isClosed && !_closing && _sessionGeneration == AccountSession.generation;

  int get queuedMessageCount => _outbox.length;

  Future<void> connect() async {
    if (!_hasCurrentSession || !_shouldBeConnected) return;
    _realtime.setActiveConversation(conversationId);
    _messageSubscription ??= _realtime.messages.listen(_receiveMessage);
    _readSubscription ??= _realtime.readReceipts.listen(_receiveReadReceipt);
    _statusSubscription ??= _realtime.statuses.listen(_receiveStatus);
    _receiveStatus(_realtime.status);

    await _realtime.connect();
    if (!_hasCurrentSession || !_shouldBeConnected) return;
    await markConversationAsRead();
  }

  Future<ChatSendResult> sendTextMessage(
    String rawContent, {
    String? localMessageId,
  }) async {
    if (!_hasCurrentSession) return const ChatSendResult.failed();
    final String content = rawContent.trim();
    if (!Validators.isValidChatContent(content)) {
      return const ChatSendResult.failed();
    }

    final _QueuedChatMessage queuedMessage = _QueuedChatMessage(
      localMessageId:
          localMessageId ?? 'local-${DateTime.now().microsecondsSinceEpoch}',
      content: content,
    );
    _outbox.add(queuedMessage);
    _emitQueuedMessageCount();

    if (!_realtime.isConnected && _shouldBeConnected) {
      try {
        await connect();
      } catch (error, stackTrace) {
        log(
          'Unable to connect the chat socket before sending: $error',
          stackTrace: stackTrace,
        );
      }
    }

    if (!_realtime.isConnected) return const ChatSendResult.queued();

    await _flushOutbox();
    return queuedMessage.result ?? const ChatSendResult.queued();
  }

  Future<void> markConversationAsRead() async {
    if (!_hasCurrentSession) return;
    if (_realtime.isConnected) {
      try {
        await _realtime.markConversationAsRead(conversationId);
        if (_hasCurrentSession) ChatUnreadRefreshBus.requestRefresh();
        return;
      } catch (_) {
        // Continue with the HTTP fallback below.
      }
    }

    if (!_hasCurrentSession) return;
    try {
      await _dataSource.markConversationAsRead(conversationId);
      if (_hasCurrentSession) ChatUnreadRefreshBus.requestRefresh();
    } catch (error, stackTrace) {
      log('Unable to mark chat as read: $error', stackTrace: stackTrace);
    }
  }

  Future<void> onAppLifecycleStateChanged(AppLifecycleState lifecycle) async {
    if (!_hasCurrentSession ||
        _realtime.activeConversationId != conversationId) {
      return;
    }
    _shouldBeConnected =
        lifecycle == AppLifecycleState.resumed ||
        lifecycle == AppLifecycleState.inactive;
    switch (lifecycle) {
      case AppLifecycleState.resumed:
        await connect();
      case AppLifecycleState.paused:
      case AppLifecycleState.detached:
      case AppLifecycleState.hidden:
        await _realtime.disconnect();
      case AppLifecycleState.inactive:
        break;
    }
  }

  void _receiveStatus(ChatRealtimeStatus status) {
    if (!_hasCurrentSession) return;
    final ChatSocketStatus mappedStatus = switch (status) {
      ChatRealtimeStatus.disconnected => ChatSocketStatus.disconnected,
      ChatRealtimeStatus.connecting => ChatSocketStatus.connecting,
      ChatRealtimeStatus.connected => ChatSocketStatus.connected,
      ChatRealtimeStatus.error => ChatSocketStatus.error,
    };
    emit(state.copyWith(status: mappedStatus));
    if (status == ChatRealtimeStatus.connected && _outbox.isNotEmpty) {
      _queueRetryTimer?.cancel();
      unawaited(_flushOutbox());
    }
  }

  void _receiveMessage(ChatSocketMessage message) {
    if (!_hasCurrentSession) return;
    final String? localMessageId = _confirmOutgoingMessage(message);
    if (localMessageId == null && !_isMessageFromActiveConversation(message)) {
      return;
    }
    _emitReceivedMessage(message, localMessageId: localMessageId);
  }

  void _receiveReadReceipt(ChatReadReceipt receipt) {
    if (!_hasCurrentSession || !_isActiveConversation(receipt.conversationId)) {
      return;
    }
    emit(state.copyWith(readReceiptRevision: state.readReceiptRevision + 1));
  }

  String? _confirmOutgoingMessage(ChatSocketMessage message) {
    final String currentUserId = UserModel.currentUser?.id ?? '';
    if (currentUserId.isEmpty || message.sender.id != currentUserId) {
      return null;
    }
    final List<_SocketConfirmation>? pending = _confirmations[message.content];
    if (pending == null || pending.isEmpty) return null;
    final _SocketConfirmation confirmation = pending.removeAt(0);
    if (pending.isEmpty) _confirmations.remove(message.content);
    if (!confirmation.completer.isCompleted) {
      confirmation.completer.complete(message);
    }
    return confirmation.localMessageId;
  }

  void _removeConfirmation(String content, _SocketConfirmation confirmation) {
    final List<_SocketConfirmation>? pending = _confirmations[content];
    pending?.remove(confirmation);
    if (pending?.isEmpty ?? false) _confirmations.remove(content);
  }

  Future<void> _flushOutbox() async {
    final Future<void>? activeFlush = _outboxFlush;
    if (activeFlush != null) {
      await activeFlush;
      return;
    }

    final Future<void> flush = _drainOutbox();
    _outboxFlush = flush;
    try {
      await flush;
    } finally {
      if (identical(_outboxFlush, flush)) _outboxFlush = null;
    }
  }

  Future<void> _drainOutbox() async {
    while (_outbox.isNotEmpty && _realtime.isConnected && _hasCurrentSession) {
      final _QueuedChatMessage queuedMessage = _outbox.first;
      final ChatSendResult result = await _deliverQueuedMessage(queuedMessage);
      if (!result.isSent) {
        _scheduleQueueRetry();
        return;
      }

      queuedMessage.result = result;
      _outbox.removeAt(0);
      _emitQueuedMessageCount();
    }
  }

  Future<ChatSendResult> _deliverQueuedMessage(
    _QueuedChatMessage queuedMessage,
  ) async {
    final Completer<ChatSocketMessage> completer =
        Completer<ChatSocketMessage>();
    final _SocketConfirmation confirmation = _SocketConfirmation(
      localMessageId: queuedMessage.localMessageId,
      completer: completer,
    );
    (_confirmations[queuedMessage.content] ??= []).add(confirmation);

    try {
      await _realtime.sendMessage(
        conversationId: conversationId,
        content: queuedMessage.content,
      );
      final ChatSocketMessage confirmedMessage = await completer.future.timeout(
        _confirmationTimeout,
      );
      return ChatSendResult.sent(restMessage: confirmedMessage);
    } catch (socketError, socketStackTrace) {
      _removeConfirmation(queuedMessage.content, confirmation);
      if (!_hasCurrentSession || !_realtime.isConnected) {
        log(
          'Chat message remains queued until the socket reconnects: '
          '$socketError',
          stackTrace: socketStackTrace,
        );
        return const ChatSendResult.queued();
      }
    }

    try {
      final ChatMessageContent message = await _dataSource.sendMessage(
        conversationId: conversationId,
        content: queuedMessage.content,
      );
      final ChatSocketMessage restMessage = _socketMessageFromRest(message);
      _emitReceivedMessage(
        restMessage,
        localMessageId: queuedMessage.localMessageId,
      );
      return ChatSendResult.sent(restMessage: restMessage);
    } catch (error, stackTrace) {
      log('Unable to send queued chat message: $error', stackTrace: stackTrace);
      return const ChatSendResult.queued();
    }
  }

  void _emitReceivedMessage(
    ChatSocketMessage message, {
    String? localMessageId,
  }) {
    if (!_hasCurrentSession) return;
    emit(
      state.copyWith(
        receivedMessage: message,
        confirmedLocalMessageId: localMessageId,
        receivedMessageRevision: state.receivedMessageRevision + 1,
      ),
    );
  }

  void _emitQueuedMessageCount() {
    if (!_hasCurrentSession) return;
    emit(state.copyWith(queuedMessageCount: _outbox.length));
  }

  void _scheduleQueueRetry() {
    if (!_shouldBeConnected || _outbox.isEmpty || !_hasCurrentSession) return;
    _queueRetryTimer?.cancel();
    _queueRetryTimer = Timer(_queueRetryDelay, () async {
      if (!_shouldBeConnected || _outbox.isEmpty || !_hasCurrentSession) return;
      if (!_realtime.isConnected) await _realtime.connect();
      if (_realtime.isConnected) await _flushOutbox();
    });
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

  bool _isMessageFromActiveConversation(ChatSocketMessage message) {
    if (_isActiveConversation(message.conversationId)) {
      return true;
    }

    return otherParticipantId.isNotEmpty &&
        message.sender.id == otherParticipantId;
  }

  bool _isActiveConversation(String incomingConversationId) {
    return incomingConversationId.isEmpty ||
        incomingConversationId == conversationId;
  }

  @override
  Future<void> close() async {
    _closing = true;
    _shouldBeConnected = false;
    _queueRetryTimer?.cancel();
    if (_realtime.activeConversationId == conversationId) {
      _realtime.setActiveConversation(null);
      await _realtime.disconnect();
    }
    await _messageSubscription?.cancel();
    await _readSubscription?.cancel();
    await _statusSubscription?.cancel();
    for (final List<_SocketConfirmation> confirmations
        in _confirmations.values) {
      for (final _SocketConfirmation confirmation in confirmations) {
        if (!confirmation.completer.isCompleted) {
          confirmation.completer.completeError(
            StateError('Chat thread was closed.'),
          );
        }
      }
    }
    _confirmations.clear();
    return super.close();
  }
}

class _QueuedChatMessage {
  _QueuedChatMessage({required this.localMessageId, required this.content});

  final String localMessageId;
  final String content;
  ChatSendResult? result;
}

class _SocketConfirmation {
  const _SocketConfirmation({
    required this.localMessageId,
    required this.completer,
  });

  final String localMessageId;
  final Completer<ChatSocketMessage> completer;
}

/// Reference-style name for the realtime cubit used by a single chat screen.
class SocketCubit extends ChatThreadCubit {
  SocketCubit({
    required super.conversationId,
    super.otherParticipantId,
    super.realtimeService,
    super.dataSource,
  });
}
