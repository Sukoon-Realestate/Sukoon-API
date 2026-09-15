import 'package:equatable/equatable.dart';

class ChatSocketMessage extends Equatable {
  const ChatSocketMessage({
    required this.id,
    required this.conversationId,
    required this.sender,
    required this.content,
    required this.createdAt,
  });

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
