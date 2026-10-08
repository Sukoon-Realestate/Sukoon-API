import 'package:sokoun_app/features/main_view/data/account_access.dart';
import 'dart:async';
import 'package:melos_core/core/helpers/validators.dart';
import 'dart:developer';

import 'package:equatable/equatable.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:uuid/uuid.dart';

import '../../data/chat_data.dart';
import '../../data/chat_local_data.dart';
import '../../data/models/chat_local_state.dart';
import '../../data/chat_realtime_service.dart';
import '../../data/chat_unread_refresh_bus.dart';
import '../../data/models/chat_content.dart';
import '../../data/models/chat_socket_message.dart';
import '../../data/models/chat_message_acknowledgement.dart';

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
    ChatLocalStore? localStore,
    bool canSend = true,
  }) : _conversationCanSend = canSend,
       _realtime = realtimeService ?? ChatRealtimeService.instance,
       _dataSource = dataSource ?? ChatData.source,
       _localStore =
           localStore ??
           ChatLocalData(
             accountId: UserModel.currentUser?.id ?? '',
             conversationId: conversationId,
           ),
       super(const ChatThreadState.initial());

  static const Duration _confirmationTimeout = Duration(seconds: 5);
  static const Duration _queueRetryDelay = Duration(seconds: 5);
  static const Duration _queuedNoticeDelay = Duration(seconds: 2);

  final String conversationId;
  final String otherParticipantId;
  final ChatRealtimeGateway _realtime;
  final ChatDataSource _dataSource;
  final ChatLocalStore _localStore;
  final bool _conversationCanSend;
  bool get canSend => _conversationCanSend && AccountAccess.isVerified;
  Future<void>? _localLoad;
  bool _draftEdited = false;
  Future<void>? _localWrites;
  Timer? _draftTimer;
  String _draftClientMessageId = '';

  Future<void> _loadLocal() => _localLoad ??= () async {
    try {
      final saved = await _localStore.read();
      if (!isClosed && _sessionGeneration == AccountSession.generation) {
        if (!_draftEdited) _draftClientMessageId = saved.draftClientMessageId;
        emit(
          state.copyWith(
            draft: _draftEdited ? state.draft : saved.draft,
            recoveredMessages: saved.messages,
          ),
        );
      }
    } catch (_) {
      if (_hasCurrentSession) emit(state.copyWith(localSaveFailed: true));
    }
  }();

  Future<void> _persistLocal() {
    final previous = _localWrites;
    final write = () async {
      if (previous != null) await previous;
      await _loadLocal();
      if (_sessionGeneration != AccountSession.generation) return;
      final snapshot = ChatLocalState(
        draft: state.draft,
        draftClientMessageId: _draftClientMessageId,
        messages: [
          ...state.recoveredMessages,
          for (final message in _outbox)
            SavedChatMessage(
              id: message.localMessageId,
              content: message.content,
              clientMessageId: message.clientMessageId,
            ),
        ],
      );
      try {
        await _localStore.write(snapshot);
        if (_hasCurrentSession) emit(state.copyWith(localSaveFailed: false));
      } catch (_) {
        if (_hasCurrentSession) emit(state.copyWith(localSaveFailed: true));
        rethrow;
      }
    }();
    _localWrites = write.catchError((Object _) {});
    return write;
  }

  void updateDraft(String value) {
    if (!_hasCurrentSession || !canSend) return;
    _draftEdited = true;
    if (value.trim() != state.draft.trim()) _draftClientMessageId = '';
    emit(state.copyWith(draft: value));
    _draftTimer?.cancel();
    _draftTimer = Timer(const Duration(milliseconds: 350), () {
      unawaited(_persistLocal().catchError((Object _) {}));
    });
  }

  Future<bool> restoreMessageDraft(SavedChatMessage message) async {
    if (!_hasCurrentSession || !canSend || state.draft.trim().isNotEmpty) {
      return false;
    }
    _draftEdited = true;
    // Reuse the original send identity unless the user edits its content.
    _draftClientMessageId = message.clientMessageId;
    emit(
      state.copyWith(
        draft: message.content,
        recoveredMessages: state.recoveredMessages
            .where((item) => item.id != message.id)
            .toList(),
      ),
    );
    await _persistLocal();
    return true;
  }

  final int _sessionGeneration = AccountSession.generation;
  final List<_QueuedChatMessage> _outbox = [];
  final Map<String, _SocketConfirmation> _confirmations = {};
  StreamSubscription<ChatSocketMessage>? _messageSubscription;
  StreamSubscription<ChatMessageAcknowledgement>? _acknowledgementSubscription;
  StreamSubscription<ChatReadReceipt>? _readSubscription;
  StreamSubscription<ChatRealtimeStatus>? _statusSubscription;
  Future<void>? _outboxFlush;
  Timer? _queueRetryTimer;
  bool _shouldBeConnected = true;
  bool _closing = false;

  bool get _hasCurrentSession =>
      !isClosed &&
      !_closing &&
      AccountAccess.isVerified &&
      _sessionGeneration == AccountSession.generation;

  int get queuedMessageCount => _outbox.length;

  Future<void> connect() async {
    if (!_hasCurrentSession || !_shouldBeConnected) return;
    await _loadLocal();
    if (!_hasCurrentSession || !canSend) return;
    _realtime.setActiveConversation(conversationId);
    _messageSubscription ??= _realtime.messages.listen(_receiveMessage);
    _acknowledgementSubscription ??= _realtime.acknowledgements.listen(
      _receiveAcknowledgement,
    );
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
    if (!_hasCurrentSession || !canSend) return const ChatSendResult.failed();
    await _loadLocal();
    if (!_hasCurrentSession) return const ChatSendResult.failed();
    final String content = rawContent.trim();
    if (!Validators.isValidChatContent(content)) {
      return const ChatSendResult.failed();
    }

    final _QueuedChatMessage queuedMessage = _QueuedChatMessage(
      localMessageId:
          localMessageId ?? 'local-${DateTime.now().microsecondsSinceEpoch}',
      content: content,
      clientMessageId:
          _draftClientMessageId.isNotEmpty && state.draft.trim() == content
          ? _draftClientMessageId
          : const Uuid().v4(),
    );
    _outbox.add(queuedMessage);
    try {
      await _persistLocal();
    } catch (_) {
      _outbox.remove(queuedMessage);
      return const ChatSendResult.failed();
    }
    _draftClientMessageId = '';
    queuedMessage.noticeTimer = Timer(_queuedNoticeDelay, () {
      if (!_hasCurrentSession || !_outbox.contains(queuedMessage)) return;
      queuedMessage.showQueuedNotice = true;
      _emitQueuedMessageCount();
    });
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

    if (!_hasCurrentSession) return const ChatSendResult.failed();
    if (!_realtime.isConnected) {
      queuedMessage.showQueuedNotice = true;
      _emitQueuedMessageCount();
      _scheduleQueueRetry();
      return const ChatSendResult.queued();
    }

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
    if (lifecycle != AppLifecycleState.resumed) {
      _draftTimer?.cancel();
      // Storage cannot delay socket ownership during rapid pause/resume events.
      unawaited(_persistLocal().catchError((Object _) {}));
    }
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
    if (status == ChatRealtimeStatus.error ||
        (status == ChatRealtimeStatus.disconnected &&
            state.status == ChatSocketStatus.connected)) {
      for (final message in _outbox) {
        message.showQueuedNotice = true;
      }
    }
    final ChatSocketStatus mappedStatus = switch (status) {
      ChatRealtimeStatus.disconnected => ChatSocketStatus.disconnected,
      ChatRealtimeStatus.connecting => ChatSocketStatus.connecting,
      ChatRealtimeStatus.connected => ChatSocketStatus.connected,
      ChatRealtimeStatus.error => ChatSocketStatus.error,
    };
    emit(
      state.copyWith(
        status: mappedStatus,
        showQueuedMessages: _outbox.any((message) => message.showQueuedNotice),
      ),
    );
    if (status == ChatRealtimeStatus.connected && _outbox.isNotEmpty) {
      _queueRetryTimer?.cancel();
      unawaited(_flushOutbox());
    }
  }

  void _receiveMessage(ChatSocketMessage message) {
    if (!_hasCurrentSession || !_isMessageFromActiveConversation(message)) {
      return;
    }
    final pending = _confirmations[message.clientMessageId];
    if (pending != null && pending.message.content != message.content) return;
    final String? localMessageId = _confirmOutgoingMessage(message);
    _emitReceivedMessage(message, localMessageId: localMessageId);
  }

  void _receiveAcknowledgement(ChatMessageAcknowledgement acknowledgement) {
    if (!_hasCurrentSession || !acknowledgement.isSent) return;
    final confirmation = _confirmations[acknowledgement.clientMessageId];
    final user = UserModel.currentUser;
    if (confirmation == null || user == null || user.id.isEmpty) return;
    _receiveMessage(
      ChatSocketMessage(
        id: acknowledgement.id,
        clientMessageId: acknowledgement.clientMessageId,
        conversationId: conversationId,
        sender: ChatParticipantContent(
          id: user.id,
          fullName: user.name,
          avatarUrl: '',
          isOnline: true,
        ),
        content: confirmation.message.content,
        createdAt: null,
      ),
    );
  }

  void _receiveReadReceipt(ChatReadReceipt receipt) {
    if (!_hasCurrentSession || !_isActiveConversation(receipt.conversationId)) {
      return;
    }
    emit(state.copyWith(readReceiptRevision: state.readReceiptRevision + 1));
  }

  String? _confirmOutgoingMessage(ChatSocketMessage message) {
    final String currentUserId = UserModel.currentUser?.id ?? '';
    if (currentUserId.isEmpty ||
        message.sender.id != currentUserId ||
        message.id.isEmpty ||
        message.conversationId != conversationId ||
        message.clientMessageId.isEmpty) {
      return null;
    }
    final confirmation = _confirmations.remove(message.clientMessageId);
    if (confirmation == null) return null;
    if (!confirmation.completer.isCompleted) {
      confirmation.completer.complete(message);
    }
    return confirmation.message.localMessageId;
  }

  void _removeConfirmation(_SocketConfirmation confirmation) {
    if (identical(
      _confirmations[confirmation.message.clientMessageId],
      confirmation,
    )) {
      _confirmations.remove(confirmation.message.clientMessageId);
    }
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
      queuedMessage.noticeTimer?.cancel();
      _outbox.removeAt(0);
      await _persistLocal();
      _emitQueuedMessageCount();
    }
  }

  Future<ChatSendResult> _deliverQueuedMessage(
    _QueuedChatMessage queuedMessage,
  ) async {
    final Completer<ChatSocketMessage> completer =
        Completer<ChatSocketMessage>();
    final _SocketConfirmation confirmation = _SocketConfirmation(
      message: queuedMessage,
      completer: completer,
    );
    _confirmations[queuedMessage.clientMessageId] = confirmation;

    try {
      await _realtime.sendMessage(
        conversationId: conversationId,
        content: queuedMessage.content,
        clientMessageId: queuedMessage.clientMessageId,
      );
      final ChatSocketMessage confirmedMessage = await completer.future.timeout(
        _confirmationTimeout,
      );
      return ChatSendResult.sent(restMessage: confirmedMessage);
    } catch (socketError, socketStackTrace) {
      _removeConfirmation(confirmation);
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
        clientMessageId: queuedMessage.clientMessageId,
      );
      if (!_hasCurrentSession ||
          message.id.isEmpty ||
          message.clientMessageId != queuedMessage.clientMessageId ||
          message.conversationId != conversationId ||
          message.sender.id != UserModel.currentUser?.id ||
          message.body != queuedMessage.content) {
        return const ChatSendResult.queued();
      }
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
    emit(
      state.copyWith(
        queuedMessageCount: _outbox.length,
        showQueuedMessages: _outbox.any((message) => message.showQueuedNotice),
      ),
    );
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
      sender: ChatParticipantContent(
        id: message.sender.id,
        fullName: message.sender.fullName,
        avatarUrl: message.sender.avatarUrl,
        isOnline: message.sender.isOnline,
      ),
      content: message.body,
      clientMessageId: message.clientMessageId,
      createdAt: message.createdAt,
    );
  }

  bool _isMessageFromActiveConversation(ChatSocketMessage message) {
    if (message.conversationId.isNotEmpty) {
      if (message.conversationId == conversationId) return true;
      // Socket payloads can use the numeric database ID while REST uses the
      // public conversation ID. Match these direct-chat replies by participant.
      if (int.tryParse(message.conversationId) == null ||
          int.tryParse(conversationId) != null) {
        return false;
      }
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
    final flushDraft =
        _draftTimer?.isActive == true ||
        (state.localSaveFailed && _draftEdited);
    _closing = true;
    _shouldBeConnected = false;
    _queueRetryTimer?.cancel();
    _draftTimer?.cancel();
    for (final message in _outbox) {
      message.noticeTimer?.cancel();
    }
    // Start storage and connection cleanup together. Disk IO must not retain a socket.
    final cleanup = <Future<void>>[];
    if (flushDraft && _sessionGeneration == AccountSession.generation) {
      cleanup.add(_persistLocal().catchError((Object _) {}));
    }
    if (_realtime.activeConversationId == conversationId) {
      _realtime.setActiveConversation(null);
      cleanup.add(_realtime.disconnect());
    }
    if (_messageSubscription != null) {
      cleanup.add(_messageSubscription!.cancel());
    }
    if (_acknowledgementSubscription != null) {
      cleanup.add(_acknowledgementSubscription!.cancel());
    }
    if (_readSubscription != null) cleanup.add(_readSubscription!.cancel());
    if (_statusSubscription != null) cleanup.add(_statusSubscription!.cancel());
    for (final confirmation in _confirmations.values) {
      if (!confirmation.completer.isCompleted) {
        confirmation.completer.completeError(
          StateError('Chat thread was closed.'),
        );
      }
    }
    _confirmations.clear();
    try {
      await Future.wait(cleanup);
      await _localWrites;
    } finally {
      await super.close();
    }
  }
}

class _QueuedChatMessage {
  _QueuedChatMessage({
    required this.localMessageId,
    required this.content,
    required this.clientMessageId,
  });

  final String localMessageId;
  final String content;
  final String clientMessageId;
  ChatSendResult? result;
  Timer? noticeTimer;
  bool showQueuedNotice = false;
}

class _SocketConfirmation {
  const _SocketConfirmation({required this.message, required this.completer});

  final _QueuedChatMessage message;
  final Completer<ChatSocketMessage> completer;
}
