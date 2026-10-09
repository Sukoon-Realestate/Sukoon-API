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
import '../../../notifications/data/foreground_notification_bus.dart';
import '../../../notifications/data/enums/app_notification_kind.dart';

part 'chat_thread_state.dart';

enum ChatSendStatus { sent, queued, failed, unknown }

class ChatSendResult {
  const ChatSendResult.sent({this.restMessage}) : status = ChatSendStatus.sent;

  const ChatSendResult.queued()
    : status = ChatSendStatus.queued,
      restMessage = null;

  const ChatSendResult.unknown()
    : status = ChatSendStatus.unknown,
      restMessage = null;

  const ChatSendResult.failed()
    : status = ChatSendStatus.failed,
      restMessage = null;

  final ChatSendStatus status;
  final ChatSocketMessage? restMessage;

  bool get isSent => status == ChatSendStatus.sent;

  bool get isQueued =>
      status == ChatSendStatus.queued || status == ChatSendStatus.unknown;
}

class ChatThreadCubit extends Cubit<ChatThreadState> {
  ChatThreadCubit({
    required this.conversationId,
    this.otherParticipantId = '',
    this.readOnly = false,
    ChatRealtimeGateway? realtimeService,
    ChatDataSource? dataSource,
    ChatLocalStore? localStore,
    bool canSend = true,
    this.durableReplay = const bool.fromEnvironment(
      'SOKOUN_CHAT_DURABLE_REPLAY',
      defaultValue: false,
    ),
    ChatParticipantContent initialContact =
        const ChatParticipantContent.initial(),
  }) : _realtime = realtimeService ?? ChatRealtimeService.instance,
       _dataSource = dataSource ?? ChatData.source,
       _localStore =
           localStore ??
           ChatLocalData(
             accountId: UserModel.currentUser?.id ?? '',
             conversationId: conversationId,
           ),
       super(
         const ChatThreadState.initial().copyWith(
           contact: initialContact,
           canSend: canSend,
         ),
       );

  static const Duration _confirmationTimeout = Duration(seconds: 5);
  static const Duration _queueRetryDelay = Duration(seconds: 5);
  static const Duration _queuedNoticeDelay = Duration(seconds: 2);

  final String conversationId;
  final String otherParticipantId;
  final bool readOnly;
  final bool durableReplay;
  void Function()? _unregisterCleanup;
  int _retryAttempt = 0;
  final ChatRealtimeGateway _realtime;
  final ChatDataSource _dataSource;
  final ChatLocalStore _localStore;
  bool get canSend => !readOnly && state.canSend && AccountAccess.isVerified;
  Future<void>? _localLoad;
  Future<void>? _contactRefresh;
  bool _contactRefreshAgain = false;
  StreamSubscription<Object?>? _contactNotificationSubscription;

  Future<void> refreshContact({bool afterVisitAcceptance = false}) {
    if (!_hasCurrentSession) return Future<void>.value();
    if (_contactRefresh != null) {
      // A read started before acceptance may still contain the hidden snapshot.
      _contactRefreshAgain |= afterVisitAcceptance;
      return _contactRefresh!;
    }
    return _contactRefresh ??= _loadContact().whenComplete(() {
      _contactRefresh = null;
      if (_contactRefreshAgain) {
        _contactRefreshAgain = false;
        unawaited(refreshContact());
      }
    });
  }

  Future<void> _loadContact() async {
    try {
      final ConversationContent conversation = await _dataSource
          .getConversation(conversationId);
      if (!_hasCurrentSession || conversation.id != conversationId) return;
      if (otherParticipantId.isNotEmpty &&
          conversation.otherParticipant.id != otherParticipantId) {
        return;
      }
      final bool wasAllowedToSend = canSend;
      emit(
        state.copyWith(
          contact: conversation.otherParticipant,
          canSend: conversation.canSend,
        ),
      );
      if (!canSend) {
        _queueRetryTimer?.cancel();
      } else if (!wasAllowedToSend && _shouldBeConnected) {
        await connect();
      }
    } catch (_) {
      // A failed refresh cannot grant contact access. Keep the supplied snapshot.
    }
  }

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
            needsDraftDecision:
                !_draftEdited && saved.draft.trim().isNotEmpty && !readOnly,
            draftSaved: !_draftEdited && saved.draft.trim().isNotEmpty,
            recoveredMessages: durableReplay ? const [] : saved.messages,
          ),
        );
        if (durableReplay && !readOnly) {
          for (final message in saved.messages) {
            if (message.delivery == ChatDeliveryState.sent ||
                !Uuid.isValidUUID(fromString: message.clientMessageId) ||
                !Validators.isValidChatContent(message.content)) {
              continue;
            }
            _outbox.add(
              _QueuedChatMessage(
                localMessageId: message.id,
                content: message.content,
                clientMessageId: message.clientMessageId,
              )..showQueuedNotice = true,
            );
          }
          _emitQueuedMessageCount();
        }
      }
    } catch (_) {
      if (_hasCurrentSession) {
        emit(
          state.copyWith(
            localSaveFailed: true,
            isSavingDraft: false,
            draftSaved: false,
          ),
        );
      }
    }
  }();

  Future<void> resolveComposerDraft(bool keep) async {
    if (!_hasCurrentSession) return;
    if (!keep) {
      _draftEdited = true;
      _draftClientMessageId = '';
    }
    emit(
      state.copyWith(draft: keep ? state.draft : '', needsDraftDecision: false),
    );
    await _persistLocal();
  }

  Future<void> reconcileHistory(List<ChatMessageContent> messages) async {
    await _loadLocal();
    if (!_hasCurrentSession) return;
    bool changed = false;
    for (final message in messages) {
      if (message.id.isEmpty ||
          message.clientMessageId.isEmpty ||
          message.conversationId != conversationId ||
          message.sender.id != UserModel.currentUser?.id) {
        continue;
      }
      final queued = _outbox
          .where(
            (item) =>
                item.clientMessageId == message.clientMessageId &&
                item.content == message.body,
          )
          .firstOrNull;
      if (queued != null) {
        final confirmation = _confirmations.remove(message.clientMessageId);
        if (confirmation != null && !confirmation.completer.isCompleted) {
          confirmation.completer.complete(_socketMessageFromRest(message));
        }
        queued.noticeTimer?.cancel();
        _outbox.remove(queued);
        _emitReceivedMessage(
          _socketMessageFromRest(message),
          localMessageId: queued.localMessageId,
        );
        changed = true;
      }
      final remaining = state.recoveredMessages
          .where(
            (item) =>
                item.clientMessageId != message.clientMessageId ||
                item.content != message.body,
          )
          .toList();
      if (remaining.length != state.recoveredMessages.length) {
        emit(state.copyWith(recoveredMessages: remaining));
        changed = true;
      }
    }
    if (changed) {
      await _persistLocal();
      _emitQueuedMessageCount();
    }
  }

  Future<void>? _deliveryRead;
  Future<void> checkDelivery() => _deliveryRead ??= () async {
    if (!_hasCurrentSession || readOnly) return;
    try {
      final (messages, _) = await _dataSource.getMessagesPage(
        conversationId: conversationId,
        page: 1,
      );
      await reconcileHistory(messages);
    } catch (_) {
      /* A failed read cannot establish a delivery outcome. */
    }
  }().whenComplete(() => _deliveryRead = null);

  Future<void> retryPending() async {
    if (!_hasCurrentSession || (!durableReplay && state.unknownDelivery)) {
      return;
    }
    _retryAttempt = 0;
    _queueRetryTimer?.cancel();
    if (!_realtime.isConnected) await connect();
    if (_realtime.isConnected) await _flushOutbox();
  }

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
              delivery: message.delivery,
            ),
        ],
      );
      try {
        await _localStore.write(snapshot);
        if (_hasCurrentSession) {
          emit(
            state.copyWith(
              localSaveFailed: false,
              isSavingDraft: false,
              draftSaved: snapshot.draft.trim().isNotEmpty,
            ),
          );
        }
      } catch (_) {
        if (_hasCurrentSession) {
          emit(
            state.copyWith(
              localSaveFailed: true,
              isSavingDraft: false,
              draftSaved: false,
            ),
          );
        }
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
    emit(
      state.copyWith(
        draft: value,
        needsDraftDecision: false,
        isSavingDraft: true,
        draftSaved: false,
      ),
    );
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
    if (readOnly || !_hasCurrentSession || !_shouldBeConnected) return;
    _unregisterCleanup ??= AccountSession.registerCleanup((_) => close());
    _contactNotificationSubscription ??= ForegroundNotificationBus.stream
        .listen((notification) {
          if (notification.kind == AppNotificationKind.visitAccepted) {
            unawaited(refreshContact(afterVisitAcceptance: true));
          }
        });
    await _loadLocal();
    if (!_hasCurrentSession || !canSend) return;
    if (durableReplay && _outbox.isNotEmpty && _messageSubscription == null) {
      try {
        final (messages, _) = await _dataSource.getMessagesPage(
          conversationId: conversationId,
          page: 1,
        );
        await reconcileHistory(messages);
      } catch (_) {
        /* Replay remains gated by confirmed server deduplication. */
      }
    }
    if (!_hasCurrentSession) return;
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
    if (!_hasCurrentSession || !canSend) return const ChatSendResult.failed();
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
          'Unable to connect the chat socket before sending',
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
    if (readOnly || !_hasCurrentSession) return;
    _unregisterCleanup ??= AccountSession.registerCleanup((_) => close());
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
      log('Unable to mark chat as read', stackTrace: stackTrace);
    }
  }

  Future<void> onAppLifecycleStateChanged(AppLifecycleState lifecycle) async {
    if (readOnly || !_hasCurrentSession) return;
    _shouldBeConnected =
        lifecycle == AppLifecycleState.resumed ||
        lifecycle == AppLifecycleState.inactive;
    if (_realtime.activeConversationId != conversationId) {
      if (lifecycle == AppLifecycleState.resumed &&
          _realtime.activeConversationId == null) {
        await connect();
      }
      return;
    }
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
    final confirmation = _confirmations[message.clientMessageId];
    if (confirmation == null ||
        confirmation.message.content != message.content) {
      return null;
    }
    _confirmations.remove(message.clientMessageId);
    if (!confirmation.completer.isCompleted) {
      confirmation.completer.complete(message);
    }
    if (confirmation.message.delivery == ChatDeliveryState.unknown &&
        _outbox.remove(confirmation.message)) {
      confirmation.message.noticeTimer?.cancel();
      unawaited(
        _persistLocal()
            .then((_) {
              _emitQueuedMessageCount();
              return _flushOutbox();
            })
            .catchError((Object _) {}),
      );
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
    while (_outbox.isNotEmpty &&
        _realtime.isConnected &&
        _hasCurrentSession &&
        canSend) {
      final _QueuedChatMessage queuedMessage = _outbox.first;
      if (queuedMessage.delivery == ChatDeliveryState.unknown &&
          !durableReplay) {
        return;
      }
      final ChatSendResult result = await _deliverQueuedMessage(queuedMessage);
      if (!result.isSent) {
        queuedMessage.result = result;
        _scheduleQueueRetry();
        return;
      }

      queuedMessage.result = result;
      queuedMessage.noticeTimer?.cancel();
      _outbox.remove(queuedMessage);
      _retryAttempt = 0;
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

    bool transmissionStarted = false;
    try {
      queuedMessage.delivery = ChatDeliveryState.sending;
      await _persistLocal();
      transmissionStarted = true;
      await _realtime.sendMessage(
        conversationId: conversationId,
        content: queuedMessage.content,
        clientMessageId: queuedMessage.clientMessageId,
      );
      queuedMessage.delivery = ChatDeliveryState.awaitingConfirmation;
      await _persistLocal();
      final ChatSocketMessage confirmedMessage = await completer.future.timeout(
        _confirmationTimeout,
      );
      return ChatSendResult.sent(restMessage: confirmedMessage);
    } catch (socketError, socketStackTrace) {
      if (!transmissionStarted) {
        _removeConfirmation(confirmation);
        _outbox.remove(queuedMessage);
        _emitQueuedMessageCount();
        return const ChatSendResult.failed();
      }
      if (!durableReplay && _hasCurrentSession) {
        // Keep the confirmation registered for a late ACK. No blind second send.
        queuedMessage.delivery = ChatDeliveryState.unknown;
        queuedMessage.showQueuedNotice = true;
        try {
          await _persistLocal();
        } catch (_) {
          /* Keep the unknown state and the storage failure visible. */
        }
        _emitQueuedMessageCount();
        return const ChatSendResult.unknown();
      }
      _removeConfirmation(confirmation);
      if (!_hasCurrentSession || !canSend || !_realtime.isConnected) {
        log(
          'Chat message remains queued until the socket reconnects',
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
      log('Unable to send queued chat message', stackTrace: stackTrace);
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
        unknownDelivery: _outbox.any(
          (message) => message.delivery == ChatDeliveryState.unknown,
        ),
      ),
    );
  }

  void _scheduleQueueRetry() {
    if (!_shouldBeConnected ||
        _outbox.isEmpty ||
        !_hasCurrentSession ||
        !canSend ||
        state.localSaveFailed) {
      return;
    }
    if (!durableReplay && _outbox.first.delivery == ChatDeliveryState.unknown) {
      return;
    }
    if (_retryAttempt >= 4) return;
    _queueRetryTimer?.cancel();
    final delay = Duration(
      seconds: _queueRetryDelay.inSeconds * (1 << _retryAttempt++),
    );
    _queueRetryTimer = Timer(delay, () async {
      if (!_shouldBeConnected ||
          _outbox.isEmpty ||
          !_hasCurrentSession ||
          !canSend) {
        return;
      }
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
    if (isClosed || _closing) return;
    _unregisterCleanup?.call();
    _unregisterCleanup = null;
    _closing = true;
    _shouldBeConnected = false;
    _queueRetryTimer?.cancel();
    _draftTimer?.cancel();
    for (final message in _outbox) {
      message.noticeTimer?.cancel();
    }
    // Start storage and connection cleanup together. Disk IO must not retain a socket.
    final cleanup = <Future<void>>[];
    if (_contactNotificationSubscription != null) {
      cleanup.add(_contactNotificationSubscription!.cancel());
    }
    if (flushDraft && _sessionGeneration == AccountSession.generation) {
      cleanup.add(_persistLocal().catchError((Object _) {}));
    }
    if (!readOnly && _realtime.activeConversationId == conversationId) {
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
  ChatDeliveryState delivery = ChatDeliveryState.queued;
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
