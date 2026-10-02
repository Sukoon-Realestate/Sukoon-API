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
    this.confirmedLocalMessageId,
  });

  const ChatThreadState.initial()
    : status = ChatSocketStatus.disconnected,
      receivedMessageRevision = 0,
      readReceiptRevision = 0,
      queuedMessageCount = 0,
      showQueuedMessages = false,
      confirmedLocalMessageId = null,
      receivedMessage = null;

  final ChatSocketStatus status;
  final ChatSocketMessage? receivedMessage;
  final String? confirmedLocalMessageId;
  final int receivedMessageRevision;
  final int readReceiptRevision;
  final int queuedMessageCount;
  final bool showQueuedMessages;

  ChatThreadState copyWith({
    ChatSocketStatus? status,
    ChatSocketMessage? receivedMessage,
    Object? confirmedLocalMessageId = _notProvided,
    int? receivedMessageRevision,
    int? readReceiptRevision,
    int? queuedMessageCount,
    bool? showQueuedMessages,
  }) {
    return ChatThreadState(
      status: status ?? this.status,
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
    receivedMessage,
    confirmedLocalMessageId,
    receivedMessageRevision,
    readReceiptRevision,
    queuedMessageCount,
    showQueuedMessages,
  ];
}

const Object _notProvided = Object();
