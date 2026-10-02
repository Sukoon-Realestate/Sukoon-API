import 'package:equatable/equatable.dart';

import 'chat_participant_content.dart';

class ConversationContent extends Equatable {
  const ConversationContent({
    required this.id,
    required this.name,
    required this.property,
    required this.lastMessage,
    required this.time,
    required this.unreadCount,
    required this.isVerified,
    required this.isOnline,
    this.otherParticipant = const ChatParticipantContent.initial(),
    this.lastMessageAt,
    this.updatedAt,
  });

  const ConversationContent.initial()
    : id = '',
      name = '',
      property = '',
      lastMessage = '',
      time = '',
      unreadCount = 0,
      isVerified = false,
      isOnline = false,
      otherParticipant = const ChatParticipantContent.initial(),
      lastMessageAt = null,
      updatedAt = null;

  factory ConversationContent.fromJson(Map<String, dynamic> json) {
    final Object? participantJson = json['other_participant'];
    final ChatParticipantContent participant = ChatParticipantContent.fromJson(
      participantJson is Map
          ? Map<String, dynamic>.from(participantJson)
          : const <String, dynamic>{},
    );

    return ConversationContent(
      id: json['id']?.toString() ?? '',
      name: participant.fullName.isNotEmpty
          ? participant.fullName
          : json['name']?.toString() ?? '',
      property: json['property']?.toString() ?? '',
      lastMessage:
          json['last_message_preview']?.toString() ??
          json['last_message']?.toString() ??
          '',
      time: json['time']?.toString() ?? '',
      unreadCount: (json['unread_count'] as num?)?.toInt() ?? 0,
      isVerified:
          json['is_verified'] as bool? ??
          (participantJson is Map && participant.isVerified),
      isOnline: json['is_online'] as bool? ?? participant.isOnline,
      otherParticipant: participant,
      lastMessageAt: DateTime.tryParse(
        json['last_message_at']?.toString() ?? '',
      ),
      updatedAt: DateTime.tryParse(json['updated_at']?.toString() ?? ''),
    );
  }

  final String id;
  final String name;
  final String property;
  final String lastMessage;
  final String time;
  final int unreadCount;
  final bool isVerified;
  final bool isOnline;
  final ChatParticipantContent otherParticipant;
  final DateTime? lastMessageAt;
  final DateTime? updatedAt;

  bool matchesQuery(String query) {
    final String normalizedQuery = query.trim().toLowerCase();
    if (normalizedQuery.isEmpty) return true;

    return name.toLowerCase().contains(normalizedQuery) ||
        property.toLowerCase().contains(normalizedQuery) ||
        lastMessage.toLowerCase().contains(normalizedQuery);
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'other_participant': otherParticipant.toJson(),
    'name': name,
    if (property.isNotEmpty) 'property': property,
    'last_message_preview': lastMessage,
    'time': time,
    'unread_count': unreadCount,
    'is_verified': isVerified,
    'is_online': isOnline,
    'last_message_at': lastMessageAt?.toIso8601String(),
    'updated_at': updatedAt?.toIso8601String(),
  };

  ConversationContent copyWith({
    String? id,
    String? name,
    String? property,
    String? lastMessage,
    String? time,
    int? unreadCount,
    bool? isVerified,
    bool? isOnline,
    ChatParticipantContent? otherParticipant,
    DateTime? lastMessageAt,
    DateTime? updatedAt,
  }) {
    return ConversationContent(
      id: id ?? this.id,
      name: name ?? this.name,
      property: property ?? this.property,
      lastMessage: lastMessage ?? this.lastMessage,
      time: time ?? this.time,
      unreadCount: unreadCount ?? this.unreadCount,
      isVerified: isVerified ?? this.isVerified,
      isOnline: isOnline ?? this.isOnline,
      otherParticipant: otherParticipant ?? this.otherParticipant,
      lastMessageAt: lastMessageAt ?? this.lastMessageAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  @override
  List<Object?> get props => [
    id,
    name,
    property,
    lastMessage,
    time,
    unreadCount,
    isVerified,
    isOnline,
    otherParticipant,
    lastMessageAt,
    updatedAt,
  ];
}
