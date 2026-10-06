import 'package:equatable/equatable.dart';

import 'chat_participant_content.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';

class ChatSocketMessage extends Equatable {
  const ChatSocketMessage({
    required this.id,
    required this.conversationId,
    required this.sender,
    required this.content,
    required this.createdAt,
  });

  const ChatSocketMessage.initial()
    : id = '',
      conversationId = '',
      sender = const ChatParticipantContent.initial(),
      content = '',
      createdAt = null;

  factory ChatSocketMessage.fromJson(Map<String, dynamic> json) {
    final dynamic senderJson = json['sender'];
    return ChatSocketMessage(
      id: json['id']?.toString() ?? '',
      conversationId:
          json['conversation_id']?.toString() ??
          json['conversation']?.toString() ??
          '',
      sender: ChatParticipantContent.fromJson(
        senderJson is Map
            ? Map<String, dynamic>.from(senderJson)
            : const <String, dynamic>{},
      ),
      content: json['content']?.toString() ?? '',
      createdAt: DateTime.tryParse(json['created_at']?.toString() ?? ''),
    );
  }

  final String id;
  final String conversationId;
  final ChatParticipantContent sender;
  final String content;
  final DateTime? createdAt;

  bool get isFromMe {
    final String currentUserId = UserModel.currentUser?.id ?? '';
    return currentUserId.isNotEmpty && sender.id == currentUserId;
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'conversation_id': conversationId,
    'sender': sender.toJson(),
    'content': content,
    'created_at': createdAt?.toIso8601String(),
  };

  ChatSocketMessage copyWith({
    String? id,
    String? conversationId,
    ChatParticipantContent? sender,
    String? content,
    DateTime? createdAt,
  }) {
    return ChatSocketMessage(
      id: id ?? this.id,
      conversationId: conversationId ?? this.conversationId,
      sender: sender ?? this.sender,
      content: content ?? this.content,
      createdAt: createdAt ?? this.createdAt,
    );
  }

  @override
  List<Object?> get props => [id, conversationId, sender, content, createdAt];
}
