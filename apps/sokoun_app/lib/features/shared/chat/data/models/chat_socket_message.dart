import 'package:equatable/equatable.dart';
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
      sender = const ChatSocketSender.initial(),
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
      sender: ChatSocketSender.fromJson(
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
  final ChatSocketSender sender;
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
    ChatSocketSender? sender,
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

class ChatSocketSender extends Equatable {
  const ChatSocketSender({
    required this.id,
    required this.name,
    required this.avatarUrl,
    required this.isOnline,
    this.firstName = '',
    this.lastName = '',
    this.email = '',
  });

  const ChatSocketSender.initial()
    : id = '',
      name = '',
      avatarUrl = '',
      isOnline = false,
      firstName = '',
      lastName = '',
      email = '';

  factory ChatSocketSender.fromJson(Map<String, dynamic> json) {
    final String firstName = json['first_name']?.toString() ?? '';
    final String lastName = json['last_name']?.toString() ?? '';
    final String fallbackName = [
      firstName,
      lastName,
    ].where((part) => part.isNotEmpty).join(' ');

    return ChatSocketSender(
      id: json['id']?.toString() ?? '',
      name: json['full_name']?.toString() ?? fallbackName,
      avatarUrl: json['avatar_url']?.toString() ?? '',
      isOnline: json['is_online'] == true,
      firstName: firstName,
      lastName: lastName,
      email: json['email']?.toString() ?? '',
    );
  }

  final String id;
  final String name;
  final String avatarUrl;
  final bool isOnline;
  final String firstName;
  final String lastName;
  final String email;

  Map<String, dynamic> toJson() => {
    'id': id,
    'full_name': name,
    'avatar_url': avatarUrl,
    'is_online': isOnline,
    'first_name': firstName,
    'last_name': lastName,
    'email': email,
  };

  ChatSocketSender copyWith({
    String? id,
    String? name,
    String? avatarUrl,
    bool? isOnline,
    String? firstName,
    String? lastName,
    String? email,
  }) {
    return ChatSocketSender(
      id: id ?? this.id,
      name: name ?? this.name,
      avatarUrl: avatarUrl ?? this.avatarUrl,
      isOnline: isOnline ?? this.isOnline,
      firstName: firstName ?? this.firstName,
      lastName: lastName ?? this.lastName,
      email: email ?? this.email,
    );
  }

  @override
  List<Object?> get props => [
    id,
    name,
    avatarUrl,
    isOnline,
    firstName,
    lastName,
    email,
  ];
}
