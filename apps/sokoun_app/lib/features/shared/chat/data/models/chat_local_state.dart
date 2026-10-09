import 'package:equatable/equatable.dart';

enum ChatDeliveryState {
  queued,
  sending,
  awaitingConfirmation,
  sent,
  failed,
  unknown,
}

class SavedChatMessage extends Equatable {
  const SavedChatMessage({
    required this.id,
    required this.content,
    this.clientMessageId = '',
    this.delivery = ChatDeliveryState.queued,
  });
  const SavedChatMessage.initial()
    : id = '',
      content = '',
      clientMessageId = '',
      delivery = ChatDeliveryState.queued;
  factory SavedChatMessage.fromJson(Map<String, dynamic> json) =>
      SavedChatMessage(
        id: json['id'] as String? ?? '',
        content: json['content'] as String? ?? '',
        clientMessageId: json['client_message_id'] as String? ?? '',
        delivery: _restoredDelivery(json['delivery']),
      );
  final String id;
  final String content;
  final String clientMessageId;
  final ChatDeliveryState delivery;
  static ChatDeliveryState _restoredDelivery(Object? value) {
    final state = ChatDeliveryState.values.firstWhere(
      (entry) => entry.name == value,
      orElse: () => ChatDeliveryState.unknown,
    );
    return state == ChatDeliveryState.sending ||
            state == ChatDeliveryState.awaitingConfirmation
        ? ChatDeliveryState.unknown
        : state;
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'content': content,
    'client_message_id': clientMessageId,
    'delivery': delivery.name,
  };
  SavedChatMessage copyWith({
    String? id,
    String? content,
    String? clientMessageId,
    ChatDeliveryState? delivery,
  }) => SavedChatMessage(
    id: id ?? this.id,
    content: content ?? this.content,
    clientMessageId: clientMessageId ?? this.clientMessageId,
    delivery: delivery ?? this.delivery,
  );
  @override
  List<Object?> get props => [id, content, clientMessageId, delivery];
}

class ChatLocalState extends Equatable {
  const ChatLocalState({
    this.draft = '',
    this.draftClientMessageId = '',
    this.messages = const [],
  });
  const ChatLocalState.initial()
    : draft = '',
      draftClientMessageId = '',
      messages = const [];
  factory ChatLocalState.fromJson(Map<String, dynamic> json) => ChatLocalState(
    draft: json['draft'] as String? ?? '',
    draftClientMessageId: json['draft_client_message_id'] as String? ?? '',
    messages: (json['messages'] as List? ?? const [])
        .whereType<Map>()
        .map(
          (value) =>
              SavedChatMessage.fromJson(Map<String, dynamic>.from(value)),
        )
        .where((message) => message.id.isNotEmpty && message.content.isNotEmpty)
        .toList(growable: false),
  );
  final String draft;
  final String draftClientMessageId;
  final List<SavedChatMessage> messages;
  Map<String, dynamic> toJson() => {
    'draft': draft,
    'draft_client_message_id': draftClientMessageId,
    'messages': messages.map((message) => message.toJson()).toList(),
  };
  ChatLocalState copyWith({
    String? draft,
    String? draftClientMessageId,
    List<SavedChatMessage>? messages,
  }) => ChatLocalState(
    draft: draft ?? this.draft,
    draftClientMessageId: draftClientMessageId ?? this.draftClientMessageId,
    messages: messages ?? this.messages,
  );
  @override
  List<Object?> get props => [draft, draftClientMessageId, messages];
}
