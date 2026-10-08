part of 'chat_thread_cubit.dart';

enum ChatSocketStatus { disconnected, connecting, connected, error }

extension ChatSocketStatusX on ChatSocketStatus {
  bool get isConnecting => this == ChatSocketStatus.connecting;
}

class ChatThreadState extends Equatable {
  const ChatThreadState({
    required this.status,
    required this.receivedMessageRevision,
    required this.readReceiptRevision,
    required this.queuedMessageCount,
    this.showQueuedMessages = false,
    this.receivedMessage,
    this.draft = '',
    this.localSaveFailed = false,
    this.recoveredMessages = const [],
    this.confirmedLocalMessageId,
    this.contact = const ChatParticipantContent.initial(),
    this.canSend = true,
  });

  const ChatThreadState.initial()
    : status = ChatSocketStatus.disconnected,
      receivedMessageRevision = 0,
      readReceiptRevision = 0,
      queuedMessageCount = 0,
      showQueuedMessages = false,
      confirmedLocalMessageId = null,
      receivedMessage = null,
      contact = const ChatParticipantContent.initial(),
      canSend = true,
      draft = '',
      localSaveFailed = false,
      recoveredMessages = const [];

  final ChatSocketStatus status;
  final ChatParticipantContent contact;
  final bool canSend;
  final String draft;
  final bool localSaveFailed;
  final List<SavedChatMessage> recoveredMessages;
  final ChatSocketMessage? receivedMessage;
  final String? confirmedLocalMessageId;
  final int receivedMessageRevision;
  final int readReceiptRevision;
  final int queuedMessageCount;
  final bool showQueuedMessages;

  ChatThreadState copyWith({
    ChatSocketStatus? status,
    String? draft,
    bool? localSaveFailed,
    List<SavedChatMessage>? recoveredMessages,
    ChatSocketMessage? receivedMessage,
    Object? confirmedLocalMessageId = _notProvided,
    int? receivedMessageRevision,
    int? readReceiptRevision,
    int? queuedMessageCount,
    bool? showQueuedMessages,
    ChatParticipantContent? contact,
    bool? canSend,
  }) {
    return ChatThreadState(
      status: status ?? this.status,
      contact: contact ?? this.contact,
      canSend: canSend ?? this.canSend,
      draft: draft ?? this.draft,
      localSaveFailed: localSaveFailed ?? this.localSaveFailed,
      recoveredMessages: recoveredMessages ?? this.recoveredMessages,
      receivedMessage: receivedMessage ?? this.receivedMessage,
      confirmedLocalMessageId: identical(confirmedLocalMessageId, _notProvided)
          ? this.confirmedLocalMessageId
          : confirmedLocalMessageId as String?,
      receivedMessageRevision:
          receivedMessageRevision ?? this.receivedMessageRevision,
      readReceiptRevision: readReceiptRevision ?? this.readReceiptRevision,
      queuedMessageCount: queuedMessageCount ?? this.queuedMessageCount,
      showQueuedMessages: showQueuedMessages ?? this.showQueuedMessages,
    );
  }

  @override
  List<Object?> get props => [
    status,
    contact,
    canSend,
    draft,
    localSaveFailed,
    recoveredMessages,
    receivedMessage,
    confirmedLocalMessageId,
    receivedMessageRevision,
    readReceiptRevision,
    queuedMessageCount,
    showQueuedMessages,
  ];
}

const Object _notProvided = Object();
