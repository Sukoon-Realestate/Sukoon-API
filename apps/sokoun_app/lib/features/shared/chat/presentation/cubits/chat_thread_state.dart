part of 'socket_cubit.dart';

enum ChatSocketStatus { disconnected, connecting, connected, error }

extension ChatSocketStatusX on ChatSocketStatus {
  bool get isConnecting => this == ChatSocketStatus.connecting;
}

class ChatThreadState extends Equatable {
  const ChatThreadState({
    required this.status,
    required this.receivedMessageRevision,
    required this.readReceiptRevision,
    this.receivedMessage,
  });

  const ChatThreadState.initial()
    : status = ChatSocketStatus.disconnected,
      receivedMessageRevision = 0,
      readReceiptRevision = 0,
      receivedMessage = null;

  final ChatSocketStatus status;
  final ChatSocketMessage? receivedMessage;
  final int receivedMessageRevision;
  final int readReceiptRevision;

  ChatThreadState copyWith({
    ChatSocketStatus? status,
    ChatSocketMessage? receivedMessage,
    int? receivedMessageRevision,
    int? readReceiptRevision,
  }) {
    return ChatThreadState(
      status: status ?? this.status,
      receivedMessage: receivedMessage ?? this.receivedMessage,
      receivedMessageRevision:
          receivedMessageRevision ?? this.receivedMessageRevision,
      readReceiptRevision: readReceiptRevision ?? this.readReceiptRevision,
    );
  }

  @override
  List<Object?> get props => [
    status,
    receivedMessage,
    receivedMessageRevision,
    readReceiptRevision,
  ];
}
