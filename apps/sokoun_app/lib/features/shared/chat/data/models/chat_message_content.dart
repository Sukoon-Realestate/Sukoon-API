import 'package:equatable/equatable.dart';

import 'chat_participant_content.dart';

class ChatMessageContent extends Equatable {
  const ChatMessageContent({
    required this.id,
    required this.body,
    required this.time,
    required this.isFromMe,
    this.type = 'text',
    this.conversationId = '',
    this.sender = const ChatParticipantContent.initial(),
    this.createdAt,
    this.clientMessageId = '',
  });

  const ChatMessageContent.initial()
    : id = '',
      body = '',
      time = '',
      isFromMe = false,
      type = 'text',
      conversationId = '',
      sender = const ChatParticipantContent.initial(),
      clientMessageId = '',
      createdAt = null;

  factory ChatMessageContent.fromJson(Map<String, dynamic> json) {
    final Object? senderJson = json['sender'];
    return ChatMessageContent(
      id: json['id']?.toString() ?? '',
      body: json['content']?.toString() ?? json['body']?.toString() ?? '',
      clientMessageId: json['client_message_id']?.toString() ?? '',
      time: json['time']?.toString() ?? '',
      isFromMe: json['is_from_me'] ?? false,
      type: json['type']?.toString() ?? 'text',
      conversationId:
          json['conversation_id']?.toString() ??
          json['conversation']?.toString() ??
          '',
      sender: ChatParticipantContent.fromJson(
        senderJson is Map
            ? Map<String, dynamic>.from(senderJson)
            : const <String, dynamic>{},
      ),
      createdAt: DateTime.tryParse(json['created_at']?.toString() ?? ''),
    );
  }

  final String id;
  final String body;
  final String clientMessageId;
  final String time;
  final bool isFromMe;
  final String type;
  final String conversationId;
  final ChatParticipantContent sender;
  final DateTime? createdAt;

  Map<String, dynamic> toJson() => {
    'id': id,
    'conversation': conversationId,
    'sender': sender.toJson(),
    'content': body,
    'client_message_id': clientMessageId,
    'created_at': createdAt?.toIso8601String(),
    'time': time,
    'is_from_me': isFromMe,
    'type': type,
  };

  ChatMessageContent copyWith({
    String? id,
    String? body,
    String? clientMessageId,
    String? time,
    bool? isFromMe,
    String? type,
    String? conversationId,
    ChatParticipantContent? sender,
    DateTime? createdAt,
  }) {
    return ChatMessageContent(
      id: id ?? this.id,
      body: body ?? this.body,
      clientMessageId: clientMessageId ?? this.clientMessageId,
      time: time ?? this.time,
      isFromMe: isFromMe ?? this.isFromMe,
      type: type ?? this.type,
      conversationId: conversationId ?? this.conversationId,
      sender: sender ?? this.sender,
      createdAt: createdAt ?? this.createdAt,
    );
  }

  @override
  List<Object?> get props => [
    id,
    body,
    clientMessageId,
    time,
    isFromMe,
    type,
    conversationId,
    sender,
    createdAt,
  ];
}
